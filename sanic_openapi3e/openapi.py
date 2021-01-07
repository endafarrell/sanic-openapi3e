"""
Build the OpenAPI spec.

Note: ```app.config.HIDE_OPENAPI_SELF``` is used to hide the ``/openapi`` and ``/swagger`` endpoints from the spec. The
      default value is `True`. To reveal these endpoints in the spec, set it explicitly to `False`.

Known limitations:
* Parameters are documented at the PathItem level, not at the underlying Operation level.

"""
import re
from itertools import repeat
from collections import OrderedDict
from typing import Any, List, Tuple

import sanic
import sanic.response
import sanic.exceptions
from sanic.blueprints import Blueprint
from sanic.views import CompositionView

from .doc import (
    endpoints,
    tags as doc_tags,
    # these originate in oas_types
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
)
from .swagger import blueprint as swagger_bp

blueprint = Blueprint("openapi", url_prefix="openapi")

NotYetImplemented = None
NotYetImplementedResponses = Responses(
    {"200": Response(description="A successful response")}
)


_openapi = {}  # type: OrderedDict[str, Any]
"""
Module-level container to hold the OAS spec that will be served-up on request. See `build_openapi_spec` for how it is
built.
"""

_openapi_all = OrderedDict()  # type: OrderedDict[str, Any]
"""
Module-level container to hold the OAS spec that may be served-up on request. The difference with this one is that it 
contains all endpoints, including those marked as `exclude`.
"""

CAST_2_SCHEMA = {int: Schema.Integer, float: Schema.Number, str: Schema.String}


@blueprint.listener("before_server_start")
def build_openapi_spec(app, _):
    hide_openapi_self = app.config.get("HIDE_OPENAPI_SELF", True)
    hide_sanic_static = app.config.get("HIDE_SANIC_STATIC", True)
    show_excluded = app.config.get("SHOW_OPENAPI_EXCLUDED", False)
    show_unused_tags = app.config.get("SHOW_OPENAPI_UNUSED_TAGS", False)

    openapi = _build_openapi_spec(
        app,
        hide_openapi_self,
        hide_excluded=True,
        show_unused_tags=show_unused_tags,
        hide_sanic_static=hide_sanic_static,
    )
    global _openapi
    _openapi = openapi.serialize()

    if show_excluded:
        openapi_all = _build_openapi_spec(
            app,
            hide_openapi_self,
            hide_excluded=False,
            show_unused_tags=True,
            hide_sanic_static=False,
        )
        global _openapi_all
        _openapi_all = openapi_all.serialize()


