# pylint: disable=too-many-lines
"""
OpenAPI Spec 3.0.2 types, though without any `Specification Extensions
<https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#specificationExtensions>`_

Some terms in the spec are unsuitable for python, they have been changed in the code:

* `in` -> `_in`
* `type` -> `_type`
* `format` -> `_format`
* `$ref` -> `_ref`
* `license` -> `_license`

Given that these changes were already needed, some others were also added to keep with PEP8 naming conventions in this
code:

* `operationId` -> `operation_id`
*

In (many) other examples, terms using camelCase were changed to use underscores. Eg `readOnly` -> `read_only`.

Limitations
-----------
This implementation has some known limitations:

* Phrases in the spec like "MUST be in the format of a URL.", or "MUST be in the format of an email address." are noted,
  in the docs, but not checked.
* There is no accommodation for Specification Extensions.
* Schema.items is not well understood, your mileage may vary.
* SecurityScheme (specifically the REQUIREDs) are not well understood, and so no validation checks on REQUIRED fields
  are done.

"""
# pylint: disable=too-few-public-methods
import copy
import functools
import json
import traceback
import warnings
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, Union

import sanic.router


def _assert_type(element: Any, types: Sequence[Any], name: str, clazz: Type[Any]) -> None:
    """
    Utility to help assert types are only as expected.

    :param element: The element being checked
    :param types: The allowed types
    :param name: The name of the element
    :param clazz: The class containing the element
    """
    assert isinstance(types, tuple)
    assert isinstance(name, str)
    if element is not None and not isinstance(element, types):
        raise TypeError("Incorrect type ({}) for {}.{}, [{}]".format(type(element), clazz.__qualname__, name, types))


def _assert_required(element, name, clazz, why=""):
    assert isinstance(name, str)

    if not element:
        raise AssertionError("For `{}`, the field `{}` is required{}.".format(clazz.__qualname__, name, why))


def _assert_strictly_greater_than_zero(element, name, clazz):
    assert isinstance(name, str)
    if element is not None:
        assert isinstance(element, int), "For `{}`, the field `{}` must be an int if supplied.".format(
            clazz.__qualname__, name
        )
        assert element > 0, "For `{}`, the field `{}` must be strictly greater than 0: {} is not".format(
            clazz.__qualname__, name, element
        )


@functools.lru_cache(maxsize=64)
def simple_snake2camel(string: str) -> str:
    if "_" not in string:
        return string.strip()
    first, *rest = string.strip().lower().split("_")
    return first + "".join(ele.capitalize() for ele in rest)


@functools.lru_cache(maxsize=64)
def openapi_keyname(key: str) -> str:
    """
    Returns the OpenAPI name for keys.
    """
    return {
        "_format": "format",
        "_in": "in",
        "_license": "license",
        "_not": "not",
        "_ref": "$ref",
        "_type": "type",
        "additional_properties": "additionalProperties",
        "all_of": "allOf",
        "any_of": "anyOf",
        "bearer_format": "bearerFormat",
        "dollar_ref": "$ref",
        "exclusive_maximum": "exclusiveMaximum",
        "exclusive_minimum": "exclusiveMinimum",
        "external_docs": "externalDocs",
        "max_items": "maxItems",
        "max_length": "maxLength",
        "max_properties": "maxProperties",
        "min_items": "minItems",
        "min_length": "minLength",
        "min_properties": "minProperties",
        "multiple_of": "multipleOf",
        "one_of": "oneOf",
        "operation_id": "operationId",
        "property_name": "propertyName",
        "read_only": "readOnly",
        "request_body": "requestBody",
        "security_schemes": "securitySchemes",
        "terms_of_service": "termsOfService",
        "unique_items": "uniqueItems",
        "write_only": "writeOnly",
    }.get(key, simple_snake2camel(key))


NoneType = type(None)


class OObject:
    """A base object for sanic_openapi3e. Internal."""

    # @staticmethod
    # def _serialize(value: Any, for_repr=False, sort=False) -> Union[Dict, List[Dict], Any]:
    #     """
    #     Internal serialisation to a dict
    #     :param value: Any
    #     :return: dict
    #     """
    #     if isinstance(value, OObject):
    #         return value.serialize(sort=sort)
    #
    #     if isinstance(value, dict):
    #         return {openapi_keyname(k): OObject._serialize(v, for_repr=for_repr, sort=sort) for k, v in value.items()}
    #
    #     if isinstance(value, list):
    #         return [OObject._serialize(v, for_repr=for_repr, sort=sort) for v in value]
    #
    #     return value

    @staticmethod
    def _as_yamlable_object(
        value: Any, sort=False, opt_key: Optional[str] = None
    ) -> Union[Dict, str, bytes, int, float, List]:
        if isinstance(value, OObject):
            return value.as_yamlable_object(sort=sort, opt_key=opt_key)
        if isinstance(value, (str, bytes, int, float)):
            return value
        if isinstance(value, list):
            if sort:
                value = sorted(value)
            return [OObject._as_yamlable_object(v, sort=sort, opt_key=opt_key) for v in value]
        if isinstance(value, (dict, OrderedDict)):
            items = list(value.items())
            if sort:
                items = sorted(items)
            return {
                key2: OObject._as_yamlable_object(value2, sort=sort, opt_key=f"{opt_key}.{key2}")
                for key2, value2 in items
            }

        raise TypeError(f"{type(value)}, value={value} opt_key={opt_key}")

    def as_yamlable_object(  # pylint: disable=too-many-branches
        self, sort=False, opt_key: Optional[str] = None
    ) -> Dict:
        _repr = {}

        if not hasattr(self, "__dict__"):
            raise TypeError(str(opt_key) + " " + self.__class__.__qualname__ + " " + repr(self))

        for key, value in self.__dict__.items():

            # Allow False bools, but not other falsy values - UNLESS self is a SecurityRequirement
            if (value is not False) and (not value):
                if value == [] and self.__class__.__qualname__ == "SecurityRequirement":
                    pass
                else:
                    continue
            if key.startswith("x_"):
                continue
            if key == "deprecated" and value is False:
                # By default, items in specs are `deprecated: false` - these are not desirable in the specs
                continue
            key2 = openapi_keyname(key)
            value2: Union[Dict, List, str, bytes, int, float, bool]
            if value is False or value is True:
                value2 = value

            ############################################################################################################
            # List of yamlable objects for element in value
            elif key2 == "parameters" and self.__class__ in (PathItem, Operation):
                value2 = [OObject.as_yamlable_object(e, sort=sort, opt_key=f"{opt_key}.{key2}") for e in value]
            # elif key2 == "security":
            #     value2 = [
            #         SecurityRequirement._as_yamlable_object(  # pylint: disable=protected-access
            #             sr, opt_key=f"{opt_key}.{key2}"
            #         )
            #         for sr in value
            #     ]
            #     print(209, key, key2, value, value2)
            ############################################################################################################
            # dicts of yamlable objects for items() value
            elif key2 == "responses" and self.__class__ == Components:
                value2 = {
                    key: value.as_yamlable_object(opt_key=f"{opt_key}.{key2}")
                    for key, value in Responses.DEFAULT_RESPONSES.items()
                }

            elif key2 == "examples":
                value2 = {
                    key3: OObject._as_yamlable_object(value3, opt_key=f"{opt_key}.{key2}")
                    for key3, value3 in value.items()
                }
            ############################################################################################################
            # paths are a special case
            elif key2 == "paths":
                value2 = {
                    uri: OObject.as_yamlable_object(path_item, opt_key=f"{opt_key}.{uri}")
                    for uri, path_item in value._paths  # pylint: disable=protected-access
                }
            ############################################################################################################
            # sort the schemas
            elif key2 == "schemas":
                # Everyone wants sorted schema entries! Note that as `dict`s, they require OObject._as_yamlable_object
                value2 = OObject._as_yamlable_object(value, sort=True, opt_key=f"{opt_key}.{key2}")
            ############################################################################################################
            # default - for known OObjects
            elif isinstance(value, OObject) and hasattr(value, "__dict__"):
                value2 = OObject.as_yamlable_object(value, sort=sort, opt_key=f"{opt_key}.{key}")
            else:
                # Note how this uses the OObject._as_yamlable_object
                value2 = OObject._as_yamlable_object(value, opt_key=f"{opt_key}.{key2}")

            _repr[key2] = value2

        if sort:
            # Note: py36 does not have any (eternally dependable) ordering for dicts, but py37+
            # remembers insert-order.
            return {key: value for key, value in sorted(_repr.items())}  # pylint: disable=unnecessary-comprehension

        return _repr

    def serialize(self, sort=False) -> OrderedDict:
        """
        Serialisation to a dict.

        :return: A dict serialisation of self.
        :rtype: OrderedDict
        """
        # _repr = OrderedDict()  # type: OrderedDict[str, Union[Dict, List]]
        # for key, value in self.__dict__.items():
        #
        #     if callable(value):
        #         continue
        #     if not value and not isinstance(value, bool):
        #         continue
        #     if key.startswith("x_") and not for_repr:
        #         continue
        #     key2 = openapi_keyname(key)
        #     value2: Union[Dict, List]
        #     if key2 == "parameters" and self.__class__.__qualname__ in ("PathItem", "Operation",):
        #         value2 = list(OObject._serialize(e, for_repr=for_repr, sort=sort) for e in value)
        #     elif key2 == "security":
        #         value2 = list(
        #             SecurityRequirement._serialize(sr, for_repr=for_repr)  # pylint: disable=protected-access
        #             for sr in value
        #         )
        #     elif key2 == "schemas":
        #         # Everyone wants sorted schema entries!
        #         value2 = OObject._serialize(value, sort=True)
        #     else:
        #         value2 = OObject._serialize(value)
        #     if not value2 or callable(value2):
        #
        #         continue
        #
        #     _repr[key2] = value2
        # if sort:
        #     _sorted_repr = OrderedDict()
        #     for key in sorted(_repr.keys()):
        #         _sorted_repr[key] = _repr[key]
        # return _repr
        yamable = self.as_yamlable_object(sort=sort)
        # if self.__class__.__qualname__ == "OpenAPIv3":
        #     print(278)
        #     # There is special ordering for this
        #     _repr = OrderedDict()
        #     _repr["openapi"] = getattr(self, "version")
        #     for key in ("info", "servers", "paths", "components", "security", "tags" "externalDocs"):
        #         _value = yamable.get(key)
        #         if key == "tags":
        #             print(284, _value)
        #         if _value:
        #             _repr[key] = _value
        #
        # else:
        #     _repr = OrderedDict(yamable)
        # return _repr
        return OrderedDict(yamable)

    def __str__(self):
        return json.dumps(self.serialize(), sort_keys=True)

    def __repr__(self):
        return "{}({})".format(self.__class__.__qualname__, json.dumps(self.serialize(), sort_keys=True),)


# --------------------------------------------------------------- #
# Primitive data types
# --------------------------------------------------------------- #


class OType(OObject):
    """A sanic_openapi3e class to hold OpenAPI types. Internal."""

    name: str = "otype"
    formats: List[str] = []


# class OInteger(OType):
#     """A sanic_openapi3e class to hold OpenAPI integer types of formats `int32` and/or `int64`."""
#
#     name = "integer"
#     formats = ["int32", "int64"]
#
#     def __init__(self, value: int, _format: Optional[str] = None):
#         if _format:
#             assert _format in self.formats
#         self.format = _format
#         self.value = value
#
#     def serialise(self) -> int:
#         return self.value


# class ONumber(OType):
#     """A sanic_openapi3e class to hold OpenAPI non-integer numeric types of formats `float` and `double`."""
#
#     name = "number"
#     formats = ["float", "double"]
#
#     def __init__(self, value: float, _format: Optional[str] = None):
#         if _format:
#             assert _format in self.formats
#         self.format = _format
#         self.value = value
#
#     def serialise(self) -> float:
#         return self.value


# class OString(OType):
#     """
#     A sanic_openapi3e class to hold OpenAPI string types of formats `byte`, `binary`, `date`, `date-time` and
#     `password`.
#     """
#
#     name = "string"
#     formats = ["byte", "binary", "date", "date-time", "password"]
#
#     def __init__(self, value: str, _format: Optional[str] = None):
#         if _format:
#             assert _format in self.formats
#         self.format = _format
#         self.value = value
#
#     def serialise(self) -> str:
#         return self.value


# class OBoolean(OType):
#     """
#     A sanic_openapi3e class to hold OpenAPI string types of formats `byte`, `binary`, `date`, `date-time` and
#     `password`.
#     """
#
#     name = "boolean"
#     formats: List[str] = []
#
#     def __init__(self, value: bool, _format: Optional[str] = None):
#         if _format:
#             assert _format in self.formats
#         self.format = _format
#         self.value = value
#
#     def serialise(self) -> bool:
#         return self.value


# OTypeFormats: Dict[str, List[str]] = {
#     _type.name: _type.formats for _type in (OInteger, ONumber, OString, OBoolean)
# }


# --------------------------------------------------------------- #
# Info Object
# --------------------------------------------------------------- #
class Contact(OObject):
    """Contact information for the exposed API."""

    def __init__(
        self, name: Optional[str] = None, url: Optional[str] = None, email: Optional[str] = None,
    ):
        """
        Contact information for the exposed API.

        :param name: The identifying name of the contact person/organization.
        :param url: The URL pointing to the contact information. MUST be in the format of a URL.
        :param email: The email address of the contact person/organization. MUST be in the format of an email address.
        """
        _assert_type(name, (str,), "name", self.__class__)
        _assert_type(url, (str,), "url", self.__class__)
        _assert_type(email, (str,), "email", self.__class__)

        self.name = name
        """The identifying name of the contact person/organization."""

        self.url = url
        """The URL pointing to the contact information. MUST be in the format of a URL."""

        self.email = email
        """The email address of the contact person/organization. MUST be in the format of an email address."""


class License(OObject):
    """License information for the exposed API."""

    def __init__(self, name: str, url: Optional[str] = None):
        """
        License information for the exposed API.

        :param name: REQUIRED. The license name used for the API.
        :param url: A URL to the license used for the API. MUST be in the format of a URL.
        """
        _assert_type(name, (str,), "name", self.__class__)
        _assert_type(url, (str,), "url", self.__class__)

        _assert_required(name, "name", self.__class__)

        self.name = name
        """REQUIRED. The license name used for the API."""

        self.url = url
        """A URL to the license used for the API. MUST be in the format of a URL."""


