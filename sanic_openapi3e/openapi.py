"""
Build the OpenAPI spec.

Note: ```app.config.HIDE_OPENAPI_SELF``` is used to hide the ``/openapi`` and ``/swagger`` endpoints from the spec. The
      default value is `True`. To reveal these endpoints in the spec, set it explicitly to `False`.

Known limitations:
* Parameters are documented at the PathItem level, not at the underlying Operation level.

"""
import copy
import re
from collections import OrderedDict
from itertools import repeat
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import sanic
import sanic.exceptions
import sanic.request
import sanic.response
import sanic.router
import yaml
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
    Schema,
    SecurityRequirement,
    Server,
    Tag,
    endpoints,
)
from .doc import module_tags as doc_tags  # these originate in oas_types
from .doc import simple_snake2camel
from .swagger import blueprint as swagger_bp

blueprint = Blueprint("openapi", url_prefix="openapi")

NOT_YET_IMPLEMENTED = None
DEFAULT_YAML_CONTENT_TYPE = "application/x-yaml"
YAML_CONTENT_TYPE = "application/x-yaml"


_OPENAPI: Dict[str, Any] = {}
"""
Module-level container to hold the OAS spec that will be served-up on request. See `_build_openapi_spec` for how it is
built. It does not contain `cloaked` nor `exclude`d endpoints.
"""

_OPENAPI_UNCLOAKED: Dict[str, Any] = {}
"""
Module-level container to hold the OAS spec that will be served-up on request. The difference with this one is that it
contains `cloaked` but not `exclude`d endpoints.
"""

_OPENAPI_ALL: Dict[str, Any] = {}
"""
Module-level container to hold the OAS spec that may be served-up on request. The difference with this one is that it 
contains all endpoints, including `cloaked` and those marked as `exclude`d.
"""


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
    cloak_fn = app.config.get("OPENAPI_CLOAK_FN")
    global YAML_CONTENT_TYPE  # pylint: disable=global-statement
    YAML_CONTENT_TYPE = app.config.get("OPENAPI_YAML_CONTENTTYPE", DEFAULT_YAML_CONTENT_TYPE)

    openapi = _build_openapi_spec(
        app,
        operation_id_fn,
        hide_openapi_self=hide_openapi_self,
        hide_excluded=True,
        show_unused_tags=show_unused_tags,
        hide_sanic_static=hide_sanic_static,
        cloak_fn=cloak_fn,
        hide_cloaked=True,
    )
    global _OPENAPI  # pylint: disable=global-statement
    _OPENAPI = openapi.as_yamlable_object()

    openapi_uncloaked = _build_openapi_spec(
        app,
        operation_id_fn,
        hide_openapi_self=hide_openapi_self,
        hide_excluded=False,
        show_unused_tags=True,
        hide_sanic_static=False,
        cloak_fn=cloak_fn,
        hide_cloaked=False,
    )
    global _OPENAPI_UNCLOAKED  # pylint: disable=global-statement
    _OPENAPI_UNCLOAKED = openapi_uncloaked.as_yamlable_object()

    if show_excluded:
        openapi_all = _build_openapi_spec(
            app,
            operation_id_fn,
            hide_openapi_self=hide_openapi_self,
            hide_excluded=False,
            show_unused_tags=True,
            hide_sanic_static=False,
            cloak_fn=None,
            hide_cloaked=False,
        )
        global _OPENAPI_ALL  # pylint: disable=global-statement
        _OPENAPI_ALL = openapi_all.as_yamlable_object()


def _build_openapi_spec(  # pylint: disable=too-many-arguments, too-many-locals
    app: sanic.app.Sanic,
    operation_id_fn: Callable[[str, str, sanic.router.Route], str],
    hide_openapi_self=True,
    hide_excluded=True,
    show_unused_tags=False,
    hide_sanic_static=True,
    cloak_fn: Optional[Callable[[str, str, sanic.router.Route], bool]] = None,
    hide_cloaked: bool = True,
) -> OpenAPIv3:
    """
    Build the OpenAPI spec.
    """

    # We may reuse this later
    assert callable(operation_id_fn), operation_id_fn

    components: Components = _build_openapi_components(app)
    oas_paths = _buld_openapi_paths(
        app, components, hide_excluded, hide_openapi_self, hide_sanic_static, operation_id_fn, cloak_fn, hide_cloaked
    )
    paths: Paths = Paths(oas_paths)
    contact = _build_openapi_contact(app)
    _license = _build_openapi_license(app)
    info = _buld_openapi_info(app, contact, _license)
    tags = _build_openapi_tags(oas_paths, show_unused_tags)
    servers = _build_openapi_servers(app)
    security = _build_openapi_security(app)
    external_docs = _build_openapi_externaldocs(app)

    return OpenAPIv3(
        openapi=OpenAPIv3.version,
        info=info,
        paths=paths,
        servers=servers,
        components=components,
        security=security,
        tags=tags,
        external_docs=external_docs,
    )