def _build_openapi_spec(
    app,
    hide_openapi_self=True,
    hide_excluded=True,
    show_unused_tags=False,
    hide_sanic_static=True,
):
    """
    Build the OpenAPI spec.

    :param app:
    :param hide_openapi_self:
    :param hide_excluded:
    :return: The spec
    :type app: sanic.Sanic
    :type hide_openapi_self: bool
    :type hide_excluded: bool
    :rtype OpenAPIv3
    """

    # We may reuse this later
    components = app.config.get("OPENAPI_COMPONENTS", None)
    if components:
        if not isinstance(components, Components):
            raise AssertionError(
                "You app.config's `OPENAPI_COMPONENTS` is not a `Components`: {}".format(
                    type(components)
                )
            )

    _oas_paths = list()  # type: List[Tuple[str, PathItem]]
    for _uri, _route in app.router.routes_all.items():
        # NOTE: TODO: there's no order here at all to either the _uri nor the _route. OAS specs do not define an order
        # NOTE: TODO: but people do rather like having at least document order for the routes.
        if hide_openapi_self:
            if (
                _uri.startswith("/" + blueprint.url_prefix)
                if blueprint.url_prefix
                else True
            ) and any([bp_uri in _uri for bp_uri in [r.uri for r in blueprint.routes]]):
                # Remove self-documentation from the spec
                continue
            if (
                _uri.startswith("/" + swagger_bp.url_prefix)
                if swagger_bp.url_prefix
                else True
            ) and any(
                [bp_uri in _uri for bp_uri in [r.uri for r in swagger_bp.routes]]
                + [not bool(swagger_bp.routes)]
            ):
                # Remove self-documentation from the spec by not adding.
                continue

        if "<file_uri" in _uri and hide_excluded:
            continue

        # We document the parameters at the PathItem, not at the Operation. First get the route parameters (if any)
        uri_parsed = _uri
        uri_for_opearion_id = _uri
        parameters = []  # type: List[Tuple[str, Parameter]]
        for _parameter in _route.parameters:
            uri_parsed = re.sub(
                "<" + _parameter.name + ".*?>", "{" + _parameter.name + "}", uri_parsed
            )
            uri_for_opearion_id = re.sub(
                "<" + _parameter.name + ".*?>", _parameter.name, uri_for_opearion_id
            )

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
            path_item = endpoints[_func]  # type: PathItem
            if path_item.x_exclude and hide_excluded:
                continue
            if str(_func.__module__) == "sanic.static" and hide_sanic_static:
                continue
            if path_item.x_exclude and not hide_excluded:
                path_item_summary = (
                    "[excluded] " + path_item.summary if path_item.summary else ""
                )
            else:
                path_item_summary = path_item.summary

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
                        except AssertionError as e:
                            raise AssertionError(
                                "For `{} {}` ({}) the `{}` param is invalid: {}".format(
                                    _method, _uri, str(_func), _parameter.name, e
                                )
                            )
                else:
                    parameters.append((_parameter.name, _parameter))

            pathitem_tag_names = [t.name for t in path_item.x_tags_holder]

            # If the route does not have a tag, use the blueprint's name.
            for _blueprint in app.blueprints.values():
                if not hasattr(_blueprint, "routes"):
                    continue

                for _bproute in _blueprint.routes:
                    if _bproute.handler != _func:
                        continue
                    if not pathitem_tag_names:
                        pathitem_tag_names.append(_blueprint.name)

            operation_id = "{}~~{}".format(
                _method.upper(), uri_for_opearion_id
            ).replace("/", "~")
            operations[_method.lower()] = Operation(
                **{
                    "operation_id": operation_id,
                    "summary": path_item_summary,
                    "description": path_item.description,
                    "parameters": [p[1] for p in parameters],
                    "tags": pathitem_tag_names,
                    "deprecated": path_item.x_deprecated_holder,
                    "responses": path_item.x_responses_holder,
                    "request_body": path_item.request_body,
                    # TODO
                    "servers": NotYetImplemented,
                    "security": NotYetImplemented,
                    "callbacks": NotYetImplemented,
                }
            )

            _path = PathItem(**operations)
            _oas_paths.append((uri_parsed, _path))

    # Possible contact
    _contact_name = app.config.get("API_CONTACT_NAME")
    _contact_url = app.config.get("API_CONTACT_URL")
    _contact_email = app.config.get("API_CONTACT_EMAIL")
    if any((_contact_email, _contact_name, _contact_url)):
        contact = Contact(name=_contact_name, email=_contact_email, url=_contact_url)
    else:
        contact = None

    # Possible license
    _license_name = app.config.get("API_LICENSE_NAME")
    _license_url = app.config.get("API_LICENSE_URL")
    if any((_license_name, _license_url)):
        _license = License(name=_license_name, url=_license_url)
    else:
        _license = None

    info = Info(
        title=app.config.get("API_TITLE", "API"),
        description=app.config.get("API_DESCRIPTION", "Description"),
        terms_of_service=app.config.get("API_TERMS_OF_SERVICE_URL"),
        contact=contact,
        _license=_license,
        version=app.config.get("API_VERSION", "1.0.0"),
    )

    _v3_paths = Paths(_oas_paths)
    _v3_tags = [t for t in doc_tags.values()]  # type: List[Tag]

    if not show_unused_tags:
        # Check that the tags are in use. This can depend on `hide_excluded`, so we re-use the _v3_paths.
        in_use_tags = []
        for tag in _v3_tags:
            for path, path_item in _v3_paths:
                for op_name in Operation.OPERATION_NAMES:
                    op = getattr(path_item, op_name)  # type: Operation
                    if op:
                        op_tag_names = op.tags
                        for op_tag_name in op_tag_names:
                            if tag.name == op_tag_name:
                                if not any(
                                    [t.name == op_tag_name for t in in_use_tags]
                                ):
                                    in_use_tags.append(tag)
        _v3_tags = in_use_tags

    servers = app.config.get("OPENAPI_SERVERS", None)
    if servers:
        if not isinstance(servers, list):
            raise AssertionError(
                "Your app.config's `OPENAPI_SERVERS` is not a list (of `Server`): {}".format(
                    type(servers)
                )
            )
        for server in servers:
            if not isinstance(server, Server):
                raise AssertionError(
                    "You app.config's `OPENAPI_SERVERS` server `{}` is not a `Server`: {}".format(
                        server, type(server)
                    )
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
        servers=servers,
        paths=_v3_paths,
        components=components,
        security=security,
        tags=_v3_tags,
        external_docs=external_docs,
    )
    return openapi


@blueprint.route("/spec.json")
def spec_v3(_):
    return sanic.response.json(_openapi)


@blueprint.route("/spec.all.json")
def spec_all(_):
    if _openapi_all:
        return sanic.response.json(_openapi_all)
    else:
        raise sanic.exceptions.NotFound()