class Info(OObject):
    """
    The object provides metadata about the API. The metadata MAY be used by the clients if needed, and MAY be
    presented in editing or documentation generation tools for convenience.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        title: str,
        version: str,
        description: Optional[str] = None,
        terms_of_service: Optional[str] = None,
        contact: Optional[Contact] = None,
        _license: Optional[License] = None,
    ):
        """
        The object provides metadata about the API. The metadata MAY be used by the clients if needed, and MAY be
        presented in editing or documentation generation tools for convenience.

        :param title: REQUIRED. The title of the application.
        :param description: A short description of the application. CommonMark syntax MAY be used for rich text
            representation.
        :param terms_of_service: A URL to the Terms of Service for the API. MUST be in the format of a URL.
        :param contact: The contact information for the exposed API.
        :param _license: The license information for the exposed API.
        :param version: REQUIRED. The version of the OpenAPI document (which is distinct from the OpenAPI Specification
            version or the API implementation version).


        """
        _assert_type(title, (str,), "title", self.__class__)
        _assert_type(description, (str,), "description", self.__class__)
        _assert_type(terms_of_service, (str,), "terms_of_service", self.__class__)
        _assert_type(contact, (Contact,), "contact", self.__class__)
        _assert_type(_license, (License,), "_license", self.__class__)
        _assert_type(version, (str,), "version", self.__class__)

        _assert_required(title, "title", self.__class__)
        _assert_required(version, "version", self.__class__)

        self.title = title
        """REQUIRED. The title of the application."""

        self.version = version
        """
        REQUIRED. The version of the OpenAPI document (which is distinct from the OpenAPI Specification version or the 
        API implementation version).
        """

        self.description = description
        """A short description of the application. CommonMark syntax MAY be used for rich text representation."""

        self.terms_of_service = terms_of_service
        """A URL to the Terms of Service for the API. MUST be in the format of a URL."""

        self.contact = contact
        """The contact information for the exposed API."""

        self.license = _license
        """The license information for the exposed API."""


# --------------------------------------------------------------- #
# Server Object. Since v3
# --------------------------------------------------------------- #
class ServerVariable(OObject):
    """An object representing a Server Variable for server URL template substitution."""

    def __init__(self, default: str, enum: List[str] = None, description: Optional[str] = None):
        """
        An object representing a Server Variable for server URL template substitution.

        :param enum:
        :param default: REQUIRED. The default value to use for substitution, which SHALL be sent if an alternate value
            is not supplied. Note this behavior is different than the Schema Object's treatment of default values,
            because in those cases parameter values are optional.
        :param description: An optional description for the server variable. CommonMark syntax MAY be used for rich text
            representation.
        """
        _assert_type(enum, (list,), "enum", self.__class__)
        _assert_type(default, (str,), "default", self.__class__)
        _assert_type(description, (str,), "description", self.__class__)

        _assert_required(default, "default", self.__class__)

        if enum:
            # All strings
            if {type(e) for e in enum} != {type("str")}:
                raise AssertionError("For `{}`, all enum values must be str.".format(self.__class__.__qualname__))
            # All unique
            if len(set(enum)) != len(enum):
                raise AssertionError("For `{}`, all enum values must be unique.".format(self.__class__.__qualname__))
        self.enum = enum
        """An enumeration of string values to be used if the substitution options are from a limited set."""

        self.default = default
        """
        REQUIRED. The default value to use for substitution, which SHALL be sent if an alternate value is not supplied. 
        Note this behavior is different than the Schema Object's treatment of default values, because in those cases 
        parameter values are optional.
        """

        self.description = description
        """
        An optional description for the server variable. CommonMark syntax MAY be used for rich text representation.
        """


class Server(OObject):
    """An object representing a Server."""

    def __init__(
        self, url: str, description: Optional[str] = None, variables: Optional[Dict[str, ServerVariable]] = None,
    ):
        """
        An object representing a Server.

        :param url: REQUIRED. A URL to the target host. This URL supports Server Variables and MAY be relative, to
            indicate that the host location is relative to the location where the OpenAPI document is being served.
            Variable substitutions will be made when a variable is named in ``{brackets}``.
        :param description: An optional string describing the host designated by the URL. CommonMark syntax MAY be used
            for rich text representation.
        :param variables: A map between a variable name and its value. The value is used for substitution in the
            server's URL template.
        """
        _assert_type(url, (str,), "url", self.__class__)
        _assert_type(description, (str,), "description", self.__class__)
        _assert_type(variables, (str,), "variables", self.__class__)

        _assert_required(url, "url", self.__class__)

        self.url = url
        """
        REQUIRED. A URL to the target host. This URL supports Server Variables and MAY be relative, to indicate that the 
        host location is relative to the location where the OpenAPI document is being served. Variable substitutions 
        will be made when a variable is named in {brackets}."""

        self.description = description
        """
        An optional string describing the host designated by the URL. CommonMark syntax MAY be used for rich text 
        representation.
        """
        self.variables = variables
        """
        A map between a variable name and its value. The value is used for substitution in the server's URL template.
        """


# --------------------------------------------------------------- #
# Components Object. Since v3
# --------------------------------------------------------------- #
class Reference(OObject):
    """
    A simple object to allow referencing other components in the specification, internally and externally.

    The Reference Object is defined by JSON Reference and follows the same structure, behavior and rules.

    For this specification, reference resolution is accomplished as defined by the JSON Reference specification and not
    by the JSON Schema specification.
    """

    def __init__(self, _ref: str):
        """
        A simple object to allow referencing other components in the specification, internally and externally.

        The Reference Object is defined by JSON Reference and follows the same structure, behavior and rules.

        For this specification, reference resolution is accomplished as defined by the JSON Reference specification and
        not by the JSON Schema specification.

        :param _ref: REQUIRED. The reference string.
        """
        _assert_type(_ref, (str,), "_ref ($ref)", self.__class__)

        _assert_required(_ref, "_ref ($ref)", self.__class__)

        self.dollar_ref = _ref
        """REQUIRED. The reference string."""


class Discriminator(OObject):
    """
    When request bodies or response payloads may be one of a number of different schemas, a discriminator object can be
    used to aid in serialization, deserialization, and validation. The discriminator is a specific object in a schema
    which is used to inform the consumer of the specification of an alternative schema based on the value associated
    with it.

    When using the discriminator, inline schemas will not be considered.

    Note: in sanic_openapi3e, this object is not well tested.
    """

    def __init__(self, property_name: str, mapping: Optional[Dict[str, str]] = None):
        """
        When request bodies or response payloads may be one of a number of different schemas, a discriminator object can
        be used to aid in serialization, deserialization, and validation. The discriminator is a specific object in a
        schema which is used to inform the consumer of the specification of an alternative schema based on the value
        associated with it.

        When using the discriminator, inline schemas will not be considered.

        :param property_name: REQUIRED. The name of the property in the payload that will hold the discriminator value.
        :param mapping: An object to hold mappings between payload values and schema names or references.
        
        """
        _assert_type(property_name, (str,), "property_name", self.__class__)
        _assert_type(mapping, (dict,), "mapping", self.__class__)

        _assert_required(property_name, "property_name", self.__class__)
        if mapping:
            for m_name, m_value in mapping.items():
                if not isinstance(m_value, str):
                    raise AssertionError(
                        "For `{}.mapping[{}]` the value must be a str.".format(self.__class__.__qualname__, m_name)
                    )

        self.property_name = property_name
        """REQUIRED. The name of the property in the payload that will hold the discriminator value."""

        self.mapping = mapping
        """An object to hold mappings between payload values and schema names or references."""


class XML(OObject):
    """
    A metadata object that allows for more fine-tuned XML model definitions.

    When using arrays, XML element names are not inferred (for singular/plural forms) and the name property SHOULD be
    used to add that information. See examples for expected behavior.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        prefix: Optional[str] = None,
        attribute: bool = False,
        wrapped: bool = False,
    ):
        """
        A metadata object that allows for more fine-tuned XML model definitions.

        When using arrays, XML element names are not inferred (for singular/plural forms) and the name property SHOULD
        be used to add that information. See examples for expected behavior.

        :param name: Replaces the name of the element/attribute used for the described schema property. When defined
            within items, it will affect the name of the individual XML elements within the list. When defined alongside
            type being array (outside the items), it will affect the wrapping element and only if wrapped is true. If
            wrapped is false, it will be ignored.
        :param namespace: The URI of the namespace definition. Value MUST be in the form of an absolute URI.
        :param prefix: The prefix to be used for the name.
        :param attribute: Declares whether the property definition translates to an attribute instead of an element.
            Default value is false.
        :param wrapped: MAY be used only for an array definition. Signifies whether the array is wrapped (for example,
            <books><book/><book/></books>) or unwrapped (<book/><book/>). Default value is false. The definition takes
            effect only when defined alongside type being array (outside the items).
        """
        _assert_type(name, (str,), "name", self.__class__)
        _assert_type(namespace, (str,), "namespace", self.__class__)
        _assert_type(prefix, (str,), "prefix", self.__class__)
        _assert_type(attribute, (bool,), "attribute", self.__class__)
        _assert_type(wrapped, (bool,), "wrapped", self.__class__)

        self.name = name
        """
        Replaces the name of the element/attribute used for the described schema property. When defined within items, it
        will affect the name of the individual XML elements within the list. When defined alongside type being array 
        (outside the items), it will affect the wrapping element and only if wrapped is true. If wrapped is false, it 
        will be ignored.
        """

        self.namespace = namespace
        """The URI of the namespace definition. Value MUST be in the form of an absolute URI."""

        self.prefix = prefix
        """The prefix to be used for the name."""

        self.attribute = attribute
        """
        Declares whether the property definition translates to an attribute instead of an element. Default value is 
        false.
        """

        self.wrapped = wrapped
        """
        MAY be used only for an array definition. Signifies whether the array is wrapped (for example, 
        ``(<books><book/><book/></books>``) or unwrapped (``<book/><book/>``). Default value is false. The definition 
        takes effect only when defined alongside type being array (outside the items).
        """


class ExternalDocumentation(OObject):
    """Allows referencing an external resource for extended documentation."""

    def __init__(self, url: str, description: Optional[str] = None):
        """
        Allows referencing an external resource for extended documentation.

        :param url: REQUIRED. The URL for the target documentation. Value MUST be in the format of a URL.
        :param description: A short description of the target documentation. CommonMark syntax MAY be used for rich text
            representation.
        """
        _assert_type(description, (str,), "name", self.__class__)
        _assert_type(url, (str,), "url", self.__class__)

        _assert_required(url, "url", self.__class__)

        self.description = description
        """
        A short description of the target documentation. CommonMark syntax MAY be used for rich text representation.
        """

        self.url = url
        """REQUIRED. The URL for the target documentation. Value MUST be in the format of a URL."""


class Example(OObject):
    """
    In the `spec <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#example-object>`_ there is
    no top-line description, but there is supplemental doc.

    In all cases, the example value is expected to be compatible with the type schema of its associated value. Tooling
    implementations MAY choose to validate compatibility automatically, and reject the example value(s) if incompatible.
    """

    def __init__(
        self,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        value: Optional[Any] = None,
        external_value: Optional[str] = None,
    ):
        """
        In the `spec <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#example-object>`_ there
        is no top-line description, but there is supplemental doc.

        In all cases, the example value is expected to be compatible with the type schema of its associated value.
        Tooling implementations MAY choose to validate compatibility automatically, and reject the example value(s) if
        incompatible.

        :param summary: Short description for the example.
        :param description: Long description for the example. CommonMark syntax MAY be used for rich text
            representation.
        :param value: Embedded literal example. The value field and externalValue field are mutually exclusive. To
            represent examples of media types that cannot naturally represented in JSON or YAML, use a string value to
            contain the example, escaping where necessary.
        :param external_value: A URL that points to the literal example. This provides the capability to reference
            examples that cannot easily be included in JSON or YAML documents. The value field and externalValue field
            are mutually exclusive.

        """
        _assert_type(summary, (str,), "summary", self.__class__)
        _assert_type(description, (str,), "description", self.__class__)
        # Note: value can be Any
        _assert_type(external_value, (str,), "external_value", self.__class__)

        assert not (value and external_value)

        # Assignment and docs
        self.summary = summary
        """Short description for the example."""

        self.description = description
        """Long description for the example. CommonMark syntax MAY be used for rich text representation."""

        self.value = value
        """
        Embedded literal example. The value field and externalValue field are mutually exclusive. To represent examples 
        of media types that cannot naturally represented in JSON or YAML, use a string value to contain the example, 
        escaping where necessary.
        """

        self.external_value = external_value
        """
        A URL that points to the literal example. This provides the capability to reference examples that cannot easily 
        be included in JSON or YAML documents. The value field and externalValue field are mutually exclusive.
        """


