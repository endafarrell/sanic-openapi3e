"""Basic tests for the openapi_blueprint."""
import json
import sys
from typing import Dict, Union

import pytest
import sanic.request
import sanic.response
from sanic import Sanic

import sanic_openapi3e.oas_types

# Some ~static~ reusable objects
int_min_4 = sanic_openapi3e.oas_types.Schema(
    _type="integer", _format="int32", minimum=4, description="Minimum: 4"
)  # type: sanic_openapi3e.oas_types.Schema

an_id_ex1 = sanic_openapi3e.oas_types.Example(
    summary="A small number", description="description: Numbers less than ten", value=7
)  # type: sanic_openapi3e.oas_types.Example

an_id_ex2 = sanic_openapi3e.oas_types.Example(
    summary="A big number", description="description: Numbers more than one million!", value=123456789,
)  # type: sanic_openapi3e.oas_types.Example

strict_slashes = True
true = True
false = False
null = None


# ------------------------------------------------------------ #
# pytest fixtures. Given that the sanic_openapi3e state is held
# in the module, we need to have them as fixtures to avoid the
# routes from all tests being visible together.
#
# While `scope="function"` is the default, it's helpful to be
# explicitly clear about it.
# ------------------------------------------------------------ #


@pytest.fixture(scope="function")
def openapi__mod_bp_doc():
    for t_unimport in (
        "sanic_openapi3e",
        "sanic_openapi3e.doc",
        "sanic_openapi3e.openapi",
    ):
        if t_unimport in sys.modules:
            del sys.modules[t_unimport]
    import sanic_openapi3e.openapi
    from sanic_openapi3e import doc, openapi_blueprint

    yield sanic_openapi3e.openapi, openapi_blueprint, doc

    # The teardown - so when each function that uses this fixture has finished, these
    # modules are uninstalled and thus they will be re-imported anew for the next use.
    for t_unimport in (
        "sanic_openapi3e",
        "sanic_openapi3e.doc",
        "sanic_openapi3e.openapi",
    ):
        del sys.modules[t_unimport]


def run_asserts(
    response: Union[
        sanic.response.HTTPResponse, sanic.response.StreamingHTTPResponse, Dict, sanic_openapi3e.oas_types.OpenAPIv3,
    ],
    expected: Dict,
):
    """
    Helper to run the assert and print the values if needed.

    :param response: What was returned by the test call
    :param expected: What was expected to be returned

    """
    if isinstance(response, dict):
        # Allows for test writing flexibility
        spec = response  # pragma: no cover
    elif isinstance(response, sanic_openapi3e.oas_types.OpenAPIv3):
        # Allows for test writing flexibility
        spec = response.serialize()  # pragma: no cover
    else:
        # Most tests use this
        assert response.status == 200
        spec = json.loads(response.body.decode())

    actual_str = json.dumps(spec, sort_keys=True)
    expected_str = json.dumps(expected, sort_keys=True)
    if actual_str != expected_str:
        # Not covered as we really don't want failures ;-)
        print("\n\nWarning: actual and expected specs differ:")  # pragma: no cover
        print("\nactual:\n", actual_str)  # pragma: no cover
        print("\nexpected:\n", expected_str)  # pragma: no cover
        print("")  # pragma: no cover
        # assert actual_str == expected_str
        assert json.loads(actual_str) == json.loads(expected_str)
