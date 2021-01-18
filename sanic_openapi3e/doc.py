"""
TODO - note: everything is documented at the PathItem level, not the Operation level.
"""
from .oas_types import *  # pylint: disable=unused-wildcard-import, wildcard-import  # <<-- here for users

module_tags: Dict[str, Tag] = {}
endpoints: Paths = Paths()


def deprecated():
    """Deprecate a route by marking it as `@doc.deprecated()`."""

    def inner(func):
        endpoints[func].x_deprecated_holder = True
        return func

    return inner


def exclude():
    """
    Deprecate a route by marking them as `@doc.exclude()`.
    """

    def inner(func):
        endpoints[func].x_exclude = True
        return func

    return inner


def external_docs(url: str, description: Optional[str] = None):  # pylint: disable=redefined-outer-name
    """
    Add an externalDoc to the route. Note that some UIs do not show route/operation external_docs.
    """

    def inner(func):

        endpoints[func].x_external_docs_holder = ExternalDocumentation(url, description=description)
        return func

    return inner


def description(text: str):
    """
    Add a description to the route by marking them `@doc.description("Descriptive text")`
    """

    def inner(func):
        endpoints[func].description = text
        return func

    return inner


# noinspection PyShadowingNames
def parameter(  # pylint: disable=too-many-arguments
    name: str,
    _in="query",
    description: Optional[str] = None,  # pylint: disable=redefined-outer-name
    required: Optional[bool] = None,
    deprecated: bool = False,  # pylint: disable=redefined-outer-name
    allow_empty_value: Optional[bool] = None,
    choices: Optional[List] = None,
    style: Optional[str] = None,
    explode: Optional[bool] = None,
    allow_reserved: Optional[bool] = None,
    schema: Optional[Union[Schema, Reference]] = None,
    example: Optional[Any] = None,
    examples: Optional[Dict[str, Union[Example, Reference]]] = None,
    content: Optional[Dict[str, MediaType]] = None,
):
    """
    Describes a single operation parameter.

    A unique parameter is defined by a combination of a name and location.

    Parameter Locations
    -------------------

    There are four possible parameter locations specified by the `location` ("in" in the spec) field:

    - path - Used together with Path Templating, where the parameter value is actually part of the operation's URL.
             This does not include the host or base path of the API. For example, in /items/{itemId}, the path
             parameter is itemId.
    - query - Parameters that are appended to the URL. For example, in /items?id=###, the query parameter is id.
    - header - Custom headers that are expected as part of the request. Note that RFC7230 states header names are
               case insensitive.
    - cookie - Used to pass a specific cookie value to the API.

    :param name: REQUIRED. The name of the parameter. Parameter names are case sensitive. If in is "path", the name
        field MUST correspond to the associated path segment from the path field in the Paths Object. See Path
        Templating for further information. If in is "header" and the name field is "Accept", "Content-Type" or
        "Authorization", the parameter definition SHALL be ignored. For all other cases, the name corresponds to the
        parameter name used by the in property.
    :param _in: REQUIRED. The location of the parameter. Possible values are "query", "header", "path" or
        "cookie".
    :param description: A brief description of the parameter. This could contain examples of use. CommonMark syntax
        MAY be used for rich text representation.
    :param required: Determines whether this parameter is mandatory. If the parameter location is "path", this
        property is REQUIRED and its value MUST be true. Otherwise, the property MAY be included and its default
        value is false.
    :param deprecated: Specifies that a parameter is deprecated and SHOULD be transitioned out of usage. Default
        value is false.
    :param allow_empty_value: Sets the ability to pass empty-valued parameters. This is valid only for query
        parameters and allows sending a parameter with an empty value. Default value is false. If style is used, and
        if behavior is n/a (cannot be serialized), the value of allowEmptyValue SHALL be ignored. Use of this
        property is NOT RECOMMENDED, as it is likely to be removed in a later revision.
    :param choices: Becomes the entries for schema.enum.
    :param style: Describes how the parameter value will be serialized depending on the type of the parameter value.
        Default values (based on value of ``location``):

        * for query - form;
        * for path - simple;
        * for header - simple;
        * for cookie - form.

    :param explode: When this is true, parameter values of type array or object generate separate parameters for
        each value of the array or key-value pair of the map. For other types of parameters this property has no
        effect. When style is form, the default value is true. For all other styles, the default value is false.
    :param allow_reserved: Determines whether the parameter value SHOULD allow reserved characters, as defined by
        RFC3986 ``:/?#[]@!$&'()*+,;=`` to be included without percent-encoding. This property only applies to
        parameters with an in value of query. The default value is false.
    :param schema: The schema defining the type used for the parameter.
    :param example: Example of the media type. The example SHOULD match the specified schema and encoding
        properties if present. The example field is mutually exclusive of the examples field. Furthermore, if
        referencing a schema which contains an example, the example value SHALL override the example provided by the
        schema. To represent examples of media types that cannot naturally be represented in JSON or YAML, a string
        value can contain the example with escaping where necessary.
    :param examples: Examples of the media type. Each example SHOULD contain a value in the correct format as
        specified in the parameter encoding. The examples field is mutually exclusive of the example field.
        Furthermore, if referencing a schema which contains an example, the examples value SHALL override the
        example provided by the schema.
    :param content: A map containing the representations for the parameter. The key is the media type and the value
        describes it. The map MUST only contain one entry.

    """

    if _in == "path":
        required = True

    # NOTE: the `schema` being passed in is __probably__ one of the "class static" ones, like `Schema.Integer` or
    #       `Schema.Strings`. If so, we __really__ do not want to modify those "class static" objects, instead we
    #       must make sure to only ever modify a copy. Not getting this right was the cause of a Heisenbug ....
    if schema is None:
        if choices is None:
            schema = Schema.String  # A basic default
        else:
            choices0_type = Schema.get_enum_type(choices)
            schema = Schema(_type=choices0_type, enum=choices)

    else:  # schema is not None
        if choices is None:
            pass  # OK - nothing to do
        else:
            # both schema and choices
            if isinstance(schema, Schema):
                schema = schema.clone()
                schema.add_enum(choices)
            else:
                raise ValueError("Cannot add choices to a Reference schema: define a new one with these choices.")

    assert schema

    def inner(func):
        _parameter = Parameter(
            name=name,
            _in=_in,
            description=description,
            required=required,
            deprecated=deprecated,
            style=style,
            explode=explode,
            allow_reserved=allow_reserved,
            allow_empty_value=allow_empty_value,
            schema=schema,
            example=example,
            examples=examples,
            content=content,
        )
        endpoints[func].parameters.append(_parameter)
        return func

    return inner


