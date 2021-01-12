from typing import Set

import pytest

import sanic_openapi3e.oas_types
from sanic_openapi3e.oas_types import Tag


def test_otype():
    with pytest.raises(TypeError):
        # noinspection PyArgumentList
        o = sanic_openapi3e.oas_types.OType(value=2)
        assert o.serialize(for_repr=False) == {"value": 2}

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


def test_license():
    _license = sanic_openapi3e.oas_types.License(name="name", url="www.url.com")
    assert _license.serialize() == {"name": "name", "url": "www.url.com"}


def test_pathitem():
    pi = sanic_openapi3e.oas_types.PathItem()
    pi.x_exclude = True
    assert pi.x_exclude

    ps = sanic_openapi3e.oas_types.Paths()
    pi = ps[test_pathitem]
    pi.x_exclude = True
    assert pi.x_exclude
    assert test_pathitem in ps
    assert ps[test_pathitem] == pi
    assert ps[test_pathitem].x_exclude
    ps[test_pathitem] = pi
    assert ps[test_pathitem].x_exclude


def test_tag_eq():
    tag = Tag("name", "desc")
    assert tag == tag
    assert tag == Tag("name", "desc")


def test_set_of_tags():
    tags: Set[Tag] = set()
    tags.add(Tag("name", "desc"))
    tags.add(Tag("name", "desc"))
    assert len(tags) == 1, tags