class Header(OObject):  # pylint: disable=too-many-instance-attributes
    """
    The Header Object follows the structure of the Parameter Object with the following changes:

    - name MUST NOT be specified, it is given in the corresponding headers map.
    - o-in (`in`) MUST NOT be specified, it is implicitly in header.
    - All traits that are affected by the location MUST be applicable to a location of header (for example, style).
    """

    def __init__(  # pylint: disable=too-many-arguments, too-many-locals
        self,
        description: Optional[str] = None,
        required: bool = False,
        deprecated: bool = False,
        allow_empty_value: bool = False,
        style: Optional[str] = None,
        explode: bool = False,
        allow_reserved: bool = False,
        schema: Optional[Union["Schema", Reference]] = None,
        example: Optional[Any] = None,
        examples: Optional[Dict[str, Union[Example, Reference]]] = None,
        content: Optional[Dict[str, "MediaType"]] = None,
    ):
        """
        The Header Object follows the structure of the Parameter Object with the following changes:

        - name MUST NOT be specified, it is given in the corresponding headers map.
        - o-in (`in`) MUST NOT be specified, it is implicitly in header.
        - All traits that are affected by the location MUST be applicable to a location of header (for example, style).

        :param description: A brief description of the parameter. This could contain examples of use. CommonMark syntax
            MAY be used for rich text representation.
        :param required: Determines whether this parameter is mandatory. If the parameter ``_in`` is "path", this
            property is REQUIRED and its value MUST be true. Otherwise, the property MAY be included and its default
            value is false. Note that this is not checked by sanic-openapi3e.
        :param deprecated: Specifies that a parameter is deprecated and SHOULD be transitioned out of usage.
        :param allow_empty_value: Sets the ability to pass empty-valued parameters. This is valid only for query
            parameters and allows sending a parameter with an empty value. Default value is false. If style is used,
            and if behavior is n/a (cannot be serialized), the value of allowEmptyValue SHALL be ignored.
        :param style: Describes how the parameter value will be serialized depending on the type of the parameter value.
            Default values (based on value of in): for query - form; for path - simple; for header - simple; for
            cookie - form.
        :param explode: When this is true, parameter values of type array or object generate separate parameters for
            each value of the array or key-value pair of the map. For other types of parameters this property has no
            effect. When style is form, the default value is true. For all other styles, the default value is false.
        :param allow_reserved: Determines whether the parameter value SHOULD allow reserved characters, as defined by
            RFC3986 ``:/?#[]@!$&'()*+,;=`` to be included without percent-encoding. This property only applies to
            parameters with an `_in` value of query. The default value is false.
        :param schema: The schema defining the type used for the parameter.
        :param example: Example of the media type. The example SHOULD match the specified schema and encoding properties
            if present. The example object is mutually exclusive of the examples object. Furthermore, if referencing a
            schema which contains an example, the example value SHALL override the example provided by the schema. To
            represent examples of media types that cannot naturally be represented in JSON or YAML, a string value can
            contain the example with escaping where necessary.
        :param examples: Examples of the media type. Each example SHOULD contain a value in the correct format as
            specified in the parameter encoding. The examples object is mutually exclusive of the example object.
            Furthermore, if referencing a schema which contains an example, the examples value SHALL override the
            example provided by the schema.
        :param content: A map containing the representations for the parameter. The key is the media type and the value
            describes it. The map MUST only contain one entry.
        """

        _assert_type(description, (str,), "description", self.__class__)
        _assert_type(required, (bool,), "required", self.__class__)
        _assert_type(deprecated, (bool,), "deprecated", self.__class__)
        _assert_type(allow_empty_value, (bool,), "allow_empty_value", self.__class__)
        _assert_type(style, (str,), "style", self.__class__)
        _assert_type(explode, (bool,), "explode", self.__class__)
        _assert_type(allow_reserved, (bool,), "allow_reserved", self.__class__)
        _assert_type(schema, (Schema, Reference), "schema", self.__class__)
        # Note: examples is specified to be "Any"
        _assert_type(examples, (dict,), "examples", self.__class__)
        _assert_type(content, (dict,), "content", self.__class__)

        # Validations.
        assert not (example and examples)
        if examples:
            for ex_name, ex in examples.items():
                if not isinstance(ex, (Example, Reference)):
                    raise AssertionError(
                        "For `{}.examples`, values must be an `Example` or a `Reference`. For {} it is a {}".format(
                            self.__class__.__qualname__, ex_name, type(ex)
                        )
                    )
        if content:
            if len(list(content.values())) != 1:
                raise AssertionError("For `{}.content` MUST only contain one entry".format(self.__class__.__qualname__))
            for c_name, media_type in content.items():
                if not isinstance(media_type, MediaType):
                    raise TypeError(
                        "For `{}.content`, values must be a `MediaType`. For {} it is a {}".format(
                            self.__class__.__qualname__, c_name, type(media_type)
                        )
                    )

        # Assignments and docs
        self.description = description
        """
        A brief description of the parameter. This could contain examples of use. CommonMark syntax MAY be used for rich 
        text representation.
        """

        self.required = required
        """
        Determines whether this parameter is mandatory. If the parameter location is "path", this property is REQUIRED 
        and its value MUST be true. Otherwise, the property MAY be included and its default value is false.
        """

        self.deprecated = deprecated
        """Specifies that a parameter is deprecated and SHOULD be transitioned out of usage."""

        self.allow_empty_value = allow_empty_value
        """
        Sets the ability to pass empty-valued parameters. This is valid only for query parameters and allows sending a 
        parameter with an empty value. Default value is false. If style is used, and if behavior is n/a (cannot be 
        serialized), the value of allowEmptyValue SHALL be ignored.
        """

        self.style = style
        """
        Describes how the parameter value will be serialized depending on the type of the parameter value. Default 
        values (based on value of in): for query - form; for path - simple; for header - simple; for cookie - form.
        """

        self.explode = explode
        """
        When this is true, parameter values of type array or object generate separate parameters for each value of the 
        array or key-value pair of the map. For other types of parameters this property has no effect. When style is 
        form, the default value is true. For all other styles, the default value is false.
        """

        self.allow_reserved = allow_reserved
        """
        Determines whether the parameter value SHOULD allow reserved characters, as defined by RFC3986 
        ``:/?#[]@!$&'()*+,;=`` to be included without percent-encoding. This property only applies to parameters with an 
        in value of query. The default value is false."""

        self.schema = schema
        """The schema defining the type used for the parameter."""

        self.example = example
        """
        Example of the media type. The example SHOULD match the specified schema and encoding properties if present. The 
        example object is mutually exclusive of the examples object. Furthermore, if referencing a schema which contains 
        an example, the example value SHALL override the example provided by the schema. To represent examples of media 
        types that cannot naturally be represented in JSON or YAML, a string value can contain the example with escaping 
        where necessary.
        """

        self.examples = examples
        """
        Examples of the media type. Each example SHOULD contain a value in the correct format as specified in the 
        parameter encoding. The examples object is mutually exclusive of the example object. Furthermore, if referencing 
        a schema which contains an example, the examples value SHALL override the example provided by the schema.
        """

        self.content = content
        """
        A map containing the representations for the parameter. The key is the media type and the value describes it. 
        The map MUST only contain one entry.
        """


