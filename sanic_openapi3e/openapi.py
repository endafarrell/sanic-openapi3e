"""
Build the OpenAPI spec.

Note: ```app.config.HIDE_OPENAPI_SELF``` is used to hide the ``/openapi`` and ``/swagger`` endpoints from the spec. The
      default value is `True`. To reveal these endpoints in the spec, set it explicitly to `False`.

Known limitations:
* Parameters are documented at the PathItem level, not at the underlying Operation level.

"""
import re
from collections import OrderedDict
from itertools import repeat
from typing import Any, Callable, List, Optional, Set, Tuple

import sanic
import sanic.exceptions
import sanic.response
import sanic.router
from sanic.blueprints import Blueprint
from sanic.views import CompositionView

from .doc import (
    Components,
    Contact,
    ExternalDocumentation,
    Info,
    License,
    OpenAPIv3,
    Operation,
    Parameter,
    PathItem,
    Paths,
    Reference,
    Response,
    Responses,
    Schema,
    SecurityRequirement,
    Server,
    Tag,
    endpoints,
)
from .doc import tags as doc_tags  # these originate in oas_types
from .swagger import blueprint as swagger_bp

blueprint = Blueprint("openapi", url_prefix="openapi")

NOT_YET_IMPLEMENTED = None
NotYetImplementedResponses = Responses({"200": Response(description="A successful response")})

# Note: python3.6 cannot use OrderedDict as a type hint (that was fixed in 3.7+...)
_OPENAPI = OrderedDict()  # type: OrderedDict[str, Any]
"""
Module-level container to hold the OAS spec that will be served-up on request. See `build_openapi_spec` for how it is
built.
"""

_OPENAPI_ALL = OrderedDict()  # type: OrderedDict[str, Any]
"""
Module-level container to hold the OAS spec that may be served-up on request. The difference with this one is that it 
contains all endpoints, including those marked as `exclude`.
"""


def simple_snake2camel(string: str) -> str:
    first, *rest = string.strip().lower().split("_")
    return first + "".join(ele.capitalize() for ele in rest)


CAST_2_SCHEMA = {int: Schema.Integer, float: Schema.Number, str: Schema.String}


def default_operation_id_fn(method: str, uri: str, route: sanic.router.Route) -> str:
    uri_for_operation_id: str = uri
    for parameter in route.parameters:
        uri_for_operation_id = re.sub("<" + parameter.name + ".*?>", parameter.name, uri_for_operation_id)

    return "{}~~{}".format(method.upper(), uri_for_operation_id).replace("/", "~")


def camel_case_operation_id_fn(method: str, uri: str, route: sanic.router.Route) -> str:
    if hasattr(route.handler, "__class__") and hasattr(route.handler, "handlers"):
        # These are `sanic.view.CompositeView`s
        _method_handler = route.handler.handlers.get(method.upper())
        if _method_handler:
            handler_name = method + "_" + _method_handler.__name__
        else:
            raise ValueError(f"No {method.upper()} handler found for {uri} handlers: {route.handler.handlers}")
    elif hasattr(route.handler, "__name__"):
        if len(route.methods) > 1:
            # This fn will be called many times, once per method, but we should prefix the handler_name with this
            # prefix to make the operationIds globally unique. If the route is only used by one method, use that
            # handler's name.
            handler_name = method + "_" + route.handler.__name__
        else:
            handler_name = route.handler.__name__
    else:
        raise NotImplementedError()
    return simple_snake2camel(handler_name)


@blueprint.listener("before_server_start")
def build_openapi_spec(app: sanic.app.Sanic, _):
    hide_openapi_self = app.config.get("HIDE_OPENAPI_SELF", True)
    hide_sanic_static = app.config.get("HIDE_SANIC_STATIC", True)
    show_excluded = app.config.get("SHOW_OPENAPI_EXCLUDED", False)
    show_unused_tags = app.config.get("SHOW_OPENAPI_UNUSED_TAGS", False)
    operation_id_fn = app.config.get("OPENAPI_OPERATION_ID_FN", default_operation_id_fn)

    assert callable(operation_id_fn), operation_id_fn
    openapi = _build_openapi_spec(
        app,
        operation_id_fn,
        hide_openapi_self=hide_openapi_self,
        hide_excluded=True,
        show_unused_tags=show_unused_tags,
        hide_sanic_static=hide_sanic_static,
    )
    global _OPENAPI  # pylint: disable=global-statement
    _OPENAPI = openapi.serialize()

    if show_excluded:
        openapi_all = _build_openapi_spec(
            app,
            operation_id_fn,
            hide_openapi_self=hide_openapi_self,
            hide_excluded=False,
            show_unused_tags=True,
            hide_sanic_static=False,
        )
        global _OPENAPI_ALL  # pylint: disable=global-statement
        _OPENAPI_ALL = openapi_all.serialize()


