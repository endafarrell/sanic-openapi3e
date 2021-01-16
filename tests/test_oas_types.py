from typing import Set

import pytest

import sanic_openapi3e.oas_types
from sanic_openapi3e.oas_types import OAuthFlow, OAuthFlows, Tag


def test_otype():
    with pytest.raises(TypeError):
        # noinspection PyArgumentList
        sanic_openapi3e.oas_types.OType(value=2)

    o_int = sanic_openapi3e.oas_types.OInteger(value=2, _format="int32")
    assert o_int.serialize(for_repr=False) == {"value": 2, "format": "int32"}

    o_int64 = sanic_openapi3e.oas_types.OInteger(value=2, _format="int64")
    assert o_int64.serialize(for_repr=False) == {"value": 2, "format": "int64"}

    o_number = sanic_openapi3e.oas_types.ONumber(value=3.14)
    assert o_number.serialize(for_repr=True) == {"value": 3.14}
    assert o_number.serialize(for_repr=False) == {"value": 3.14}


def test_contact():
    contact = sanic_openapi3e.oas_types.Contact(name="name", url="www.url.com", email="email@url.com")
    assert contact.serialize() == {
        "name": "name",
        "url": "www.url.com",
        "email": "email@url.com",
    }
    assert contact.as_yamlable_object() == {
        "name": "name",
        "url": "www.url.com",
        "email": "email@url.com",
    }


def test_license():
    _license = sanic_openapi3e.oas_types.License(name="name", url="www.url.com")
    assert _license.serialize() == {"name": "name", "url": "www.url.com"}


def test_pathitem():
    pi = sanic_openapi3e.oas_types.PathItem(x_exclude=True)
    assert pi.x_exclude

    ps = sanic_openapi3e.oas_types.Paths([("test_pathitem", pi)])
    pi = ps["test_pathitem"]
    assert pi.x_exclude


def test_tag_eq():
    tag = Tag("name", "desc")
    assert tag == tag
    assert tag == Tag("name", "desc")


def test_set_of_tags():
    tags: Set[Tag] = set()
    tags.add(Tag("name", "desc"))
    tags.add(Tag("name", "desc"))
    assert len(tags) == 1, tags


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