class Encoding(OObject):
    """A single encoding definition applied to a single schema property."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        content_type: Optional[str] = None,
        headers: Optional[Dict[str, Union[Header, Reference]]] = None,
        style: Optional[str] = None,
        explode: bool = False,
        allow_reserved=False,
    ):
        """
        A single encoding definition applied to a single schema property.

        :param content_type: The Content-Type for encoding a specific property. Default value depends on the property
            type:

            * for string with format being binary – `application/octet-stream`;
            * for other primitive types – `text/plain`;
            * for object - `application/json`;
            * for array – the default is defined based on the inner type.

            The value can be a specific media type (e.g. `application/json`), a wildcard media type (e.g. `image/*`), or
            a comma-separated list of the two types.
        :param headers: A map allowing additional information to be provided as headers, for example
            `Content-Disposition`. `Content-Type` is described separately and SHALL be ignored in this section. This
            property SHALL be ignored if the request body media type is not a multipart.
        :param style: Describes how a specific property value will be serialized depending on its type. See Parameter
        Object for details on the style property. The behavior follows the same values as query parameters, including
         default values. This property SHALL be ignored if the request body media type is not
         `application/x-www-form-urlencoded`.
        :param explode: When this is true, property values of type array or object generate separate parameters for each
            value of the array, or key-value-pair of the map. For other types of properties this property has no effect.
            When style is form, the default value is true. For all other styles, the default value is false. This
            property SHALL be ignored if the request body media type is not application/x-www-form-urlencoded.
        :param allow_reserved: Determines whether the parameter value SHOULD allow reserved characters, as defined by
         RFC3986 ``:/?#[]@!$&'()*+,;=`` to be included without percent-encoding. The default value is false. This
         property SHALL be ignored if the request body media type is not application/x-www-form-urlencoded.
        """
        _assert_type(content_type, (str,), "content_type", self.__class__)
        _assert_type(headers, (dict,), "headers", self.__class__)
        _assert_type(style, (str,), "style", self.__class__)
        _assert_type(explode, (bool,), "explode", self.__class__)
        _assert_type(allow_reserved, (bool,), "allow_reserved", self.__class__)

        if headers:
            for _header_name, header_spec in headers.items():
                assert isinstance(header_spec, (Header, Reference))
        if style:
            assert style in ("matrix", "label", "form", "simple", "spaceDelimited", "pipeDelimited", "deepObject",)
            # TODO - add (where?) check that the style is suitable for this type+location.
        if explode is None:
            explode = bool(style == "form")

        _assert_type(explode, (bool,), "explode", self.__class__)
        _assert_type(allow_reserved, (bool,), "allow_reserved", self.__class__)

        # Assignment and docs
        self.content_type = content_type
        """
        The Content-Type for encoding a specific property. Default value depends on the property type: 
        
        * for `string` with `format` being `binary` – `application/octet-stream`; 
        * for other primitive types – `text/plain`; 
        * for object - `application/json`; 
        * for array – the default is defined based on the inner type. 
        
        The value can be a specific media type (e.g. `application/json`), a wildcard media type (e.g. `image/*`), or a 
        comma-separated list of the two types.
        """

        self.headers = headers
        """
        A map allowing additional information to be provided as headers, for example `Content-Disposition`. Content-Type 
        is described separately and SHALL be ignored in this section. This property SHALL be ignored if the request body 
        media type is not a multipart.
        """

        self.explode = explode
        """
        When this is true, property values of type array or object generate separate parameters for each value of the 
        array, or key-value-pair of the map. For other types of properties this property has no effect. When style is 
        form, the default value is true. For all other styles, the default value is false. This property SHALL be 
        ignored if the request body media type is not application/x-www-form-urlencoded.
        """

        self.allow_reserved = allow_reserved
        """
        Determines whether the parameter value SHOULD allow reserved characters, as defined by RFC3986 
        ``:/?#[]@!$&'()*+,;=`` to be included without percent-encoding. The default value is false. This property SHALL 
        be ignored if the request body media type is not application/x-www-form-urlencoded.
        """


class MediaType(OObject):
    """Each Media Type Object provides schema and examples for the media type identified by its key."""

    def __init__(
        self,
        schema: Optional[Union["Schema", Reference]] = None,
        example: Optional[Any] = None,
        examples: Optional[Dict[str, Union[Example, Reference]]] = None,
        encoding: Optional[Dict[str, Encoding]] = None,
    ):
        """
        Each Media Type Object provides schema and examples for the media type identified by its key.

        :param schema: The schema defining the content of the request, response, or parameter.
        :param example: Example of the media type. The example object SHOULD be in the correct format as specified by
            the media type. The example field is mutually exclusive of the examples field. Furthermore, if referencing a
            schema which contains an example, the example value SHALL override the example provided by the schema.
        :param examples: Examples of the media type. Each example object SHOULD match the media type and specified
            schema if present. The examples field is mutually exclusive of the example field. Furthermore, if
            referencing a schema which contains an example, the examples value SHALL override the example provided by
            the schema.
        :param encoding: A map between a property name and its encoding information. The key, being the property name,
            MUST exist in the schema as a property. The encoding object SHALL only apply to requestBody objects when the
            media type is multipart or application/x-www-form-urlencoded.

        """
        _assert_type(schema, (Schema, Reference), "schema", self.__class__)
        # Note: example is specified as "Any"
        _assert_type(examples, (dict,), "examples", self.__class__)
        _assert_type(encoding, (dict,), "encoding", self.__class__)

        # validations
        assert not (example and examples)
        if examples:
            for ex_name, ex in examples.items():
                if not isinstance(ex, (Example, Reference)):
                    raise AssertionError(
                        "For `{}.examples, values should be an `Example` or a `Reference`. For {} it is a {}".format(
                            self.__class__.__qualname__, ex_name, ex
                        )
                    )
        if encoding:
            for e_name, enc in encoding.items():
                if not isinstance(enc, Encoding):
                    raise AssertionError(
                        "For `{}.encoding, values should be an `Encoding`. For {} it is a {}".format(
                            self.__class__.__qualname__, e_name, type(enc)
                        )
                    )

        # Assignment and Docs
        if not schema:
            warnings.warn(
                "A MediaType without a schema is not shown in Swagger. {}".format(
                    {"encoding": encoding, "example": example, "examples": examples, "schema": schema}
                )
            )
            traceback.print_stack()
        self.schema = schema
        """The schema defining the content of the request, response, or parameter."""

        self.example = example
        """
        Example of the media type. The example object SHOULD be in the correct format as specified by the media type. 
        The example field is mutually exclusive of the examples field. Furthermore, if referencing a schema which 
        contains an example, the example value SHALL override the example provided by the schema.
        """

        self.examples = examples
        """
        Examples of the media type. Each example object SHOULD match the media type and specified schema if present. The 
        examples field is mutually exclusive of the example field. Furthermore, if referencing a schema which contains
        an example, the examples value SHALL override the example provided by the schema.
        """

        self.encoding = encoding
        """
        A map between a property name and its encoding information. The key, being the property name, MUST exist in the 
        schema as a property. The encoding object SHALL only apply to requestBody objects when the media type is 
        multipart or application/x-www-form-urlencoded.
        """


class Schema(OObject):  # pylint: disable=too-many-instance-attributes
    """
    The Schema Object allows the definition of input and output data types. These types can be objects, but also
    primitives and arrays. This object is an extended subset of the `JSON Schema Specification Wright Draft 00
    <https://tools.ietf.org/html/draft-wright-json-schema-validation-00>`_.

    For more information about the properties, see JSON Schema Core and JSON Schema Validation. Unless stated
    otherwise, the property definitions follow the JSON Schema.

    The following properties are taken directly from the JSON Schema definition and follow the same specifications:

    - title
    - multiple_of
    - maximum
    - exclusive_maximum
    - minimum
    - exclusive_minimum
    - max_length
    - min_length
    - pattern
    - max_items
    - min_items
    - unique_items
    - max_properties
    - min_properties
    - required
    - enum

    The following properties are taken from the JSON Schema definition but their definitions were adjusted to the
    OpenAPI Specification.

    - type - Value MUST be a string. Multiple types via an array are not supported.
    - all_of - Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
    - one_of - Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
    - any_of - Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
    - _not - Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
    - items - Value MUST be an object and not an array. Inline or referenced schema MUST be of a Schema Object and
        not a standard JSON Schema. items MUST be present if the type is array.
    - properties - Property definitions MUST be a Schema Object and not a standard JSON Schema (inline or
        referenced).
    - additional_properties - Inline or referenced schema MUST be of a Schema
        Object and not a standard JSON Schema. Consistent with JSON Schema.
    - description - CommonMark syntax MAY be used for rich text representation.
    - _format - See Data Type Formats for further details. While relying on JSON Schema's defined formats, the
        OAS offers a few additional predefined formats.
    - default - The default value represents what would be assumed by the consumer of the input as the value of the
        schema if one is not provided. Unlike JSON Schema, the value MUST conform to the defined type for the Schema
        Object defined at the same level. For example, if type is string, then default can be "foo" but cannot be 1.

    Alternatively, any time a Schema Object can be used, a Reference Object can be used in its place. This allows
    referencing definitions instead of defining them inline.

    Additional properties defined by the JSON Schema specification that are not mentioned here are strictly
    unsupported.
    """

    Integer = None  # type: Schema
    """A pre-defined Integer Schema. Very simple, no properties other than `format` of `int64`."""

    Number = None  # type: Schema
    """A pre-defined Number Schema. Very simple, no properties other than `format` of `double`."""

    String = None  # type: Schema
    """A pre-defined String Schema. Very simple, no properties."""

    Integers = None  # type: Schema
    """A pre-defined Integers Schema. An array of (simple) Integer elements."""

    Numbers = None  # type: Schema
    """A pre-defined Number Schema. An array of (simple) Number elements."""

    Strings = None  # type: Schema
    """A pre-defined String Schema. An array of (simple) String elements."""

    def __init__(  # pylint: disable=too-many-arguments, too-many-locals, too-many-statements
        self,
        _type: str,
        #
        # The following properties are taken directly from the JSON Schema definition and follow the same
        # specifications:
        title: Optional[str] = None,
        multiple_of: Optional[int] = None,
        maximum: Optional[int] = None,
        exclusive_maximum: bool = False,
        minimum: Optional[int] = None,
        exclusive_minimum: bool = False,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        pattern: Optional[str] = None,
        max_items: Optional[int] = None,
        min_items: Optional[int] = None,
        unique_items: bool = False,
        max_properties: Optional[int] = None,
        min_properties: Optional[int] = None,
        required: Optional[List[str]] = None,
        enum: Optional[List[Any]] = None,
        #
        # The following properties are taken from the JSON Schema definition but their definitions were adjusted to the
        # OpenAPI Specification.
        all_of: Optional[Union["Schema", Reference]] = None,
        one_of: Optional[Union["Schema", Reference]] = None,
        any_of: Optional[Union["Schema", Reference]] = None,
        _not: Optional[Union["Schema", Reference]] = None,
        items: Optional[Dict[str, Union["Schema", Reference]]] = None,
        properties: Optional[Union["Schema", Reference]] = None,
        additional_properties: Optional[Union["Schema", Reference]] = None,
        description: Optional[str] = None,
        _format: Optional[str] = None,
        default: Optional[Union[str, int, float, bool]] = None,
        #
        # The OAS extensions.
        nullable: bool = False,
        discriminator: Optional[Discriminator] = None,
        read_only: bool = False,
        write_only: bool = False,
        xml: Optional[XML] = None,
        external_docs: Optional[ExternalDocumentation] = None,
        example: Optional[Any] = None,
        deprecated: bool = False,
        #
        # sanic-openapi3e extension
        x_frozen: bool = False,
    ):
        """
        The Schema Object allows the definition of input and output data types. These types can be objects, but also
        primitives and arrays. This object is an extended subset of the `JSON Schema Specification Wright Draft 00
        <https://tools.ietf.org/html/draft-wright-json-schema-validation-00>`_.

        For more information about the properties, see JSON Schema Core and JSON Schema Validation. Unless stated
        otherwise, the property definitions follow the JSON Schema.

        The following properties are taken directly from the JSON Schema definition and follow the same specifications:

        - title
        - multiple_of
        - maximum
        - exclusive_maximum
        - minimum
        - exclusive_minimum
        - max_length
        - min_length
        - pattern
        - max_items
        - min_items
        - unique_items
        - max_properties
        - min_properties
        - required
        - enum

        The following properties are taken from the JSON Schema definition but their definitions were adjusted to the
        OpenAPI Specification.

        - type - Value MUST be a string. Multiple types via an array are not supported.
        - all_of - Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
        - one_of - Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
        - any_of - Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
        - _not - Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
        - items - Value MUST be an object and not an array. Inline or referenced schema MUST be of a Schema Object and
            not a standard JSON Schema. items MUST be present if the type is array.
        - properties - Property definitions MUST be a Schema Object and not a standard JSON Schema (inline or
            referenced).
        - additional_properties - Inline or referenced schema MUST be of a Schema
            Object and not a standard JSON Schema. Consistent with JSON Schema.
        - description - CommonMark syntax MAY be used for rich text representation.
        - _format - See Data Type Formats for further details. While relying on JSON Schema's defined formats, the
            OAS offers a few additional predefined formats.
        - default - The default value represents what would be assumed by the consumer of the input as the value of the
            schema if one is not provided. Unlike JSON Schema, the value MUST conform to the defined type for the Schema
            Object defined at the same level. For example, if type is string, then default can be "foo" but cannot be 1.

        Alternatively, any time a Schema Object can be used, a Reference Object can be used in its place. This allows
        referencing definitions instead of defining them inline.

        Additional properties defined by the JSON Schema specification that are not mentioned here are strictly
        unsupported.

        :param title: Can be used to decorate a user interface with information about the data produced by this user
            interface.  A title will preferrably [sic] be short.
        :param multiple_of: The value of "multiple_of" MUST be a number, strictly greater than 0. A numeric instance is
            only valid if division by this keyword's value results in an integer.
        :param maximum: The value of "maximum" MUST be a number, representing an upper limit for a numeric instance. If
            the instance is a number, then this keyword validates if "exclusiveMaximum" is true and instance is less
            than the provided value, or else if the instance is less than or exactly equal to the provided value.
        :param exclusive_maximum: The value of "exclusive_maximum" MUST be a boolean, representing whether the limit in
            "maximum" is exclusive or not.  An undefined value is the same as false. If "exclusive_maximum" is true,
            then a numeric instance SHOULD NOT be equal to the value specified in "maximum". If "exclusive_maximum" is
            false (or not specified), then a numeric instance MAY be equal to the value of "maximum".
        :param minimum: The value of "minimum" MUST be a number, representing a lower limit for a numeric instance. If
            the instance is a number, then this keyword validates if "exclusive_minimum" is true and instance is greater
            than the provided value, or else if the instance is greater than or exactly equal to the provided value.
        :param exclusive_minimum: The value of "exclusive_minimum" MUST be a boolean, representing whether the limit in
            "minimum" is exclusive or not.  An undefined value is the same as false. If "exclusive_minimum" is true,
            then a numeric instance SHOULD NOT be equal to the value specified in "minimum". If "exclusive_minimum" is
            false (or not specified), then a numeric instance MAY be equal to the value of "minimum".
        :param max_length: The value of this keyword MUST be a non-negative integer. The value of this keyword MUST be
            an integer.  This integer MUST be greater than, or equal to, 0. A string instance is valid against this
            keyword if its length is less than, or equal to, the value of this keyword. The length of a string instance
            is defined as the number of its characters as defined by RFC 7159 [RFC7159].
        :param min_length: A string instance is valid against this keyword if its length is greater than, or equal to,
            the value of this keyword. The length of a string instance is defined as the number of its characters as
            defined by RFC 7159 [RFC7159]. The value of this keyword MUST be an integer.  This integer MUST be greater
            than, or equal to, 0. "min_length", if absent, may be considered as being present with integer value 0.
        :param pattern: The value of this keyword MUST be a string.  This string SHOULD be a valid regular expression,
            according to the ECMA 262 regular expression dialect. A string instance is considered valid if the regular
            expression matches the instance successfully.  Recall: regular expressions are not implicitly anchored.
            Note: whether or not this is a valid regular expression is not checked by sanic-openapi3e.
        :param max_items: The value of this keyword MUST be an integer.  This integer MUST be greater than, or equal to,
            0. An array instance is valid against "maxItems" if its size is less than, or equal to, the value of this
            keyword.
        :param min_items: The value of this keyword MUST be an integer.  This integer MUST be greater than, or equal to,
            0. An array instance is valid against "minItems" if its size is greater than, or equal to, the value of this
            keyword. If this keyword is not present, it may be considered present with a value of 0.
        :param unique_items: The value of this keyword MUST be a boolean. If this keyword has boolean value false, the
            instance validates successfully.  If it has boolean value true, the instance validates successfully if all
            of its elements are unique. If not present, this keyword may be considered present with boolean value false.
        :param max_properties: he value of this keyword MUST be an integer.  This integer MUST be greater than, or equal
            to, 0. An object instance is valid against "max_properties" if its number of properties is less than, or
            equal to, the value of this keyword.
        :param min_properties: The value of this keyword MUST be an integer.  This integer MUST be greater than, or
            equal to, 0. An object instance is valid against "min_properties" if its number of properties is greater
            than, or equal to, the value of this keyword. If this keyword is not present, it may be considered present
            with a value of 0.
        :param required: The value of this keyword MUST be an array.  This array MUST have at least one element.
            Elements of this array MUST be strings, and MUST be unique. An object instance is valid against this keyword
            if its property set contains all elements in this keyword's array value. Note: sanic-openapi3e implements
            these checks as a Set of str.
        :param enum: The value of this keyword MUST be an array.  This array SHOULD have at least one element.
            Elements in the array SHOULD be unique. Elements in the array MAY be of any type, including null. An
            instance validates successfully against this keyword if its value is equal to one of the elements in this
            keyword's array value. Note: sanic-openapi3e implements these checks as a Set of Any.
        :param _type: Value MUST be a string. Multiple types via an array are not supported.
        :param all_of: Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
        :param one_of: Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
        :param any_of: Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
        :param _not: Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
        :param items: Value MUST be an object and not an array. Inline or referenced schema MUST be of a Schema Object
            and not a standard JSON Schema. items MUST be present if the type is array.
        :param properties: Property definitions MUST be a Schema Object and not a standard JSON Schema (inline or
            referenced).
        :param additional_properties: Value can be boolean or object. Inline or referenced schema MUST be of a Schema
            Object and not a standard JSON Schema. Consistent with JSON Schema, additionalProperties defaults to true.
        :param description: CommonMark syntax MAY be used for rich text representation.
        :param _format:  See `Data Type Formats
            <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#dataTypeFormat>`_ for further
            details. While relying on JSON Schema's defined formats, the OAS offers a few additional predefined formats.
        :param default: The default value represents what would be assumed by the consumer of the input as the value of
            the schema if one is not provided. Unlike JSON Schema, the value MUST conform to the defined type for the
            Schema Object defined at the same level. For example, if type is string, then default can be "foo" but
            cannot be 1.
        :param nullable: Allows sending a null value for the defined schema. Default value is false.
        :param discriminator: Adds support for polymorphism. The discriminator is an object name that is used to
            differentiate between other schemas which may satisfy the payload description. See Composition and
            Inheritance for more details.
        :param read_only: Relevant only for Schema "properties" definitions. Declares the property as "read only". This
            means that it MAY be sent as part of a response but SHOULD NOT be sent as part of the request. If the
            property is marked as read_only being true and is in the required list, the required will take effect on the
            response only. A property MUST NOT be marked as both read_only and writeOnly being true. Default value is
            false.
        :param write_only: Relevant only for Schema "properties" definitions. Declares the property as "write only".
            Therefore, it MAY be sent as part of a request but SHOULD NOT be sent as part of the response. If the
            property is marked as write_only being true and is in the required list, the required will take effect on
            the request only. A property MUST NOT be marked as both read_only and write_only being true. Default value
            is false.
        :param xml: This MAY be used only on properties schemas. It has no effect on root schemas. Adds additional
            metadata to describe the XML representation of this property.
        :param external_docs: Additional external documentation for this schema.
        :param example: A free-form property to include an example of an instance for this schema. To represent examples
            that cannot be naturally represented in JSON or YAML, a string value can be used to contain the example with
            escaping where necessary.
        :param deprecated: Specifies that a schema is deprecated and SHOULD be transitioned out of usage. Default value
            is false.
        :param x_frozen: Specifies that no modifications should be applied to this instance. Default is false.
        """

        # JSON Schema definition
        _assert_type(title, (str,), "title", self.__class__)
        _assert_type(multiple_of, (int,), "multiple_of", self.__class__)
        _assert_type(maximum, (int, float), "maximum", self.__class__)
        _assert_type(exclusive_maximum, (bool,), "exclusive_maximum", self.__class__)
        _assert_type(minimum, (int, float), "minimum", self.__class__)
        _assert_type(exclusive_minimum, (bool,), "exclusive_minimum", self.__class__)
        _assert_type(max_length, (int,), "max_length", self.__class__)
        _assert_type(min_length, (int,), "min_length", self.__class__)
        _assert_type(pattern, (str,), "pattern", self.__class__)
        _assert_type(max_items, (int,), "max_items", self.__class__)
        _assert_type(min_items, (int,), "min_items", self.__class__)
        _assert_type(unique_items, (bool,), "unique_items", self.__class__)
        _assert_type(max_properties, (int,), "max_properties", self.__class__)
        _assert_type(min_properties, (int,), "min_properties", self.__class__)
        _assert_type(required, (list,), "required", self.__class__)
        _assert_type(enum, (list,), "enum", self.__class__)

        # JSON Schema definition but their definitions were adjusted to the OpenAPI Specification.
        _assert_type(_type, (str,), "_type", self.__class__)
        _assert_type(all_of, (Schema, Reference), "all_of", self.__class__)
        _assert_type(one_of, (Schema, Reference), "one_of", self.__class__)
        _assert_type(any_of, (Schema, Reference), "any_of", self.__class__)
        _assert_type(_not, (Schema, Reference), "_not", self.__class__)
        _assert_type(items, (dict,), "items", self.__class__)
        # TODO - finish the definition of "items", it is incomplete. Is it supposed to be a dict of Schemae?
        _assert_type(properties, (Schema, Reference), "properties", self.__class__)
        _assert_type(
            additional_properties, (Schema, Reference), "additional_properties", self.__class__,
        )
        _assert_type(description, (str,), "description", self.__class__)
        _assert_type(_format, (str,), "_format", self.__class__)
        _assert_type(default, (str, int, float, bool), "default", self.__class__)

        # The OAS extensions
        _assert_type(nullable, (bool,), "nullable", self.__class__)
        _assert_type(discriminator, (Discriminator,), "discriminator", self.__class__)
        _assert_type(read_only, (bool,), "read_only", self.__class__)
        _assert_type(write_only, (bool,), "write_only", self.__class__)
        _assert_type(xml, (XML,), "xml", self.__class__)
        _assert_type(external_docs, (ExternalDocumentation,), "external_docs", self.__class__)
        # Note: example is defined to have the type `Any`
        _assert_type(deprecated, (bool,), "deprecated", self.__class__)
        _assert_strictly_greater_than_zero(multiple_of, "multiple_of", self.__class__)
        _assert_strictly_greater_than_zero(max_length, "max_length", self.__class__)
        _assert_strictly_greater_than_zero(min_length, "min_length", self.__class__)
        _assert_strictly_greater_than_zero(max_items, "max_items", self.__class__)
        _assert_strictly_greater_than_zero(min_properties, "min_properties", self.__class__)

        if required is not None:
            assert required, "MUST have at least one element."
            assert set(type(e) for e in required) == {
                type("str")
            }, "For `{}.required`, all elements MUST be strings.".format(self.__class__.__qualname__)
            assert len(set(required)) == len(required), "For `{}.required`, all elements MUST be unique.".format(
                self.__class__.__qualname__
            )
        # if enum:
        #     if not len(enum):
        #         logger.warning(
        #             "`{}.enum` SHOULD have at least one element. {}".format(
        #                 self.__class__.__qualname__, self
        #             )
        #         )
        if _type == "array":
            _assert_required(items, "items", self.__class__, " as `type=array`.")

        #  Assignment and docs
        self.title = title
        """
        Can be used to decorate a user interface with information about the data produced by this user interface.  A 
        title will preferrably [sic] be short.
        """

        self.multiple_of = multiple_of
        """
        The value of "multiple_of" MUST be a number, strictly greater than 0.

        A numeric instance is only valid if division by this keyword's value results in an integer. """

        self.maximum = maximum
        """
        The value of "maximum" MUST be a number, representing an upper limit for a numeric instance.

        If the instance is a number, then this keyword validates if "exclusiveMaximum" is true and instance is less than 
        the provided value, or else if the instance is less than or exactly equal to the provided value.
        """

        self.exclusive_maximum = exclusive_maximum
        """
        The value of "exclusive_maximum" MUST be a boolean, representing whether the limit in "maximum" is exclusive or 
        not.  An undefined value is the same as false.

        If "exclusive_maximum" is true, then a numeric instance SHOULD NOT be equal to the value specified in "maximum".  
        If "exclusive_maximum" is false (or not specified), then a numeric instance MAY be equal to the value of 
        "maximum".
        """

        self.minimum = minimum
        """
        The value of "minimum" MUST be a number, representing a lower limit for a numeric instance.

        If the instance is a number, then this keyword validates if "exclusive_minimum" is true and instance is greater 
        than the provided value, or else if the instance is greater than or exactly equal to the provided value.
        """

        self.exclusive_minimum = exclusive_minimum
        """
        The value of "exclusive_minimum" MUST be a boolean, representing whether the limit in "minimum" is exclusive or 
        not.  An undefined value is the same as false.

        If "exclusive_minimum" is true, then a numeric instance SHOULD NOT be equal to the value specified in "minimum".  
        If "exclusive_minimum" is false (or not specified), then a numeric instance MAY be equal to the value of
        "minimum".
        """

        self.max_length = max_length
        """
        The value of this keyword MUST be a non-negative integer.

        The value of this keyword MUST be an integer.  This integer MUST be greater than, or equal to, 0.

        A string instance is valid against this keyword if its length is less than, or equal to, the value of this 
        keyword.

        The length of a string instance is defined as the number of its characters as defined by RFC 7159 [RFC7159].
        """

        self.min_length = min_length
        """
        A string instance is valid against this keyword if its length is greater than, or equal to, the value of this 
        keyword.

        The length of a string instance is defined as the number of its characters as defined by RFC 7159 [RFC7159].

        The value of this keyword MUST be an integer.  This integer MUST be greater than, or equal to, 0.

        "min_length", if absent, may be considered as being present with integer value 0.
        """

        self.pattern = pattern
        """
        The value of this keyword MUST be a string.  This string SHOULD be a valid regular expression, according to the 
        ECMA 262 regular expression dialect.

        A string instance is considered valid if the regular expression matches the instance successfully.  Recall: 
        regular expressions are not implicitly anchored.
        
        Note: whether or not this is a valid regular expression is not checked by sanic-openapi3e.
        """

        self.max_items = max_items
        """
        The value of this keyword MUST be an integer.  This integer MUST be greater than, or equal to, 0.

        An array instance is valid against "maxItems" if its size is less than, or equal to, the value of this keyword.
        """

        self.min_items = min_items
        """
        The value of this keyword MUST be an integer.  This integer MUST be greater than, or equal to, 0.

        An array instance is valid against "minItems" if its size is greater than, or equal to, the value of this 
        keyword.
        
        If this keyword is not present, it may be considered present with a value of 0.
        """

        self.unique_items = unique_items
        """
        The value of this keyword MUST be a boolean.

        If this keyword has boolean value false, the instance validates successfully.  If it has boolean value true, the 
        instance validates successfully if all of its elements are unique.

        If not present, this keyword may be considered present with boolean value false.
        """

        self.max_properties = max_properties
        """
        The value of this keyword MUST be an integer.  This integer MUST be greater than, or equal to, 0.

        An object instance is valid against "max_properties" if its number of properties is less than, or equal to, the 
        value of this keyword.
        """

        self.min_properties = min_properties
        """
        The value of this keyword MUST be an integer.  This integer MUST be greater than, or equal to, 0.

        An object instance is valid against "min_properties" if its number of properties is greater than, or equal to, 
        the value of this keyword.

        If this keyword is not present, it may be considered present with a value of 0.
        """

        self.required = required
        """
        The value of this keyword MUST be an array.  This array MUST have at least one element.  Elements of this array 
        MUST be strings, and MUST be unique.

        An object instance is valid against this keyword if its property set contains all elements in this keyword's 
        array value.
        """

        self.enum = enum
        """
        The value of this keyword MUST be an array.  This array SHOULD have at least one element.  Elements in the array 
        SHOULD be unique.

        Elements in the array MAY be of any type, including null.

        An instance validates successfully against this keyword if its value is equal to one of the elements in this 
        keyword's array value.
        """

        if _type:
            # TODO - must these be in OTypeFormat.keys()?
            pass
        self._type: Optional[str] = _type
        """Value MUST be a string. Multiple types via an array are not supported."""

        self.all_of = all_of
        """Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema."""

        self.one_of = one_of
        """Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema."""

        self.any_of = any_of
        """Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema."""

        self._not = _not
        """Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema."""

        self.items = items
        """
        Value MUST be an object and not an array. Inline or referenced schema MUST be of a Schema Object and not a 
        standard JSON Schema. items MUST be present if the type is array.
        """
        # TODO - finish the definition of "items", it is incomplete. Is it supposed to be a dict of Schemae?

        self.properties = properties
        """ Property definitions MUST be a Schema Object and not a standard JSON Schema (inline or referenced)."""

        self.additional_properties = additional_properties
        """
        Value can be boolean or object. Inline or referenced schema MUST be of a Schema Object and not a standard JSON 
        Schema.
        """

        self.description = description
        """CommonMark syntax MAY be used for rich text representation."""

        self._format = _format
        """
        See Data Type Formats for further details. While relying on JSON Schema's defined formats, the OAS offers a few 
        additional predefined formats.
        """

        self.default = default
        """
        The default value represents what would be assumed by the consumer of the input as the value of the schema if 
        one is not provided. Unlike JSON Schema, the value MUST conform to the defined type for the Schema Object 
        defined at the same level. For example, if type is string, then default can be "foo" but cannot be 1.
        """
        # TODO - add checks that ensure that the type of default is compatible with the _type

        # The OAS extensions
        self.nullable = nullable
        """Allows sending a null value for the defined schema. Default value is false."""

        self.discriminator = discriminator
        """
        Adds support for polymorphism. The discriminator is an object name that is used to differentiate between other 
        schemas which may satisfy the payload description. See Composition and Inheritance for more details.
        """

        self.read_only = read_only
        """
        Relevant only for Schema "properties" definitions. Declares the property as "read only". This means that it MAY 
        be sent as part of a response but SHOULD NOT be sent as part of the request. If the property is marked as 
        read_only being true and is in the required list, the required will take effect on the response only. A property 
        MUST NOT be marked as both read_only and write_only being true. Default value is false.
        """

        self.write_only = write_only
        """
        Relevant only for Schema "properties" definitions. Declares the property as "write only". Therefore, it MAY be 
        sent as part of a request but SHOULD NOT be sent as part of the response. If the property is marked as 
        write_only being true and is in the required list, the required will take effect on the request only. A property
        MUST NOT be marked as both read_only and write_only being true. Default value is false.
        """

        self.xml = xml
        """
        This MAY be used only on properties schemas. It has no effect on root schemas. Adds additional metadata to 
        describe the XML representation of this property.
        """

        self.external_docs = external_docs
        """Additional external documentation for this schema."""

        self.example = example
        """
        A free-form property to include an example of an instance for this schema. To represent examples that cannot be 
        naturally represented in JSON or YAML, a string value can be used to contain the example with escaping where 
        necessary.
        """

        self.deprecated = deprecated
        """ Specifies that a schema is deprecated and SHOULD be transitioned out of usage. Default value is false."""

        self.x_frozen = x_frozen
        """Specifies that no modifications should be applied to this instance. Default is false."""

        if _type == "array" and not items:
            raise AssertionError(
                "For `{}`, items MUST be present if the type is array.".format(self.__class__.__qualname__)
            )
        if _format:
            # TODO - must these be in OTypeFormat[_type]?
            pass

        if read_only and write_only:
            raise AssertionError(
                "For `{}`, A property; MUST NOT be marked as both read_only and write_only being true.".format(
                    self.__class__.__qualname__
                )
            )

    def add_enum(self, enum: List):
        assert not self.x_frozen, "Please do not modify a frozen Schema: {}".format(self)
        enum0_type: str = self.get_enum_type(enum)

        if self._type:
            if self._type == "array":
                if self.items:
                    assert self.items.get("type") == enum0_type, (
                        self.items,
                        enum0_type,
                    )
                else:
                    self.items = {"items": Schema(_type=enum0_type)}
            else:
                assert self._type == enum0_type, (self._type, enum0_type)
        else:
            self._type = enum0_type
        self.enum = enum

    def clone(self) -> "Schema":
        _clone = copy.deepcopy(self)
        _clone.x_frozen = False
        return _clone

    @classmethod
    def get_enum_type(cls, enum: List) -> str:
        _assert_type(enum, (list,), "enum", cls)
        assert enum
        enum_types = {type(e) for e in enum}
        if len(enum_types) != 1:
            raise AssertionError(
                "For `{}`, all values of the enum/choices must be of the same type, but `{}` were seen".format(
                    cls.__qualname__, enum_types
                )
            )

        # At definition, the Schema.String is set to `None`, but below (and before code gets to use it) it is set to
        # `Schema(_type="string")`. This is for python3.6 reasons. Thus, mypy needs to be silenced for the next line and
        # the line just before the return.
        schema_string_type = Schema.String._type  # pylint: disable=protected-access
        assert schema_string_type
        _enum_type: str = schema_string_type
        enum0_schema: Optional[Schema] = {int: Schema.Integer, str: Schema.String, float: Schema.Number,}.get(
            type(enum[0])
        )
        if enum0_schema:
            enum0_schema_type = enum0_schema._type  # pylint: disable=protected-access
            assert enum0_schema_type
            _enum_type = enum0_schema_type

        return _enum_type