# noinspection PyShadowingNames
def request_body(
    content: Dict[str, MediaType],
    description: Optional[str] = None,  # pylint: disable=redefined-outer-name
    required: bool = False,
):
    """
    Describes a single request body.

    :param content: REQUIRED. The content of the request body. The key is a media type or media type range and the
        value describes it. For requests that match multiple keys, only the most specific key is applicable. e.g.
        ``text/plain`` overrides ``text/*``
    :param description: A brief description of the request body. This could contain examples of use. CommonMark
        syntax MAY be used for rich text representation.
    :param required: Determines if the request body is required in the request. Defaults to false.
    """

    def inner(func):
        _request_body = RequestBody(description=description, required=required, content=content,)
        endpoints[func].request_body = _request_body
        return func

    return inner


# noinspection PyShadowingNames
def response(
    status_code: Union[int, str],
    description: str,
    headers: Optional[Dict[str, Union[Header, Reference]]] = None,
    content: Optional[Dict[str, MediaType]] = None,
    links: Optional[Dict[str, Union[Link, Reference]]] = None,
):  # pylint: disable=redefined-outer-name
    """
    Add a response to the route.
    """

    def inner(func):
        if any((description, headers, content, links)):
            endpoints[func].x_responses_holder[str(status_code)] = Response(
                description=description, headers=headers, content=content, links=links
            )
        return func

    return inner


def servers(server_list: List[Server]):
    """
    Add an alternative server array to service all operations in this path. Note that if you have not set the top-level
    `Servers` (via `app.config.OPENAPI_SERVERS = [doc.Server(f"http://localhost:8000", "this server")]`) then this
    path-level `Servers` will not be shown in Swagger.
    """

    def inner(func):
        endpoints[func].servers = server_list
        return func

    return inner


def summary(text):
    """
    Add a summary to the route by marking them `@doc.summary("Summary text")`
    """

    def inner(func):
        endpoints[func].summary = text
        return func

    return inner


# noinspection PyShadowingNames
def tag(name, description=None):  # pylint: disable=redefined-outer-name
    """
    Add a tag - which gives Swagger grouping - to the route by marking them `@doc.tag("Tag", "Optional description")`
    """

    def inner(func):
        if name in module_tags:
            if module_tags[name].description:
                if description and module_tags[name].description != description:
                    msg = "Conflicting tag.description for tag `{}`: existing: `{}`, conflicting: `{}`".format(
                        name, module_tags[name].description, description
                    )
                    assert module_tags[name].description == description, msg
            else:
                module_tags[name] = Tag(name=name, description=description)
        else:
            module_tags[name] = Tag(name=name, description=description)
        endpoints[func].x_tags_holder.append(module_tags[name])
        return func

    return inner