def _build_openapi_spec(  # pylint: disable=too-many-arguments,too-many-locals,too-many-statements,(too-many-branches
    app: sanic.app.Sanic,
    operation_id_fn: Callable[[str, str, sanic.router.Route], str],
    hide_openapi_self=True,
    hide_excluded=True,
    show_unused_tags=False,
    hide_sanic_static=True,
) -> OpenAPIv3:
    """
    Build the OpenAPI spec.

    :param app:
    :param operation_id_fn
    :param hide_openapi_self:
    :param hide_excluded:
    :return: The spec
    """

    # We may reuse this later
    assert callable(operation_id_fn), operation_id_fn
    components = app.config.get("OPENAPI_COMPONENTS", None)
    if components:
        if not isinstance(components, Components):
            raise AssertionError(
                "You app.config's `OPENAPI_COMPONENTS` is not a `Components`: {}".format(type(components))
            )

    _oas_paths: List[Tuple[str, PathItem]] = []
    for _uri, _route in app.router.routes_all.items():  # pylint: disable=too-many-nested-blocks
        assert isinstance(_uri, str)
        assert isinstance(_route, sanic.router.Route), type(_route)
        # NOTE: TODO: there's no order here at all to either the _uri nor the _route. OAS specs do not define an order
        # NOTE: TODO: but people do rather like having at least document order for the routes.
        if hide_openapi_self:
            if (_uri.startswith("/" + blueprint.url_prefix) if blueprint.url_prefix else True) and any(
                [bp_uri in _uri for bp_uri in [r.uri for r in blueprint.routes]]
            ):
                # Remove self-documentation from the spec
                continue
            if (_uri.startswith("/" + swagger_bp.url_prefix) if swagger_bp.url_prefix else True) and any(
                [bp_uri in _uri for bp_uri in [r.uri for r in swagger_bp.routes]] + [not bool(swagger_bp.routes)]
            ):
                # Remove self-documentation from the spec by not adding.
                continue

        if "<file_uri" in _uri and hide_excluded:
            continue

        # We document the parameters at the PathItem, not at the Operation. First get the route parameters (if any)
        uri_parsed: str = _uri
        uri_for_opearion_id = _uri
        parameters: List[Tuple[str, Parameter]] = []
        for _parameter in _route.parameters:
            uri_parsed = re.sub("<" + _parameter.name + ".*?>", "{" + _parameter.name + "}", uri_parsed)
            uri_for_opearion_id = re.sub("<" + _parameter.name + ".*?>", _parameter.name, uri_for_opearion_id)

            # Sanic route parameters can give us a name, we know that it is in the path and we may be able to establish
            # the basic schema.
            parameter = Parameter(
                name=_parameter.name,
                _in="path",
                description=None,
                required=True,
                deprecated=None,
                allow_empty_value=None,
                style=None,
                explode=None,
                allow_reserved=None,
                schema=CAST_2_SCHEMA.get(_parameter.cast),
                example=None,
                examples=None,
                content=None,
            )
            parameters.append((parameter.name, parameter))

        handler_type = type(_route.handler)
        if handler_type is CompositionView:
            view = _route.handler
            pathitem_operations = view.handlers.items()
        else:
            pathitem_operations = zip(_route.methods, repeat(_route.handler))

        operations = OrderedDict()
        for _method, _func in pathitem_operations:
            path_item: PathItem = endpoints[_func]
            assert isinstance(path_item, PathItem)
            if path_item.x_exclude and hide_excluded:
                continue
            if str(_func.__module__) == "sanic.static" and hide_sanic_static:
                continue

            path_item_summary: Optional[str] = path_item.summary
            if path_item.x_exclude and not hide_excluded:
                path_item_summary = "[excluded] " + (path_item.summary if path_item.summary else "")

            _parameters = path_item.parameters
            for _parameter in _parameters:
                if isinstance(_parameter.schema, Reference):
                    # Swagger v3.21.0 doesn't show the description for references, so ...
                    if not _parameter.description:
                        if components:
                            if components.schemas:
                                if components.schemas.get(_parameter.name):
                                    ref = components.schemas.get(_parameter.name)
                                    _parameter.description = ref.description

                if _parameter.name in [p[0] for p in parameters]:
                    # Find and merge them. Parameter has a special __add__ for this.
                    for idx, _ in enumerate(parameters):
                        try:
                            if parameters[idx][0] == _parameter.name:
                                parameters[idx] = (
                                    _parameter.name,
                                    parameters[idx][1] + _parameter,
                                )
                        except AssertionError as ex:
                            raise AssertionError(
                                "For `{} {}` ({}) the `{}` param is invalid: {}".format(
                                    _method, _uri, str(_func), _parameter.name, ex
                                )
                            ) from ex
                else:
                    parameters.append((_parameter.name, _parameter))

            pathitem_tag_names: Set[str] = {t.name for t in path_item.x_tags_holder}

            # If the route does not have a tag, use the blueprint's name.
            for _blueprint in app.blueprints.values():
                if not hasattr(_blueprint, "routes"):
                    continue

                for _bproute in _blueprint.routes:
                    if _bproute.handler != _func:
                        continue
                    if not pathitem_tag_names:
                        pathitem_tag_names.add(_blueprint.name)

            operation_id = operation_id_fn(_method, _uri, _route)
            operations[_method.lower()] = Operation(
                operation_id=operation_id,
                responses=path_item.x_responses_holder,
                summary=path_item_summary,
                description=path_item.description,
                parameters=[p[1] for p in parameters],
                tags=sorted(pathitem_tag_names),
                deprecated=path_item.x_deprecated_holder,
                request_body=path_item.request_body,
                # TODO
                servers=NOT_YET_IMPLEMENTED,
                security=NOT_YET_IMPLEMENTED,
                callbacks=NOT_YET_IMPLEMENTED,
            )

            _path = PathItem(**operations)
            _oas_paths.append((uri_parsed, _path))

    # Possible contact
    contact: Optional[Contact] = None
    _contact_name = app.config.get("API_CONTACT_NAME")
    _contact_url = app.config.get("API_CONTACT_URL")
    _contact_email = app.config.get("API_CONTACT_EMAIL")
    if any((_contact_email, _contact_name, _contact_url)):
        contact = Contact(name=_contact_name, email=_contact_email, url=_contact_url)

    # Possible license
    _license: Optional[License] = None
    _license_name = app.config.get("API_LICENSE_NAME")
    _license_url = app.config.get("API_LICENSE_URL")
    if any((_license_name, _license_url)):
        _license = License(name=_license_name, url=_license_url)

    info = Info(
        title=app.config.get("API_TITLE", "API"),
        description=app.config.get("API_DESCRIPTION", "Description"),
        terms_of_service=app.config.get("API_TERMS_OF_SERVICE_URL"),
        contact=contact,
        _license=_license,
        version=app.config.get("API_VERSION", "1.0.0"),
    )

    _v3_paths = Paths(_oas_paths)
    _v3_tags: List[Tag] = sorted(doc_tags.values())

    if not show_unused_tags:  # pylint: disable=too-many-nested-blocks
        # Check that the tags are in use. This can depend on `hide_excluded`, so we re-use the _v3_paths.
        in_use_tags: Set[Tag] = set()
        for tag in _v3_tags:
            for _path, path_item in _v3_paths:
                for op_name in Operation.OPERATION_NAMES:
                    operation: Operation = getattr(path_item, op_name)
                    if operation:
                        op_tag_names = operation.tags
                        if op_tag_names:
                            for op_tag_name in op_tag_names:
                                if tag.name == op_tag_name:
                                    if not any([t.name == op_tag_name for t in in_use_tags]):
                                        in_use_tags.add(tag)
        _v3_tags = sorted(in_use_tags)

    servers = app.config.get("OPENAPI_SERVERS", None)
    if servers:
        if not isinstance(servers, list):
            raise AssertionError(
                "Your app.config's `OPENAPI_SERVERS` is not a list (of `Server`): {}".format(type(servers))
            )
        for server in servers:
            if not isinstance(server, Server):
                raise AssertionError(
                    "You app.config's `OPENAPI_SERVERS` server `{}` is not a `Server`: {}".format(server, type(server))
                )

    security = app.config.get("OPENAPI_SECURITY", None)
    if security:
        if not isinstance(security, list):
            raise AssertionError(
                "You app.config's `OPENAPI_SECURITY` is not a list (of `SecurityRequirement`): {}".format(
                    type(security)
                )
            )
        for security_element in security:
            if not isinstance(security_element, SecurityRequirement):
                raise AssertionError(
                    "You app.config's `OPENAPI_SECURITY` security `{}` is not a `SecurityRequirement`: {}".format(
                        security_element, type(security_element)
                    )
                )

    external_docs = app.config.get("OPENAPI_EXTERNAL_DOCS", None)
    if external_docs:
        if not isinstance(external_docs, ExternalDocumentation):
            raise AssertionError(
                "You app.config's `OPENAPI_EXTERNAL_DOCS` is not a `ExternalDocumentation`: {}".format(
                    type(external_docs)
                )
            )

    openapi = OpenAPIv3(
        openapi=OpenAPIv3.version,
        info=info,
        paths=_v3_paths,
        servers=servers,
        components=components,
        security=security,
        tags=_v3_tags,
        external_docs=external_docs,
    )
    return openapi


@blueprint.route("/spec.json")
def spec_v3(_):
    return sanic.response.json(_OPENAPI)


@blueprint.route("/spec.all.json")
def spec_all(_):
    if _OPENAPI_ALL:
        return sanic.response.json(_OPENAPI_ALL)
    raise sanic.exceptions.NotFound("Not found")