Schema.Integer = Schema(_type="integer", x_frozen=True)
Schema.Number = Schema(_type="number", _format="double", x_frozen=True)
Schema.String = Schema(_type="string", x_frozen=True)
Schema.Integers = Schema(_type="array", items=Schema.Integer.serialize(), x_frozen=True)
Schema.Numbers = Schema(_type="array", items=Schema.Number.serialize(), x_frozen=True)
Schema.Strings = Schema(_type="array", items=Schema.String.serialize(), x_frozen=True)


class Parameter(OObject):  # pylint: disable=too-many-instance-attributes
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
    """

    def __init__(  # pylint: disable=too-many-arguments, too-many-locals, too-many-statements
        self,
        name: str,
        _in: str,
        description: Optional[str] = None,
        required: Optional[bool] = None,
        deprecated: Optional[bool] = None,
        allow_empty_value: Optional[bool] = None,
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

        _assert_type(name, (str,), "name", self.__class__)
        _assert_type(_in, (str,), "_in", self.__class__)
        _assert_type(description, (str,), "description", self.__class__)
        _assert_type(required, (bool,), "required", self.__class__)
        _assert_type(deprecated, (bool,), "deprecated", self.__class__)
        _assert_type(allow_empty_value, (bool,), "allow_empty_value", self.__class__)
        _assert_type(style, (str,), "style", self.__class__)
        _assert_type(explode, (bool,), "explode", self.__class__)
        _assert_type(allow_reserved, (bool,), "allow_reserved", self.__class__)
        _assert_type(schema, (Schema, Reference), "schema", self.__class__)
        # Note: examples is specified to be "Any"
        _assert_type(examples, (dict,), "examples", self.__class__)
        _assert_type(content, (MediaType,), "content", self.__class__)

        # validations
        _assert_required(name, "name", self.__class__)
        if _in == "requestBody":
            raise AssertionError(
                """For `{}`, the OpenAPI spec requires a `@doc.requestBody` and not a `@doc.parameter`""".format(name)
            )
        if _in not in ("query", "header", "path", "cookie"):
            raise AssertionError(
                """`{}._in` must be one of ("query", "header", "path" or "cookie"), not `{}`""".format(
                    self.__class__.__qualname__, _in
                )
            )
        if _in == "path":
            assert required is True
        else:
            required = required or False

        assert not (example and examples)
        if examples:
            for ex_name, ex in examples.items():
                if not isinstance(ex, (Example, Reference)):
                    raise AssertionError(
                        "For `{}.examples`, values must be either an `Example` or a `Reference`. {} is a {}".format(
                            self.__class__.__qualname__, ex_name, type(ex)
                        )
                    )
        if content:
            if len(content) != 1:
                raise AssertionError("For `{}.content` MUST only contain one entry".format(self.__class__.__qualname__))
            for c_name, _media_type in content.items():
                if not isinstance(c_name, MediaType):
                    raise AssertionError(
                        "For `{}.content`, the value must be a `MediaType`".format(self.__class__.__qualname__)
                    )

        # Assignments and docs
        self.name = name
        """
        REQUIRED. The name of the parameter. Parameter names are case sensitive. If in is "path", the name field MUST 
        correspond to the associated path segment from the path field in the Paths Object. See Path Templating for 
        further information. If in is "header" and the name field is "Accept", "Content-Type" or "Authorization", the 
        parameter definition SHALL be ignored. For all other cases, the name corresponds to the parameter name used by 
        the in property.
        """

        self.description = description
        """
        A brief description of the parameter. This could contain examples of use. CommonMark syntax MAY be used for rich 
        text representation.
        """

        self._in = _in
        """REQUIRED. The location of the parameter. Possible values are "query", "header", "path" or "cookie"."""

        self.description = description
        """
        A brief description of the parameter. This could contain examples of use. CommonMark syntax MAY be used for rich 
        text representation.
        """
        self.required: bool = required
        """
        Determines whether this parameter is mandatory. If the parameter _in is "path", this property is REQUIRED 
        and its value MUST be true. Otherwise, the property MAY be included and its default value is false.
        """

        self.deprecated = deprecated or False
        """Specifies that a parameter is deprecated and SHOULD be transitioned out of usage. Default value is false."""

        self.allow_empty_value = allow_empty_value
        """
        Sets the ability to pass empty-valued parameters. This is valid only for query parameters and allows sending a 
        parameter with an empty value. Default value is false. If style is used, and if behavior is n/a (cannot be 
        serialized), the value of allowEmptyValue SHALL be ignored. Use of this property is NOT RECOMMENDED, as it is 
        likely to be removed in a later revision.
        """

        self.style = style
        """
        Describes how the parameter value will be serialized depending on the type of the parameter value. Default 
        values (based on value of ``_in``): 
        
        * for query - form; 
        * for path - simple; 
        * for header - simple; 
        * for cookie - form.
        """
        # ^^ TODO - set these defaults?
        self.explode = explode
        """
        When this is true, parameter values of type array or object generate separate parameters for each value of the 
        array or key-value pair of the map. For other types of parameters this property has no effect. When style is 
        form, the default value is true. For all other styles, the default value is false.
        """
        # ^^ TODO - set these defaults?

        self.allow_reserved = allow_reserved
        """
        Determines whether the parameter value SHOULD allow reserved characters, as defined by RFC3986 
        ``:/?#[]@!$&'()*+,;=`` to be included without percent-encoding. This property only applies to parameters with an 
        ``_in`` value of query. The default value is false.
        """

        self.schema = schema
        """The schema defining the type used for the parameter."""

        self.example = example
        """
        Example of the media type. The example SHOULD match the specified schema and encoding properties if present. The 
        example field is mutually exclusive of the examples field. Furthermore, if referencing a schema which contains 
        an example, the example value SHALL override the example provided by the schema. To represent examples of media 
        types that cannot naturally be represented in JSON or YAML, a string value can contain the example with escaping 
        where necessary.
        """

        self.examples = examples
        """
        Examples of the media type. Each example SHOULD contain a value in the correct format as specified in the 
        parameter encoding. The examples object is mutually exclusive of the example object. Furthermore, if referencing 
        a schema which contains an example, the examples value SHALL override the example provided by the schema.
        """

        self.content = content
        """
        A map containing the representations for the parameter. The key is the media type and the value describes it. 
        The map MUST only contain one entry.
        """

    def __add__(self, other):
        assert isinstance(other, Parameter)
        _d = {}
        for key, value in self.__dict__.items():  # pylint: disable=too-many-nested-blocks
            if value:
                _d[key] = value
                other_value = getattr(other, key)
                if other_value and value != other_value:
                    # TODO - this should be done recursively. Move __add__ up to OObject?
                    # eg: schema:
                    # Schema{"type": "integer"} != Schema{"format": "int32", "minimum": 4, "type": "integer"}
                    if isinstance(other_value, Reference):
                        # Simple replace.
                        # TODO - check that the ref actually exists in the components.
                        # TODO - check that the ref is compatible
                        _d[key] = other_value

                    elif isinstance(value, OObject):
                        v_d = {}
                        for v_k, v_v in value.__dict__.items():
                            if v_v:
                                v_d[v_k] = v_v
                                v_ov = getattr(other_value, v_k)
                                if v_ov:
                                    assert v_v == v_ov, "{}.{}: {} != {}".format(key, v_k, v_v, v_ov)

                            else:
                                v_d[v_k] = getattr(other_value, v_k)
                        # TODO: this use of globals is _OK_ but it would be nice to not need it.
                        _d[key] = globals()[value.__class__.__qualname__](**v_d)

                    else:
                        raise AssertionError("{}: {} != {}".format(key, getattr(self, key), other_value))

            else:
                _d[key] = getattr(other, key)
        return Parameter(**_d)


class Link(OObject):
    """
    The Link object represents a possible design-time link for a response. The presence of a link does not guarantee
    the caller's ability to successfully invoke it, rather it provides a known relationship and traversal mechanism
    between responses and other operations.

    Unlike dynamic links (i.e. links provided in the response payload), the OAS linking mechanism does not require
    link information in the runtime response.

    For computing links, and providing instructions to execute them, a runtime expression is used for accessing
    values in an operation and using them as parameters while invoking the linked operation.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        operation_ref: Optional[str] = None,
        operation_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        request_body: Optional[Any] = None,
        description: Optional[str] = None,
        server: Optional[Server] = None,
    ):
        """
        The Link object represents a possible design-time link for a response. The presence of a link does not guarantee
        the caller's ability to successfully invoke it, rather it provides a known relationship and traversal mechanism
        between responses and other operations.

        Unlike dynamic links (i.e. links provided in the response payload), the OAS linking mechanism does not require
        link information in the runtime response.

        For computing links, and providing instructions to execute them, a runtime expression is used for accessing
        values in an operation and using them as parameters while invoking the linked operation.

        :param operation_ref: A relative or absolute reference to an OAS operation. This field is mutually exclusive of
            the operationId field, and MUST point to an Operation Object. Relative operationRef values MAY be used to
            locate an existing Operation Object in the OpenAPI definition.
        :param operation_id: The name of an existing, resolvable OAS operation, as defined with a unique operationId.
            This field is mutually exclusive of the operationRef field.
        :param parameters: A map representing parameters to pass to an operation as specified with operationId or
            identified via operationRef. The key is the parameter name to be used, whereas the value can be a constant
            or an expression to be evaluated and passed to the linked operation. The parameter name can be qualified
            using the parameter _in [{in}.]{name} for operations that use the same parameter name in different
            locations (e.g. path.id).
        :param request_body: A literal value or {expression} to use as a request body when calling the target operation.
        :param description: A description of the link. CommonMark syntax MAY be used for rich text representation.
        :param server: A server object to be used by the target operation.

        """
        # TODO docstrings
        _assert_type(operation_ref, (str,), "operation_ref", self.__class__)
        _assert_type(operation_id, (str,), "operation_id", self.__class__)
        _assert_type(parameters, (dict,), "parameters", self.__class__)
        # Note: request_body can be Any
        _assert_type(description, (str,), "description", self.__class__)
        _assert_type(server, (Server,), "server", self.__class__)

        assert not (operation_ref and operation_id)

        self.operation_ref = operation_ref
        """
        A relative or absolute reference to an OAS operation. This field is mutually exclusive of the operationId field,
        and MUST point to an Operation Object. Relative operationRef values MAY be used to locate an existing Operation 
        Object in the OpenAPI definition.
        """

        self.operation_id = operation_id
        """
        The name of an existing, resolvable OAS operation, as defined with a unique operationId. This field is mutually 
        exclusive of the operationRef field.
        """

        self.parameters = parameters
        """
        A map representing parameters to pass to an operation as specified with operationId or identified via 
        operationRef. The key is the parameter name to be used, whereas the value can be a constant or an expression to 
        be evaluated and passed to the linked operation. The parameter name can be qualified using the parameter 
        _in [{_in}.]{name} for operations that use the same parameter name in different locations (e.g. 
        path.id).
        """

        self.request_body = request_body
        """ A literal value or {expression} to use as a request body when calling the target operation."""

        self.description = description

        self.server = server
        """A server object to be used by the target operation."""


