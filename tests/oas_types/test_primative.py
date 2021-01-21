import pytest

import sanic_openapi3e
import sanic_openapi3e.oas_types


def test_otype():
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        sanic_openapi3e.oas_types.Contact(name=2)

    o_contact = sanic_openapi3e.oas_types.Contact(name="name", url="url")
    assert o_contact.serialize() == {"name": "name", "url": "url"}


def test_asserts():
    with pytest.raises(AssertionError):
        sanic_openapi3e.oas_types._assert_required(None, "name", sanic_openapi3e.oas_types.OpenAPIv3, why="a test")

    with pytest.raises(AssertionError):
        sanic_openapi3e.oas_types._assert_strictly_greater_than_zero(-1, "min_length", sanic_openapi3e.oas_types.Schema)


@pytest.mark.parametrize(
    "key, expected", [("bearerToken", "bearerToken"), ("bearer_format", "bearerFormat"), ("dollar_ref", "$ref"),]
)
def test_openapi_keyname(key: str, expected: str):
    assert sanic_openapi3e.oas_types.openapi_keyname(key) == expected
