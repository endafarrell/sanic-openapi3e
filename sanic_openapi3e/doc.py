"""
TODO - note: everything is documented at the PathItem level, not the Operation level.
"""
from .oas_types import *  # <<-- here for users

tags = dict()  # type: Dict[str, Tag]
endpoints = Paths()  # type: Paths


def deprecated(boolean=True):
    """
    Deprecate a route by marking it as `@doc.deprecated()`, or `@doc.deprecated`.
    """
    if callable(boolean):
        # As "boolean" is a callable, and the decorator is expected to be given a bool,
        # it's fair (in this case) to assume that the sanic route handler was decorated
        # like:
        #
        # >>> @doc.deprecated
        # >>> async def a_deprecated_route_handler( ...)
        #
        # So, this time we note the function that was deprecated, and return it.
        endpoints[boolean].x_deprecated_holder = True
        return boolean

    # Not a callable? Ensure it's a bool
    assert isinstance(
        boolean, bool
    ), "Only `True` or `False` are bool, {} ({}) is not.".format(boolean, type(boolean))

    # Decorator called with a param, so we need to return a wrapped fn which will set the endpoint's value.
    def inner(func):
        endpoints[func].x_deprecated_holder = boolean
        return func

    return inner


def description(text):
    """
    Add a description to the route by marking them `@doc.description("Descriptive text")`
    """

    def inner(func):
        endpoints[func].description = text
        return func

    return inner


def exclude(boolean=True):
    """
    Deprecate a route by marking them as `@doc.exclude()`, or `@doc.exclude`.
    """
    if callable(boolean):
        # As "boolean" it's a callable, and the decorator is expected to be given a bool,
        # it's fair (in this case) to assume that the sanic route handler was decorated
        # like:
        #
        # >>> @doc.exclude
        # >>> async def an_excluded_route_handler( ...)
        #
        # So, this time we note the function that was excluded, and return it.
        endpoints[boolean].x_exclude = True
        return boolean

    # Not a callable? Ensure it's a bool
    assert isinstance(
        boolean, bool
    ), "Only `True` or `False` are bool, {} ({}) is not.".format(boolean, type(boolean))

    # Decorator called with a param, so we need to return a wrapped fn which will set the endpoint's value.
    def inner(func):
        endpoints[func].x_exclude = boolean
        return func

    return inner


# noinspection PyShadowingNames
def parameter(
    name,
    _in="query",
    description=None,
    required=False,
    deprecated=False,
    style=None,
    explode=None,
    allow_reserved=None,
    schema=None,  # type: Schema
    example=None,
    examples=None,
    content=None,
    choices=None,
):
    """TODO - note how `@doc.parameter.choices` becomes `schema.enum`."""
    if _in == "path":
        required = True

    # Schema and choices
    # if schema is None:
    #     if choices is not None:
    #         schema = Schema(enum=choices)
    #     else:
    #         schema = Schema.String

    if schema is None and choices is not None:
        schema = Schema(enum=choices)
    elif schema is None and choices is None:
        schema = Schema.String
    elif schema is not None and choices is not None:
        # ah: still need to ensure that these are compatible
        schema.addEnum(choices)
    elif schema is not None and choices is None:
        pass
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
    description=None,
    required=False,
    content=None,
):

    def inner(func):
        _request_body = RequestBody(
            description=description,
            required=required,
            content=content,
        )
        endpoints[func].request_body = _request_body
        return func

    return inner


# noinspection PyShadowingNames
def response(status_code, description=None, headers=None, content=None, links=None):
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
def tag(name, description=None):
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