def _build_openapi_components(app: sanic.app.Sanic) -> Components:
    components = app.config.get("OPENAPI_COMPONENTS")
    if components and not isinstance(components, Components):
        raise AssertionError("You app.config's `OPENAPI_COMPONENTS` is not a `Components`: {}".format(type(components)))
    if not components:
        components = Components()
    return components


def _build_openapi_externaldocs(app: sanic.app.Sanic):
    external_docs = app.config.get("OPENAPI_EXTERNAL_DOCS")
    if external_docs and not isinstance(external_docs, ExternalDocumentation):
        raise AssertionError(
            "You app.config's `OPENAPI_EXTERNAL_DOCS` is not a `ExternalDocumentation`: {}".format(type(external_docs))
        )
    return external_docs


def _build_openapi_security(app: sanic.app.Sanic) -> List[SecurityRequirement]:
    security = app.config.get("OPENAPI_SECURITY")
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
    return security


def _build_openapi_servers(app: sanic.app.Sanic) -> List[Server]:
    servers = app.config.get("OPENAPI_SERVERS")
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
    return servers


def _buld_openapi_info(app: sanic.app.Sanic, contact: Optional[Contact], _license: Optional[License]) -> Info:
    return Info(
        title=app.config.get("API_TITLE", "API"),
        description=app.config.get("API_DESCRIPTION", "Description"),
        terms_of_service=app.config.get("API_TERMS_OF_SERVICE_URL"),
        contact=contact,
        _license=_license,
        version=app.config.get("API_VERSION", "v1.0.0"),
    )


def _build_openapi_license(app: sanic.app.Sanic) -> Optional[License]:
    # Possible license
    _license: Optional[License] = None
    _license_name = app.config.get("API_LICENSE_NAME")
    _license_url = app.config.get("API_LICENSE_URL")
    if any((_license_name, _license_url)):
        _license = License(name=_license_name, url=_license_url)
    return _license


def _build_openapi_contact(app: sanic.app.Sanic) -> Optional[Contact]:
    # Possible contact
    contact: Optional[Contact] = None
    _contact_name = app.config.get("API_CONTACT_NAME")
    _contact_url = app.config.get("API_CONTACT_URL")
    _contact_email = app.config.get("API_CONTACT_EMAIL")
    if any((_contact_email, _contact_name, _contact_url)):
        contact = Contact(name=_contact_name, email=_contact_email, url=_contact_url)
    return contact