class Response(OObject):
    """
    Describes a single response from an API Operation, including design-time, static links to operations based on the
    response.
    """

    # This is reset from None to a Response directly after the class definition.
    DEFAULT_SUCCESS = None  # type: Response
    BAD_REQUEST = None  # type: Response
    UNAUTHORIZED = None  # type: Response
    FORBIDDEN = None  # type: Response
    NOT_FOUND = None  # type: Response
    METHOD_NOT_ALLOWED = None  # type: Response
    GONE = None  # type: Response
    INTERNAL_SERVER_ERROR = None  # type: Response

    def __init__(
        self,
        description: str,
        headers: Optional[Dict[str, Union[Header, Reference]]] = None,
        content: Optional[Dict[str, MediaType]] = None,
        links: Optional[Dict[str, Union[Link, Reference]]] = None,
    ):
        """
        Describes a single response from an API Operation, including design-time, static links to operations based on
        the response.

        :param description: REQUIRED. A short description of the response. CommonMark syntax MAY be used for rich text
            representation.
        :param headers: Maps a header name to its definition. RFC7230 states header names are case insensitive. If a
            response header is defined with the name "Content-Type", it SHALL be ignored.
        :param content: A map containing descriptions of potential response payloads. The key is a media type or media
            type range and the value describes it. For responses that match multiple keys, only the most specific key is
            applicable. e.g. ``text/plain`` overrides ``text/*``.
        :param links: A map of operations links that can be followed from the response. The key of the map is a short
        """
        _assert_type(description, (str,), "description", self.__class__)
        _assert_type(headers, (dict,), "headers", self.__class__)
        _assert_type(content, (dict,), "content", self.__class__)
        _assert_type(links, (dict,), "links", self.__class__)

        _assert_required(description, "description", self.__class__)
        if headers:
            for _header_name, header_spec in headers.items():
                assert isinstance(header_spec, (Header, Reference))
        if content:
            for _media_type_name, media_type_spec in content.items():
                assert isinstance(media_type_spec, MediaType)
        if links:
            for _link_name, link_spec in links.items():
                assert isinstance(link_spec, (Link, Reference))

        # Assignment and docs
        self.description = description
        """
        REQUIRED. A short description of the response. CommonMark syntax MAY be used for rich text representation.
        """

        self.headers = headers
        """
        Maps a header name to its definition. RFC7230 states header names are case insensitive. If a response header is 
        defined with the name "Content-Type", it SHALL be ignored.
        """

        self.content = content
        """
        A map containing descriptions of potential response payloads. The key is a media type or media type range and 
        the value describes it. For responses that match multiple keys, only the most specific key is applicable. e.g. 
        ``text/plain`` overrides ``text/*``.
        """

        self.links = links
        """
        A map of operations links that can be followed from the response. The key of the map is a short name for the 
        link, following the naming constraints of the names for Component Objects.
        """


Response.DEFAULT_SUCCESS = Response(description="OK")
Response.BAD_REQUEST = Response(description="Bad Request")
Response.UNAUTHORIZED = Response(description="Unauthorized")
Response.FORBIDDEN = Response(description="Forbidden")
Response.NOT_FOUND = Response(description="Not Found")
Response.METHOD_NOT_ALLOWED = Response(description="Method Not Allowed")
Response.GONE = Response(description="Gone")
Response.INTERNAL_SERVER_ERROR = Response(description="Internal Server Error")


