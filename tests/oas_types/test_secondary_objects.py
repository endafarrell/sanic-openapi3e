import pytest

from sanic_openapi3e.oas_types import (
    XML,
    Contact,
    Discriminator,
    Encoding,
    Example,
    Header,
    Link,
    MediaType,
    OAuthFlow,
    OAuthFlows,
    SecurityScheme,
    ServerVariable,
)

########################################################################################################################
# Discriminator
########################################################################################################################


def test_discriminator():
    assert Discriminator(
        property_name="name", mapping={"first": "FirstName", "last": "LastName"}
    ).as_yamlable_object() == {"mapping": {"first": "FirstName", "last": "LastName"}, "propertyName": "name"}

    with pytest.raises(AssertionError):
        Discriminator(property_name="name", mapping={"first": "FirstName", "last": "LastName", "contact": Contact})


########################################################################################################################
# Encoding
########################################################################################################################


def test_encoding():
    assert Encoding(content_type="text/plain").as_yamlable_object() == {
        "allowReserved": False,
        "contentType": "text/plain",
        "explode": False,
    }


########################################################################################################################
# Header
########################################################################################################################


def test_header():
    assert Header().as_yamlable_object() == {
        "allowEmptyValue": False,
        "allowReserved": False,
        "explode": False,
        "required": False,
    }
    assert Header(content={"text/plain": MediaType(example="Bearer ....token...")}).as_yamlable_object() == {
        "allowEmptyValue": False,
        "allowReserved": False,
        "content": {"text/plain": {"example": "Bearer ....token..."}},
        "explode": False,
        "required": False,
    }

    with pytest.raises(AssertionError):
        Header(example="an example", examples={"a": Example(description="a"), "b": Example(description="b")})

    with pytest.raises(AssertionError):
        # noinspection PyTypeChecker
        assert Header(examples={"a": 2})

    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        assert Header(content={"a": 2})

    with pytest.raises(AssertionError):
        media_type = MediaType()
        # noinspection PyTypeChecker
        assert Header(content={"a": media_type, "b": media_type})


########################################################################################################################
# Link
########################################################################################################################


def test_link():
    assert Link(operation_id="getDetailsForUser").as_yamlable_object() == {
        "operationId": "getDetailsForUser",
    }


########################################################################################################################
# OAuthFlows, OAuthFlow
########################################################################################################################


def test_oauthflows_keys_casing__issue9():
    assert OAuthFlows(
        authorization_code=OAuthFlow(
            authorization_url="authorization_url", token_url="token_url", scopes={"scope1": "", "scope2": ""},
        )
    ).as_yamlable_object() == {
        "authorizationCode": {
            "authorizationUrl": "authorization_url",
            "tokenUrl": "token_url",
            "scopes": {"scope1": "", "scope2": ""},
        }
    }


########################################################################################################################
# SecurityScheme
########################################################################################################################


def test_security_scheme():
    assert SecurityScheme(
        _type="http", name="Authorization", _in="header", flows=None, openid_connect_url=None, scheme="Bearer"
    ).as_yamlable_object() == {"in": "header", "name": "Authorization", "scheme": "Bearer", "type": "http"}


########################################################################################################################
# ServerVariable
########################################################################################################################


def test_servervariable():
    assert ServerVariable(
        default="prod", enum=["dev", "staging", "prod"], description="instance environment"
    ).as_yamlable_object() == {
        "default": "prod",
        "description": "instance environment",
        "enum": ["dev", "staging", "prod"],
    }

    with pytest.raises(AssertionError):
        not_a_str: int = 404
        ServerVariable(default="prod", enum=["dev", "staging", "prod", not_a_str], description="instance environment")

    with pytest.raises(AssertionError):

        ServerVariable(
            default="prod",
            enum=["dev", "staging", "prod", "repeated-env", "repeated-env"],
            description="instance environment",
        )


########################################################################################################################
# XML
########################################################################################################################


def test_xml():
    assert XML(name="name", namespace="ns", prefix="prefix", attribute=False, wrapped=False).as_yamlable_object() == {
        "name": "name",
        "namespace": "ns",
        "prefix": "prefix",
        "attribute": False,
        "wrapped": False,
    }