def _buld_openapi_paths(  # pylint: disable=too-many-arguments,too-many-locals,too-many-branches.too-many-statements
    app: sanic.app.Sanic,
    components: Components,
    hide_excluded: bool,
    hide_openapi_self: bool,
    hide_sanic_static: bool,
    operation_id_fn: Callable[[str, str, sanic.router.Route], str],
    cloak_fn: Optional[Callable[[str, str, sanic.router.Route], bool]] = None,
    hide_cloaked: bool = True,
) -> List[Tuple[str, PathItem]]:
    paths: List[Tuple[str, PathItem]] = []
    for _uri, _route in app.router.routes_all.items():
        # paranoia
        assert isinstance(_uri, str)
        assert isinstance(_route, sanic.router.Route), type(_route)

        # NOTE: TODO: there's no order here at all to either the _uri nor the _route. OAS specs do not define an order
        # NOTE: TODO: but people do rather like having at least document order for the routes.

        if _build_openapi_path_should_be_skipped(_uri, hide_excluded, hide_openapi_self):
            continue

        # We document the parameters at the PathItem, not at the Operation. First get the route parameters (if any)
        route_parameters, uri_parsed = _build_openapi_paths_routeparameters_and_uri(_route, _uri)

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

            if _build_openapi_paths_operations_should_be_skipped(
                _route, path_item, _method, _func, _uri, cloak_fn, hide_cloaked, hide_excluded, hide_sanic_static
            ):
                continue

            path_item_summary: Optional[str] = path_item.summary
            if path_item.x_exclude and not hide_excluded:
                path_item_summary = "[excluded] " + (path_item.summary or "")

            _op_parameters = _build_openapi_paths_opparameters(path_item, route_parameters, components)
            pathitem_tag_names: Set[str] = _build_openapi_paths_operations_tagnames(app, path_item, _func)

            operation_id = operation_id_fn(_method, _uri, _route)

            operations[_method.lower()] = Operation(
                operation_id=operation_id,
                deprecated=path_item.x_deprecated_holder,
                description=path_item.description,
                external_docs=path_item.x_external_docs_holder,
                parameters=_op_parameters,
                request_body=path_item.request_body,
                responses=path_item.x_responses_holder,
                servers=path_item.servers,
                summary=path_item_summary,
                tags=sorted(pathitem_tag_names),
                # TODO
                callbacks=NOT_YET_IMPLEMENTED,
                security=NOT_YET_IMPLEMENTED,
            )

            _path = PathItem(**operations)
            paths.append((uri_parsed, _path))
    return paths


def _build_openapi_paths_operations_should_be_skipped(  # pylint: disable=too-many-arguments
    route: sanic.router.Route,
    path_item: PathItem,
    method: str,
    handler_func,  # TODO - how should this be type hinted?
    uri: str,
    cloak_fn: Optional[Callable[[str, str, sanic.router.Route], bool]],
    hide_cloaked: bool,
    hide_excluded: bool,
    hide_sanic_static: bool,
):

    if path_item.x_exclude and hide_excluded:
        return True
    if str(handler_func.__module__) == "sanic.static" and hide_sanic_static:
        return True
    cloak = cloak_fn(method, uri, route) if cloak_fn else False
    return bool(cloak and hide_cloaked)


def _build_openapi_paths_opparameters(
    path_item: PathItem, route_parameters: List[Parameter], components: Components
) -> List[Union[Parameter, Reference]]:
    # Create a per-operation copy of the route params.
    _op_parameters: List[Union[Parameter, Reference]] = [*route_parameters]
    for _op_parameter in path_item.parameters:

        # Swagger v3.21.0 doesn't show the description for schema references, so lets try add some.
        _op_parameter = _upgrade_parameter_schema_description(_op_parameter, components)

        # Is this _op_parameter something new - like a query param - or an "upgrade annotation" for one of the
        # original route params?
        _orig_parameters = {
            (idx, p)
            for idx, p in enumerate(route_parameters)
            if isinstance(_op_parameter, Parameter) and p.name == _op_parameter.name
        }
        if _orig_parameters:
            assert len(_orig_parameters) == 1, (len(_orig_parameters), _orig_parameters)
            _orig_parameter_idx, _orig_parameter = _orig_parameters.pop()
            _op_parameters[_orig_parameter_idx] = _orig_parameter + _op_parameter
        else:
            _op_parameters.append(_op_parameter)
    return _op_parameters


def _upgrade_parameter_schema_description(
    _op_parameter: Union[Parameter, Reference], components: Components
) -> Union[Parameter, Reference]:

    if isinstance(_op_parameter, Parameter) and isinstance(_op_parameter.schema, Reference):
        # Swagger v3.21.0 doesn't show the description for references, so ...
        if not _op_parameter.description:
            if components and components.schemas:
                ref = components.schemas.get(_op_parameter.name)
                if isinstance(ref, Schema):
                    _parameter = copy.deepcopy(_op_parameter)
                    _parameter.description = ref.description
                    return _parameter
    return _op_parameter