class RequestBody(OObject):
    """Describes a single request body."""

    def __init__(
        self, content: Dict[str, MediaType], description: Optional[str] = None, required: bool = False,
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
        # TODO - types
        _assert_required(content, "content", self.__class__)
        _assert_type(content, (dict,), "content", self.__class__)

        # Assignment and docs
        self.description = description
        """
        A brief description of the request body. This could contain examples of use. CommonMark syntax MAY be used for 
        rich text representation.
        """

        self.content = content
        """
        REQUIRED. The content of the request body. The key is a media type or media type range and the value describes 
        it. For requests that match multiple keys, only the most specific key is applicable. e.g. ``text/plain`` 
        overrides ``text/*``
        """

        self.required = required
        """Determines if the request body is required in the request. Defaults to false."""


class OAuthFlow(OObject):
    """
    Configuration details for a supported OAuth Flow.

    Note: there is an ``Applies To`` column in the spec and its full meaning is not clear. Be advised that you may
    need to check again how this applies to you. See `OAuth Flow Object
    <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#oauth-flow-object>`_.
    Specifically unclear (and inconsistent with some other sections of the docs) is whether the "REQUIRED"
    terminology only applies to the value in the ``Applies To`` column. For this reason, there is no validation that
    (possibly) REQUIRED values are presented.
    """

    def __init__(
        self, authorization_url: str, token_url: str, scopes: Dict[str, str], refresh_url: Optional[str] = None,
    ):
        """
        Configuration details for a supported OAuth Flow.

        Note: there is an ``Applies To`` column in the spec and its full meaning is not clear. Be advised that you may
        need to check again how this applies to you. See `OAuth Flow Object
        <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#oauth-flow-object>`_.
        Specifically unclear (and inconsistent with some other sections of the docs) is whether the "REQUIRED"
        terminology only applies to the value in the ``Applies To`` column. For this reason, there is no validation that
        (possibly) REQUIRED values are presented.

        :param authorization_url: REQUIRED (but not checked). The authorization URL to be used for this flow. This MUST
            be in the form of a URL.
        :param token_url: REQUIRED (but not checked). The token URL to be used for this flow. This MUST be in the form
            of a URL.
        :param refresh_url: The URL to be used for obtaining refresh tokens. This MUST be in the form of a URL.
        :param scopes: REQUIRED (but not checked). The available scopes for the OAuth2 security scheme. A map between
            the scope name and a short description for it.
        """

        # TODO - see notes above re: validation

        # Assignment and docs
        self.authorization_url = authorization_url
        """
        REQUIRED (but not checked). The authorization URL to be used for this flow. This MUST be in the form of a URL.
        """

        self.token_url = token_url
        """REQUIRED (but not checked). The token URL to be used for this flow. This MUST be in the form of a URL."""

        self.refresh_url = refresh_url
        """The URL to be used for obtaining refresh tokens. This MUST be in the form of a URL."""

        self.scopes = scopes
        """
        REQUIRED (but not checked). The available scopes for the OAuth2 security scheme. A map between the scope name 
        and a short description for it.
        """


class OAuthFlows(OObject):
    """Allows configuration of the supported OAuth Flows."""

    def __init__(
        self,
        implicit: Optional[OAuthFlow] = None,
        password: Optional[OAuthFlow] = None,
        client_credentials: Optional[OAuthFlow] = None,
        authorization_code: Optional[OAuthFlow] = None,
    ):
        """
        Allows configuration of the supported OAuth Flows.

        :param implicit: Configuration for the OAuth Implicit flow.
        :param password: Configuration for the OAuth Resource Owner Password flow.
        :param client_credentials: Configuration for the OAuth Client Credentials flow. Previously called application in
            OpenAPI 2.0.
        :param authorization_code: Configuration for the OAuth Authorization Code flow. Previously called accessCode in
            OpenAPI 2.0.
        """
        # TODO - types
        # No specific validation

        # Assignment and docs
        self.implicit = implicit
        """Configuration for the OAuth Implicit flow"""

        self.password = password
        """Configuration for the OAuth Resource Owner Password flow"""

        self.client_credentials = client_credentials
        """Configuration for the OAuth Client Credentials flow. Previously called application in OpenAPI 2.0."""

        self.authorization_code = authorization_code
        """Configuration for the OAuth Authorization Code flow. Previously called accessCode in OpenAPI 2.0."""


class SecurityScheme(OObject):  # pylint: disable=too-many-instance-attributes
    """
    Defines a security scheme that can be used by the operations. Supported schemes are HTTP authentication, an API
    key (either as a header, a cookie parameter or as a query parameter), OAuth2's common flows (implicit, password,
    application and access code) as defined in RFC6749, and OpenID Connect Discovery.

    Note: there is an ``Applies To`` column in the spec and its full meaning is not clear. Be advised that you may
    need to check again how this applies to you. See `Security Scheme Object
    <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#security-scheme-object>`_.
    Specifically unclear (and inconsistent with some other sections of the docs) is whether the "REQUIRED"
    terminology only applies to the ``_type`` value in the ``Applies To`` column. For this reason, there is not
    validation that (possibly) REQUIRED values are presented.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        _type: str,
        name: str,
        _in: str,
        scheme: str,
        flows: Optional[OAuthFlows] = None,
        openid_connect_url: Optional[str] = None,
        description: Optional[str] = None,
        bearer_format=None,
    ):
        """
        Defines a security scheme that can be used by the operations. Supported schemes are HTTP authentication, an API
        key (either as a header, a cookie parameter or as a query parameter), OAuth2's common flows (implicit, password,
        application and access code) as defined in RFC6749, and OpenID Connect Discovery.

        Note: there is an ``Applies To`` column in the spec and its full meaning is not clear. Be advised that you may
        need to check again how this applies to you. See `Security Scheme Object
        <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#security-scheme-object>`_.
        Specifically unclear (and inconsistent with some other sections of the docs) is whether the "REQUIRED"
        terminology only applies to the ``_type`` value in the ``Applies To`` column. For this reason, there is not
        validation that (possibly) REQUIRED values are presented.

        :param _type: REQUIRED. The type of the security scheme. Valid values are "apiKey", "http", "oauth2",
            "openIdConnect".
        :param description: A short description for security scheme. CommonMark syntax MAY be used for rich text
            representation.
        :param name: REQUIRED (but not checked). The name of the header, query or cookie parameter to be used.
        :param _in: REQUIRED (but not checked). The location of the API key. Valid values are "query", "header" or
            "cookie".
        :param scheme: REQUIRED (but not checked). The name of the HTTP Authorization scheme to be used in the
            Authorization header as defined in RFC7235.
        :param bearer_format: A hint to the client to identify how the bearer token is formatted. Bearer tokens are
            usually generated by an authorization server, so this information is primarily for documentation purposes.
        :param flows: REQUIRED when `_type` is `oauth2`. An object containing configuration information for the flow
            types supported.
        :param openid_connect_url: REQUIRED when `_type` is `openIdConnect`. OpenId Connect URL to discover OAuth2
            configuration values. This MUST be in the form of a URL.
        """
        # TODO - types

        assert _type in {"apiKey", "http", "oauth2", "openIdConnect"}
        if _in:
            assert _in in {"query", "header", "cookie"}, _in

        self._type = _type
        """
        REQUIRED (but not checked). The type of the security scheme. Valid values are "apiKey", "http", "oauth2", 
        "openIdConnect"."""

        self.description = description
        """A short description for security scheme. CommonMark syntax MAY be used for rich text representation."""

        self.name = name
        """REQUIRED (but not checked). The name of the header, query or cookie parameter to be used."""

        self._in = _in
        """REQUIRED (but not checked). The location of the API key. Valid values are "query", "header" or "cookie"."""

        self.scheme = scheme
        """
        REQUIRED (but not checked). The name of the HTTP Authorization scheme to be used in the Authorization header as 
        defined in RFC7235.
        """

        self.bearer_format = bearer_format
        """
        A hint to the client to identify how the bearer token is formatted. Bearer tokens are usually generated by an 
        authorization server, so this information is primarily for documentation purposes.
        """

        self.flows = flows
        """
        REQUIRED when _type is oauth2. An object containing configuration information for the flow types supported.
        """

        self.openid_connect_url = openid_connect_url
        """
        REQUIRED when _type is openIdConnect. OpenId Connect URL to discover OAuth2 configuration values. This MUST be 
        in the form of a URL.
        """


class Callback(OObject):
    """
    A map of possible out-of band callbacks related to the parent operation. Each value in the map is a PathItem
    Object that describes a set of requests that may be initiated by the API provider and the expected responses.
    The key value used to identify the callback object is an expression, evaluated at runtime, that identifies a URL
    to use for the callback operation.

    Note: there is a _lot_ more documentation available in the spec for callbacks. `See
    <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#callback-object>`_ .
    """

    # TODO - may need to reimplement the ``serialise`` and ``schema``.
    def __init__(self, callbacks: Dict[Any, "PathItem"]):
        """
        A map of possible out-of band callbacks related to the parent operation. Each value in the map is a PathItem
        Object that describes a set of requests that may be initiated by the API provider and the expected responses.
        The key value used to identify the callback object is an expression, evaluated at runtime, that identifies a URL
        to use for the callback operation.

        Note: there is a _lot_ more documentation available in the spec for callbacks. `See
        <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#callback-object>`_ .

        :param callbacks: A mapping of Any to a PathItem used to define a callback request and expected responses.
        A `complete example
        <https://github.com/OAI/OpenAPI-Specification/blob/master/examples/v3.0/callback-example.yaml>`_ is available.

        """
        # TODO - types
        # TODO - validations
        self.__dict__ = callbacks

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __getitem__(self, key):
        return self.__dict__[key]

    def __repr__(self):
        return repr(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        del self.__dict__[key]

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def has_key(self, k):
        return k in self.__dict__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, *args):
        return self.__dict__.pop(*args)

    def __cmp__(self, other):
        return self.__dict__.__cmp__(other)

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)


class Responses(OObject):
    """
    A container for the expected responses of an operation. The container maps a HTTP response code to the expected
    response. The documentation is not necessarily expected to cover all possible HTTP response codes because they
    may not be known in advance. However, documentation is expected to cover a successful operation response and any
    known errors.

    The default MAY be used as a default response object for all HTTP codes that are not covered individually by the
    specification.

    The Responses Object MUST contain at least one response code, and it SHOULD be the response for a successful
    operation call.

    "default" key in responses
    --------------------------
    The documentation of responses other than the ones declared for specific HTTP response codes. Use this field to
    cover undeclared responses. A Reference Object can link to a response that the OpenAPI Object's
    components/responses section defines.

    HTTP status code keys in responses
    ----------------------------------
    Any HTTP status code can be used as the property name, but only one property per code, to describe the expected
    response for that HTTP status code. A Reference Object can link to a response that is defined in the OpenAPI
    Object's components/responses section. This field MUST be enclosed in quotation marks (for example, "200") for
    compatibility between JSON and YAML. To define a range of response codes, this field MAY contain the uppercase
    wildcard character X. For example, 2XX represents all response codes between [200-299]. Only the following range
    definitions are allowed: 1XX, 2XX, 3XX, 4XX, and 5XX. If a response is defined using an explicit code, the
    explicit code definition takes precedence over the range definition for that code.
    """

    DEFAULT_RESPONSES = {
        "200": Response.DEFAULT_SUCCESS,
        "400": Response.BAD_REQUEST,
        "401": Response.UNAUTHORIZED,
        "403": Response.FORBIDDEN,
        "404": Response.NOT_FOUND,
        "405": Response.METHOD_NOT_ALLOWED,
        "410": Response.GONE,
        "500": Response.INTERNAL_SERVER_ERROR,
    }

    # TODO - may need to reimplement the ``serialise`` and ``schema``.
    def __init__(self, responses: Optional[Dict[str, Union[Response, Reference]]] = None):
        """
        A container for the expected responses of an operation. The container maps a HTTP response code to the expected
        response. The documentation is not necessarily expected to cover all possible HTTP response codes because they
        may not be known in advance. However, documentation is expected to cover a successful operation response and any
        known errors.

        The default MAY be used as a default response object for all HTTP codes that are not covered individually by the
        specification.

        The Responses Object MUST contain at least one response code, and it SHOULD be the response for a successful
        operation call.

        "default" key in responses
        --------------------------
        The documentation of responses other than the ones declared for specific HTTP response codes. Use this field to
        cover undeclared responses. A Reference Object can link to a response that the OpenAPI Object's
        components/responses section defines.

        HTTP status code keys in responses
        ----------------------------------
        Any HTTP status code can be used as the property name, but only one property per code, to describe the expected
        response for that HTTP status code. A Reference Object can link to a response that is defined in the OpenAPI
        Object's components/responses section. This field MUST be enclosed in quotation marks (for example, "200") for
        compatibility between JSON and YAML. To define a range of response codes, this field MAY contain the uppercase
        wildcard character X. For example, 2XX represents all response codes between [200-299]. Only the following range
        definitions are allowed: 1XX, 2XX, 3XX, 4XX, and 5XX. If a response is defined using an explicit code, the
        explicit code definition takes precedence over the range definition for that code.

        :param responses: A mapping of response code (as str) to a Response.
        """
        # TODO - types
        # TODO - validations
        _init_responses: Dict[str, Union[Response, Reference]] = {
            key: Reference("#/components/responses/{}".format(key)) for key in Responses.DEFAULT_RESPONSES
        }
        if responses:
            for status_code, response in responses.items():
                _init_responses[str(status_code)] = response
        self.__dict__ = _init_responses

    @property
    def as_dict(self) -> Dict[str, Union[Response, Reference]]:
        return self.__dict__

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __getitem__(self, key):
        return self.__dict__[key]

    def __repr__(self):
        return repr(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        del self.__dict__[key]

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def has_key(self, k):
        return k in self.__dict__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, *args):
        return self.__dict__.pop(*args)

    # def __cmp__(self, other):
    #     return self.__dict__.__cmp__(other)

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)


class Components(OObject):  # pylint: disable=too-many-instance-attributes
    """
    Holds a set of reusable objects for different aspects of the OAS. All objects defined within the components
    object will have no effect on the API unless they are explicitly referenced from properties outside the
    components object.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        schemas: Optional[Dict[str, Union[Schema, Reference]]] = None,
        responses: Optional[Dict[str, Union[Response, Reference]]] = None,
        parameters: Optional[Dict[str, Union[Parameter, Reference]]] = None,
        examples: Optional[Dict[str, Union[Example, Reference]]] = None,
        request_bodies: Optional[Dict[str, Union[RequestBody, Reference]]] = None,
        headers: Optional[Dict[str, Union[Header, Reference]]] = None,
        security_schemes: Optional[Dict[str, Union[SecurityScheme, Reference]]] = None,
        links: Optional[Dict[str, Union[Link, Reference]]] = None,
        callbacks: Optional[Dict[str, Union[Callback, Reference]]] = None,
    ):
        """
        Holds a set of reusable objects for different aspects of the OAS. All objects defined within the components
        object will have no effect on the API unless they are explicitly referenced from properties outside the
        components object.

        :param schemas: An object to hold reusable Schema Objects.
        :param responses: An object to hold reusable Response Objects.
        :param parameters: An object to hold reusable Parameter Objects.
        :param examples: An object to hold reusable Example Objects.
        :param request_bodies: An object to hold reusable Request Body Objects.
        :param headers: An object to hold reusable Header Objects.
        :param security_schemes: An object to hold reusable Security Scheme Objects.
        :param links: An object to hold reusable Link Objects.
        :param callbacks: An object to hold reusable Callback Objects.

        """
        _assert_type(schemas, (dict,), "schemas", self.__class__)
        _assert_type(responses, (dict,), "responses", self.__class__)
        _assert_type(parameters, (dict,), "parameters", self.__class__)
        _assert_type(examples, (dict,), "examples", self.__class__)
        _assert_type(request_bodies, (dict,), "request_bodies", self.__class__)
        _assert_type(headers, (dict,), "headers", self.__class__)
        _assert_type(security_schemes, (dict,), "security_schemes", self.__class__)
        _assert_type(links, (dict,), "links", self.__class__)
        _assert_type(callbacks, (dict,), "callbacks", self.__class__)

        # TODO - value type checks

        # assignment and docs
        self.schemas = schemas
        """An object to hold reusable Schema Objects."""

        self.responses = responses or Responses.DEFAULT_RESPONSES
        """An object to hold reusable Response Objects."""

        self.parameters = parameters
        """An object to hold reusable Parameter Objects."""

        self.examples = examples
        """An object to hold reusable Example Objects."""

        self.request_bodies = request_bodies
        """An object to hold reusable Request Body Objects."""

        self.headers = headers
        """An object to hold reusable Header Objects."""

        self.security_schemes = security_schemes
        """An object to hold reusable Security Scheme Objects."""

        self.links = links
        """An object to hold reusable Link Objects."""

        self.callbacks = callbacks
        """An object to hold reusable Callback Objects."""


class SecurityRequirement(OObject):  # pylint: disable=missing-function-docstring
    """
    Lists the required security schemes to execute this operation. The name used for each property MUST correspond to a
    security scheme declared in the Security Schemes under the Components Object.

    Security Requirement Objects that contain multiple schemes require that all schemes MUST be satisfied for a
    request to be authorized. This enables support for scenarios where multiple query parameters or HTTP headers are
    required to convey security information.

    When a list of Security Requirement Objects is defined on the OpenAPI Object or Operation Object, only one of
    the Security Requirement Objects in the list needs to be satisfied to authorize the request.
    """

    # TODO - may need to reimplement the ``serialise`` and ``schema``.
    def __init__(self, names: Dict[str, List[str]]):
        """
        Lists the required security schemes to execute this operation. The name used for each property MUST correspond
        to a security scheme declared in the Security Schemes under the Components Object.

        Security Requirement Objects that contain multiple schemes require that all schemes MUST be satisfied for a
        request to be authorized. This enables support for scenarios where multiple query parameters or HTTP headers are
        required to convey security information.

        When a list of Security Requirement Objects is defined on the OpenAPI Object or Operation Object, only one of
        the Security Requirement Objects in the list needs to be satisfied to authorize the request.

        :param names: Each ``names`` dict key MUST correspond to a security scheme which is declared in the Security
            Schemes under the Components Object. If the security scheme is of type "oauth2" or "openIdConnect", then the
            value is a list of scope names required for the execution. For other security scheme types, the array MUST
            be empty.
        """
        # TODO - types
        # TODO - validations
        self.__dict__ = names

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __getitem__(self, key):
        return self.__dict__[key]

    def __repr__(self):
        return repr(self.__dict__)

    def serialize(self, sort=False):
        raise NotImplementedError(self)
        # return self.__dict__

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        del self.__dict__[key]

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def has_key(self, k):
        return k in self.__dict__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, *args):
        return self.__dict__.pop(*args)

    def __cmp__(self, other):
        return self.__dict__.__cmp__(other)

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)


class Operation(OObject):  # pylint: disable=too-many-instance-attributes
    """Describes a single API operation on a path."""

    OPERATION_NAMES = frozenset(("get", "put", "post", "delete", "options", "head", "patch", "trace"))

    def __init__(  # pylint: disable=too-many-arguments
        self,
        operation_id: str,
        responses: Responses,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        external_docs: Optional[ExternalDocumentation] = None,
        parameters: Optional[List[Union[Parameter, Reference]]] = None,
        request_body: Optional[Union[RequestBody, Reference]] = None,
        callbacks: Optional[Dict[str, Union[Callback, Reference]]] = None,
        deprecated: bool = False,
        security: Optional[List[SecurityRequirement]] = None,
        servers: Optional[List[Server]] = None,
        x_handler_route: sanic.router.Route = None,
    ):
        """
        Describes a single API operation on a path.

        :param tags: A list of tags names for API documentation control. Tags can be used for logical grouping of
            operations by resources or any other qualifier.
        :param summary: A short summary of what the operation does.
        :param description: A verbose explanation of the operation behavior. CommonMark syntax MAY be used for rich text
            representation.
        :param external_docs: Additional external documentation for this operation.
        :param operation_id: Unique string used to identify the operation. The id MUST be unique among all operations
            described in the API. The operationId value is case-sensitive. Tools and libraries MAY use the operationId
            to uniquely identify an operation, therefore, it is RECOMMENDED to follow common programming naming
            conventions.
        :param parameters: A list of parameters that are applicable for this operation. If a parameter is already
            defined at the Path Item, the new definition will override it but can never remove it. The list MUST NOT
            include duplicated parameters. A unique parameter is defined by a combination of a name and location. The
            list can use the Reference Object to link to parameters that are defined at the OpenAPI Object's
            components/parameters.
        :param request_body: The request body applicable for this operation. The requestBody is only supported in HTTP
            methods where the HTTP 1.1 specification RFC7231 has explicitly defined semantics for request bodies. In
            other cases where the HTTP spec is vague, requestBody SHALL be ignored by consumers.
        :param responses: REQUIRED. The list of possible responses as they are returned from executing this operation.
        :param callbacks: A map of possible out-of band callbacks related to the parent operation. The key is a unique
            identifier for the Callback Object. Each value in the map is a Callback Object that describes a request that
            may be initiated by the API provider and the expected responses. The key value used to identify the callback
            object is an expression, evaluated at runtime, that identifies a URL to use for the callback operation.
        :param deprecated: Declares this operation to be deprecated. Consumers SHOULD refrain from usage of the declared
            operation. Default value is false.
        :param security: A declaration of which security mechanisms can be used for this operation. The list of values
            includes alternative security requirement objects that can be used. Only one of the security requirement
            objects need to be satisfied to authorize a request. This definition overrides any declared top-level
            security. To remove a top-level security declaration, an empty array can be used.
        :param servers: An alternative server array to service this operation. If an alternative server object is
            specified at the Path Item Object or Root level, it will be overridden by this value.
        """
        # TODO  - types
        _assert_type(parameters, (list,), "parameters", self.__class__)

        # TODO - validations
        _assert_required(responses, "responses", self.__class__)
        _assert_required(operation_id, "operation_id", self.__class__)

        # assignment and docs
        self.tags = tags
        """
        A list of tags for API documentation control. Tags can be used for logical grouping of operations by resources 
        or any other qualifier.
        """

        self.summary = summary
        """A short summary of what the operation does."""

        self.description = description
        """
        A verbose explanation of the operation behavior. CommonMark syntax MAY be used for rich text representation.
        """

        self.external_docs = external_docs
        """Additional external documentation for this operation."""

        assert operation_id
        self.operation_id = operation_id
        """
        Unique string used to identify the operation. The id MUST be unique among all operations described in the API. 
        The operationId value is case-sensitive. Tools and libraries MAY use the operationId to uniquely identify an 
        operation, therefore, it is RECOMMENDED to follow common programming naming conventions.
        """

        self.parameters = parameters
        """
        A list of parameters that are applicable for this operation. If a parameter is already defined at the Path Item, 
        the new definition will override it but can never remove it. The list MUST NOT include duplicated parameters. 
        A unique parameter is defined by a combination of a name and location. The list can use the Reference Object to 
        link to parameters that are defined at the OpenAPI Object's components/parameters.
        """

        self.request_body = request_body
        """
        The request body applicable for this operation. The requestBody is only supported in HTTP methods where the HTTP 
        1.1 specification RFC7231 has explicitly defined semantics for request bodies. In other cases where the HTTP 
        spec is vague, requestBody SHALL be ignored by consumers.
        """

        self.responses = responses
        """REQUIRED. The list of possible responses as they are returned from executing this operation."""

        self.callbacks = callbacks
        """
        A map of possible out-of band callbacks related to the parent operation. The key is a unique identifier for the 
        Callback Object. Each value in the map is a Callback Object that describes a request that may be initiated by 
        the API provider and the expected responses. The key value used to identify the callback object is an 
        expression, evaluated at runtime, that identifies a URL to use for the callback operation.
        """

        self.deprecated = deprecated
        """
        Declares this operation to be deprecated. Consumers SHOULD refrain from usage of the declared operation. Default 
        value is false.
        """

        self.security = security
        """
        A declaration of which security mechanisms can be used for this operation. The list of values includes 
        alternative security requirement objects that can be used. Only one of the security requirement objects need to 
        be satisfied to authorize a request. This definition overrides any declared top-level security. To remove a 
        top-level security declaration, an empty array can be used.
        """

        self.servers = servers
        """
        An alternative server array to service this operation. If an alternative server object is specified at the 
        PathItem Object or Root level, it will be overridden by this value.
        """

        self.x_handler_route = x_handler_route


