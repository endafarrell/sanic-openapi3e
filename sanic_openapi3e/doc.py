"""
TODO - note: everything is documented at the PathItem level, not the Operation level.
"""
from .oas_types import *  # pylint: disable=unused-wildcard-import, wildcard-import  # <<-- here for users

tags: Dict[str, Tag] = {}
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
    description=None, required=False, content=None,  # pylint: disable=redefined-outer-name
):
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
        endpoints[func].x_responses_holder[str(status_code)] = Response(
            description=description, headers=headers, content=content, links=links
        )
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
        if name not in tags:
            tags[name] = Tag(name=name, description=description)
        else:
            if not tags[name].description:
                tags[name] = Tag(name=name, description=description)
            else:
                if description:
                    if not tags[name].description == description:
                        msg = "Conflicting tag.description for tag `{}`: existing: `{}`, conflicting: `{}`".format(
                            name, tags[name].description, description
                        )
                        assert tags[name].description == description, msg
        endpoints[func].x_tags_holder.append(tags[name])
        return func

    return inner