def _build_openapi_path_should_be_skipped(_uri: str, hide_excluded: bool, hide_openapi_self: bool):

    if hide_openapi_self:
        if (_uri.startswith("/" + blueprint.url_prefix) if blueprint.url_prefix else True) and any(
            bp_uri in _uri for bp_uri in [r.uri for r in blueprint.routes]
        ):
            # Remove self-documentation from the spec
            return True
        if (_uri.startswith("/" + swagger_bp.url_prefix) if swagger_bp.url_prefix else True) and any(
            [bp_uri in _uri for bp_uri in [r.uri for r in swagger_bp.routes]] + [not bool(swagger_bp.routes)]
        ):
            # Remove self-documentation from the spec by not adding.
            return True
    return "<file_uri" in _uri and hide_excluded


def _build_openapi_paths_routeparameters_and_uri(_route, _uri: str) -> Tuple[List[Parameter], str]:
    uri_parsed: str = _uri
    route_parameters: List[Parameter] = []
    for _route_parameter in _route.parameters:
        uri_parsed = re.sub("<" + _route_parameter.name + ".*?>", "{" + _route_parameter.name + "}", uri_parsed)

        # Sanic route parameters can give us a name, we know that it is in the path and we may be able to establish
        # the basic schema.
        parameter = Parameter(
            name=_route_parameter.name,
            _in="path",
            description=None,
            required=True,
            deprecated=None,
            allow_empty_value=None,
            style=None,
            explode=None,
            allow_reserved=None,
            schema=CAST_2_SCHEMA.get(_route_parameter.cast),
            example=None,
            examples=None,
            content=None,
        )
        route_parameters.append(parameter)
    return route_parameters, uri_parsed


def _build_openapi_paths_operations_tagnames(app: sanic.app.Sanic, path_item: PathItem, _func: Callable) -> Set[str]:
    pathitem_tag_names: Set[str] = {t.name for t in path_item.x_tags_holder}
    if not pathitem_tag_names:
        # If the route does not have a tag, use the blueprint's name.
        for _blueprint in app.blueprints.values():
            if not hasattr(_blueprint, "routes"):
                # QQ: when was it last possible for a blueprint to not have routes ... ?
                continue

            for _bproute in _blueprint.routes:
                if _bproute.handler == _func:
                    pathitem_tag_names.add(_blueprint.name)
                    break
            if pathitem_tag_names:
                break
    return pathitem_tag_names


def _build_openapi_tags(_paths: List[Tuple[str, PathItem]], show_unused_tags: bool = False) -> List[Tag]:
    _tags: Set[Tag] = set(doc_tags.values())
    if not show_unused_tags:
        # Check that the tags are in use. This can depend on `hide_excluded`, so we re-use the _paths.
        in_use_tag_names: Set[str] = set()
        for _path, path_item in _paths:
            for operation in path_item.x_operations():
                for op_tag_name in operation.tags or []:
                    in_use_tag_names.add(op_tag_name)
        _tags = {tag for tag in _tags if tag.name in in_use_tag_names}
    return sorted(_tags)


########################################################################################################################
########################################################################################################################
# ROUTES
# ======================================================================================================================
# spec.json & spec.yml
@blueprint.route("/spec.json")
async def spec_v3_json(_):
    return await serve_spec(_OPENAPI, "json")


@blueprint.route("/spec.yml")
async def spec_v3_yaml(_):
    return await serve_spec(_OPENAPI, "yaml")


@blueprint.route("/uncloaked.json")
async def spec_v3_uncloaked_json(_):
    return await serve_spec(_OPENAPI_UNCLOAKED, "json")


@blueprint.route("/uncloaked.yml")
async def spec_v3_uncloaked_yaml(_):
    return await serve_spec(_OPENAPI_UNCLOAKED, "yaml")


# ======================================================================================================================
# spec.all.json / spec.all.yml


@blueprint.route("/spec.all.json")
async def spec_all_json(_):
    return await serve_spec(_OPENAPI_ALL, "json")


@blueprint.route("/spec.all.yml")
async def spec_all_yml(_):
    return await serve_spec(_OPENAPI_ALL, "yaml")


# ======================================================================================================================


async def serve_spec(spec: Dict, json_yaml: str):
    if not spec:
        # ... including empty dicts in this if block
        raise sanic.exceptions.NotFound("Not found")

    if json_yaml == "json":
        return sanic.response.json(spec)

    return sanic.response.HTTPResponse(
        content_type=YAML_CONTENT_TYPE,
        body=yaml.dump(spec, Dumper=yaml.CDumper, default_flow_style=False, explicit_start=False, sort_keys=False),
    )