class Tag(OObject):
    """
    Adds metadata to a single tag that is used by the Operation Object. It is not mandatory to have a Tag Object per tag
    defined in the Operation Object instances.
    """

    def __init__(
        self, name: str, description: Optional[str] = None, external_docs: Optional[ExternalDocumentation] = None,
    ):
        """
        Adds metadata to a single tag that is used by the Operation Object. It is not mandatory to have a Tag Object per
        tag defined in the Operation Object instances.

        :param name: REQUIRED. The name of the tag.
        :param description: A short description for the tag. CommonMark syntax MAY be used for rich text representation.
        :param external_docs: An ExternalDocumentation fpr this tag.
        """

        _assert_required(name, "name", self.__class__)

        self.name = name
        """REQUIRED. The name of the tag."""

        self.description = description
        """A short description for the tag. CommonMark syntax MAY be used for rich text representation."""

        self.external_docs = external_docs
        """Additional external documentation for this tag."""

    def __hash__(self):
        return hash((self.name, self.description, self.external_docs))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            raise NotImplementedError()
        return (
            self.name == other.name
            and self.description == other.description
            and self.external_docs == other.external_docs
        )

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            raise NotImplementedError()
        return (self.name, self.description, self.external_docs) < (other.name, other.description, other.external_docs,)


class PathItem(OObject):  # pylint: disable=too-many-instance-attributes
    """
    Describes the operations available on a single path. A Path Item MAY be empty, due to ACL constraints. The path
    itself is still exposed to the documentation viewer but they will not know which operations and parameters are
    available.
    """

    def __init__(  # pylint: disable=too-many-locals, too-many-arguments
        self,
        dollar_ref: Optional[str] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        get: Optional[Operation] = None,
        put: Optional[Operation] = None,
        post: Optional[Operation] = None,
        delete: Optional[Operation] = None,
        options: Optional[Operation] = None,
        head: Optional[Operation] = None,
        patch: Optional[Operation] = None,
        trace: Optional[Operation] = None,
        servers: Optional[List[Server]] = None,
        parameters: Optional[List[Union[Parameter, Reference]]] = None,
        request_body: Optional[Union[RequestBody, Reference]] = None,
        # TODO = add hide/suppress?
        x_tags_holder: Optional[List[Tag]] = None,
        x_deprecated_holder: bool = False,
        x_external_docs_holder: Optional[ExternalDocumentation] = None,
        x_responses_holder: Optional[Dict[str, Union[Response, Reference]]] = None,
        x_exclude: bool = False,
    ):
        """
        Describes the operations available on a single path. A Path Item MAY be empty, due to ACL constraints. The path
        itself is still exposed to the documentation viewer but they will not know which operations and parameters are
        available.

        :param dollar_ref: Allows for an external definition of this path item. The referenced structure MUST be in the
            format of a Path Item Object. If there are conflicts between the referenced definition and this Path Item's
            definition, the behavior is undefined.
        :param summary: An optional, string summary, intended to apply to all operations in this path.
        :param description: An optional, string description, intended to apply to all operations in this path.
            CommonMark syntax MAY be used for rich text representation.
        :param get: A definition of a GET operation on this path.
        :param put: A definition of a PUT operation on this path.
        :param post: A definition of a POST operation on this path.
        :param delete: A definition of a DELETE operation on this path.
        :param options: A definition of an OPTIONS operation on this path.
        :param head: A definition of a HEAD operation on this path.
        :param patch: A definition of a PATCH operation on this path.
        :param trace: A definition of a TRACE operation on this path.
        :param servers: An alternative server array to service all operations in this path.
        :param parameters: A list of parameters that are applicable for all the operations described under this
            path. These parameters can be overridden at the operation level, but cannot be removed there. The list
            MUST NOT include duplicated parameters. A unique parameter is defined by a combination of a name and
            location. The list can use the Reference Object to link to parameters that are defined at the OpenAPI
            Object's components/parameters.
        :param request_body: sanic-openapi3e implementation extension to allow requestBody to be defined.
        :param x_tags_holder: sanic-openapi3e implementation extension to allow tags on the PathItem until they can be
            passed to the Operation/s.
        :param x_deprecated_holder: sanic-openapi3e implementation extension to allow deprecated on the PathItem until
            they can be passed to the Operation/s.
        :param x_external_docs_holder: sanic-openapi3e implementation extension to allow externalDocs on the PathItem
            until they can be passed to the Operation/s.
        :param x_responses_holder: sanic-openapi3e implementation extension to allow Responses on the PathItem until
            they can be passed to the Operation/s.
        :param x_exclude: sanic-openapi3e extension to completly exclude the path from the spec.
        """
        if x_external_docs_holder:
            raise ValueError(x_external_docs_holder)

        # TODO - validations
        if x_tags_holder:
            for x_tag in x_tags_holder:
                _assert_type(x_tag, (Tag,), "x_tags_holder[*]", self.__class__)

        # Assignment and docs
        self.dollar_ref = dollar_ref
        """
        Allows for an external definition of this path item. The referenced structure MUST be in the format of a Path 
        Item Object. If there are conflicts between the referenced definition and this Path Item's definition, the 
        behavior is undefined.
        """

        self.summary = summary
        """An optional, string summary, intended to apply to all operations in this path."""

        self.description = description
        """
        An optional, string description, intended to apply to all operations in this path. CommonMark syntax MAY be used 
        for rich text representation.
        """

        self.get = get
        """ A definition of a GET operation on this path."""

        self.put = put
        """A definition of a PUT operation on this path."""

        self.post = post
        """A definition of a POST operation on this path."""

        self.delete = delete
        """A definition of a DELETE operation on this path."""

        self.options = options
        """A definition of an OPTIONS operation on this path."""

        self.head = head
        """A definition of a HEAD operation on this path."""

        self.patch = patch
        """A definition of an PATCH operation on this path."""

        self.trace = trace
        """A definition of a TRACE operation on this path."""

        self.servers = servers
        """An alternative server array to service all operations in this path."""

        self.parameters: List[Union[Parameter, Reference]] = parameters if parameters is not None else []
        """
        A list of parameters that are applicable for all the operations described under this path. These 
        parameters can be overridden at the operation level, but cannot be removed there. The list MUST NOT 
        include duplicated parameters. A unique parameter is defined by a combination of a name and location. The 
        list can use the Reference Object to link to parameters that are defined at the OpenAPI Object's 
        components/parameters.
        """

        self.request_body = request_body

        self.x_tags_holder: List[Tag] = x_tags_holder if x_tags_holder is not None else []
        self.x_deprecated_holder = x_deprecated_holder
        self.x_responses_holder: Responses = Responses(x_responses_holder)
        self.x_external_docs_holder = x_external_docs_holder
        self.x_exclude = x_exclude

    def x_operations(self) -> List[Operation]:
        _ops = [self.get, self.get, self.put, self.post, self.delete, self.options, self.head, self.patch, self.trace]
        return [_op for _op in _ops if _op]


class Paths(OObject):
    """
    Holds the relative endpoints to the individual endpoints and their operations. The path is appended to the URL
    from the Server Object in order to construct the full URL. The Paths MAY be empty, due to ACL constraints.
    """

    def __init__(self, path_items: Optional[List[Tuple[str, PathItem]]] = None):
        """
        Holds the relative endpoints to the individual endpoints and their operations. The path is appended to the URL
        from the Server Object in order to construct the full URL. The Paths MAY be empty, due to ACL constraints.

        :param path_items The endpoints
        """
        self.locked: bool = False
        self._paths: List[Tuple[str, PathItem]] = []
        """
        A collection of your `app`'s functions and their Path Item. The field name MUST begin with a slash. The path is 
        appended (no relative URL resolution) to the expanded URL from the Server Object's url field in order to 
        construct the full URL. Path templating is allowed. When matching URLs, concrete (non-templated) endpoints would 
        be matched before their templated counterparts. Templated endpoints with the same hierarchy but different 
        templated names MUST NOT exist as they are identical. In case of ambiguous matching, it's up to the tooling to 
        decide which one to use.
        """
        if path_items:
            self.locked = True
            self._paths = path_items

    def __len__(self):
        return len(self._paths)

    def __getitem__(self, item: str) -> PathItem:
        """
        A defaultdict interface if not locked.

        :param item: What to find.
        """

        for _parsed_uri, path_item in self._paths:
            if _parsed_uri == item:
                return path_item
        if not self.locked:
            path_item = PathItem()
            self._paths.append((item, path_item))
            return self._paths[-1][1]
        raise KeyError(item)

    def __contains__(self, item):
        return any(_parsed_uri == item for _parsed_uri, _path_item in self._paths)

    def __iter__(self):
        yield from self._paths

    def __setitem__(self, key, value):

        if not self.locked:
            for idx, _ in enumerate(self._paths):
                if self._paths[idx][0] == key:
                    self._paths[idx] = (key, value)
                    break
            else:
                raise KeyError(key)
        else:
            raise ValueError("locked")


class OpenAPIv3(OObject):  # pylint: disable=too-many-instance-attributes
    """The root document object of the OpenAPI document."""

    version = "3.0.2"

    def __init__(  # pylint: disable=too-many-arguments
        self,
        openapi: str,
        info: Info,
        paths: Paths,
        servers: Optional[List[Server]] = None,
        components: Optional[Components] = None,
        security: Optional[List[SecurityRequirement]] = None,
        tags: Optional[List[Tag]] = None,
        external_docs: Optional[ExternalDocumentation] = None,
    ):
        """
        This is the root document object of the OpenAPI document.

        :param openapi: REQUIRED. This string MUST be the semantic version number of the OpenAPI Specification version
            that the OpenAPI document uses. The openapi field SHOULD be used by tooling specifications and clients to
            interpret the OpenAPI document. This is not related to the API info.version string.
        :param info: REQUIRED. Provides metadata about the API. The metadata MAY be used by tooling as required.
        :param servers: An array of Server Objects, which provide connectivity information to a target server. If the
            servers property is not provided, or is an empty array, the default value would be a Server Object with a
            url value of /.
        :param paths: REQUIRED. The available endpoints and operations for the API.
        :param components: An element to hold various schemas for the specification.
        :param security: A declaration of which security mechanisms can be used across the API. The list of values
            includes alternative security requirement objects that can be used. Only one of the security requirement
            objects need to be satisfied to authorize a request. Individual operations can override this definition.
        :param tags: A list of tags used by the specification with additional metadata. The order of the tags can be
            used to reflect on their order by the parsing tools. Not all tags that are used by the Operation Object must
            be declared. The tags that are not declared MAY be organized randomly or based on the tools' logic. Each tag
            name in the list MUST be unique.
        :param external_docs: Additional external documentation.
        """

        _assert_type(openapi, (str,), "openapi", self.__class__)
        _assert_type(info, (Info,), "info", self.__class__)
        _assert_type(servers, (list,), "servers", self.__class__)
        _assert_type(paths, (Paths,), "endpoints", self.__class__)
        _assert_type(components, (Components,), "components", self.__class__)
        _assert_type(security, (list,), "security", self.__class__)
        _assert_type(tags, (list,), "tags", self.__class__)
        _assert_type(external_docs, (ExternalDocumentation,), "external_docs", self.__class__)

        _assert_required(openapi, "openapi", self.__class__)
        _assert_required(info, "info", self.__class__)
        _assert_required(paths, "endpoints", self.__class__)

        # TODO - other assertions - eg `Servers`
        if tags:
            assert len([t.name for t in tags]) == len(tags)

        self.openapi = openapi
        """
        REQUIRED. This string MUST be the semantic version number of the OpenAPI Specification version that the OpenAPI 
        document uses. The openapi field SHOULD be used by tooling specifications and clients to interpret the OpenAPI 
        document. This is not related to the API info.version string."""

        self.info = info
        """REQUIRED. Provides metadata about the API. The metadata MAY be used by tooling as required."""
        assert paths
        self.paths = paths
        """REQUIRED. The available endpoints and operations for the API."""

        self.servers = servers
        """
        An array of Server Objects, which provide connectivity information to a target server. If the servers property 
        is not provided, or is an empty array, the default value would be a Server Object with a url value of /.
        """
        self.components = components
        """An element to hold various schemas for the specification."""

        self.security = security
        """
        A declaration of which security mechanisms can be used across the API. The list of values includes alternative 
        security requirement objects that can be used. Only one of the security requirement objects need to be satisfied 
        to authorize a request. Individual operations can override this definition.
        """

        if tags:
            assert sorted({t.name for t in tags}) == sorted(t.name for t in tags)
        self.tags = tags
        """
        A list of tags used by the specification with additional metadata. The order of the tags can be used to reflect 
        on their order by the parsing tools. Not all tags that are used by the Operation Object must be declared. The 
        tags that are not declared MAY be organized randomly or based on the tools' logic. Each tag name in the list 
        MUST be unique.
        """

        self.external_docs = external_docs
        """Additional external documentation."""

    def as_yamlable_object(self, sort=False, opt_key: Optional[str] = None):
        # This one is here to allow mypy to accept that the root `yaml`-able object really is always a dict. That
        # annotation is found near the top of `openapi.py`.
        return super().as_yamlable_object(sort=False, opt_key=".")
