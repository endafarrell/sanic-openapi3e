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
        spec = response
    elif isinstance(response, sanic_openapi3e.oas_types.OpenAPIv3):
        spec = response.serialize()
    else:
        assert response.status == 200
        spec = json.loads(response.body.decode())

    if json.dumps(spec, sort_keys=True) != json.dumps(
        expected, sort_keys=True
    ):
        print("\n   actual:", json.dumps(spec, sort_keys=True))
        print("expected:", json.dumps(expected, sort_keys=True))

    assert json.loads(json.dumps(spec, sort_keys=True)) == json.loads(json.dumps(expected, sort_keys=True))


def test_fundamentals(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_fundamentals", strict_slashes=strict_slashes,)

    app.blueprint(openapi_blueprint)

    @app.get("/test/102/anId/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, _in="path", schema=sanic_openapi3e.oas_types.Schema.Integer,
    )
    def test_id(request, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/102/anId/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~102~anId~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                }
            }
        },
    }

    run_asserts(response, expected)


def test_path_integer_min(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_consumes_from_path_does_not_duplicate_parameters", strict_slashes=strict_slashes,)

    app.blueprint(openapi_blueprint)

    @app.get("/test/148/anId/<an_id:int>")
    @doc.parameter(name="an_id", description="An ID", required=True, _in="path", schema=int_min_4)
    def test_id(request, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/148/anId/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~148~anId~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"description": "Minimum: 4", "format": "int32", "minimum": 4, "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                }
            }
        },
    }

    run_asserts(response, expected)


def test_path_integer_examples_w_summary_and_description(openapi__mod_bp_doc):
    openapi_mod, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path_integer_examples_w_summary_and_description", strict_slashes=strict_slashes,)
    app.config.OPENAPI_OPERATION_ID_FN = openapi_mod.camel_case_operation_id_fn

    app.blueprint(openapi_blueprint)

    @app.get("/examples/195/test_id_examples/<an_id:int>")
    @doc.parameter(
        name="an_id",
        description="An ID",
        required=True,
        _in="path",
        schema=int_min_4,
        examples={"small": an_id_ex1, "big": an_id_ex2},
    )
    @doc.summary("A path with parameter examples")
    @doc.description("Swagger UIs do not show examples")
    def test_id_examples(request, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/examples/195/test_id_examples/{an_id}": {
                "get": {
                    "description": "Swagger UIs do not show examples",
                    "operationId": "testIdExamples",
                    "parameters": [
                        {
                            "description": "An ID",
                            "examples": {
                                "big": {
                                    "description": "description: Numbers more than one million!",
                                    "summary": "A big number",
                                    "value": 123456789,
                                },
                                "small": {
                                    "description": "description: Numbers less than ten",
                                    "summary": "A small number",
                                    "value": 7,
                                },
                            },
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"description": "Minimum: 4", "format": "int32", "minimum": 4, "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                    "summary": "A path with parameter examples",
                }
            }
        },
    }

    run_asserts(response, expected)


def test_path__deprecated(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path__deprecated", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/examples/260/test_path__deprecated/<an_id:int>")
    @doc.deprecated()  # <<-- detail under test
    @doc.parameter(
        name="an_id",
        description="An ID",
        required=True,
        _in="path",
        schema=int_min_4,
        examples={"small": an_id_ex1, "big": an_id_ex2},
    )
    @doc.summary("A path with parameter examples")
    @doc.description("This should be marked as being deprecated")
    def path__deprecated(request, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/examples/260/test_path__deprecated/{an_id}": {
                "get": {
                    "deprecated": true,
                    "description": "This should be marked as being deprecated",
                    "operationId": "GET~~~examples~260~test_path__deprecated~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "examples": {
                                "big": {
                                    "description": "description: Numbers more than one million!",
                                    "summary": "A big number",
                                    "value": 123456789,
                                },
                                "small": {
                                    "description": "description: Numbers less than ten",
                                    "summary": "A small number",
                                    "value": 7,
                                },
                            },
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {
                                "description": "Minimum: 4",
                                "format": "int32",
                                "minimum": 4,
                                "type": "integer",
                            },
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                    "summary": "A path with parameter examples",
                }
            }
        },
    }

    run_asserts(response, expected)


def test_parameter__deprecated(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_parameter__deprecated", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/examples/327/test_parameter__deprecated/<an_id:int>")
    @doc.parameter(
        name="an_id",
        description="An ID",
        required=True,
        _in="path",
        schema=sanic_openapi3e.oas_types.Schema.Integer,
        deprecated=True,  # <<-- detail under test
    )
    @doc.summary("A path deprecated parameter")
    @doc.description("The parameter should be marked as deprecated")
    def param__deprecated(request, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/examples/327/test_parameter__deprecated/{an_id}": {
                "get": {
                    "description": "The parameter should be marked as deprecated",
                    "operationId": "GET~~~examples~327~test_parameter__deprecated~an_id",
                    "parameters": [
                        {
                            "deprecated": true,
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                    "summary": "A path deprecated parameter",
                }
            }
        },
    }

    run_asserts(response, expected)


# ------------------------------------------------------------ #
#  tag details
# ------------------------------------------------------------ #


def test_tag_unique_description__conflicts(openapi__mod_bp_doc):
    """Test tags have non-conflicting values: conflicting values are disallowed."""
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_tag_unique_description__conflicts", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/382/anId/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    @doc.response(200, description="A 200 description")
    @doc.response(201, description="A 201 description")
    @doc.tag("Described tag", description="This tag has a lovely description.")
    def test_id(_, an_id: int):
        return sanic.response.json(locals())

    with pytest.raises(AssertionError, match=r"^Conflicting tag.description for tag"):

        @app.get("/test/398/anId2/<an_id:int>")
        @doc.parameter(
            name="an_id", description="An ID", required=True, choices=[1, 3, 5, 7, 11, 13], _in="path",
        )
        @doc.response(200, description="A 200 description")
        @doc.response(201, description="A 201 description")
        @doc.tag("Described tag", description="This same tag has a conflicting description")  # <<-- detail under test
        def test_id2(_, an_id: int):
            return sanic.response.json(locals())


def test_tag_unique_description__one_null(openapi__mod_bp_doc):
    """Test tags have non-conflicting values: only one of them has been described but that one description is seen by
    all."""
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_tag_unique_description__one_null", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/423/anId/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    @doc.response(200, description="A 200 description")
    @doc.response(201, description="A 201 description")
    @doc.tag("Described tag", description="This tag has a lovely description.")
    def test_id(_, an_id: int):
        return sanic.response.json(locals())

    @app.get("/test/437/anId2/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    @doc.response(200, description="A 200 description")
    @doc.response(201, description="A 201 description")
    @doc.tag("Described tag")  # <<-- detail under test
    def test_id2(_, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/423/anId/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~423~anId~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "A 200 description"},
                        "201": {"description": "A 201 description"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                    "tags": ["Described tag"],
                }
            },
            "/test/437/anId2/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~437~anId2~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "A 200 description"},
                        "201": {"description": "A 201 description"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                    "tags": ["Described tag"],
                }
            },
        },
        "tags": [{"description": "This tag has a lovely description.", "name": "Described tag"}],
    }
    run_asserts(response, expected)


def test_tag_unique_description__same(openapi__mod_bp_doc):
    """
    Test tags have non-conflicting values: only one of them has been described but that one description is seen by all.
    """
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_tag_unique_description__same", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/515/anId/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    @doc.response(200, description="A 200 description")
    @doc.response(201, description="A 201 description")
    @doc.tag("Described tag", description="This tag has a lovely description.")
    def test_id(_, an_id: int):
        return sanic.response.json(locals())

    @app.get("/test/529/anId2/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    @doc.response(200, description="A 200 description")
    @doc.response(201, description="A 201 description")
    @doc.tag("Described tag", description="This tag has a lovely description.")  # <<-- the detail under test.
    def test_id2(_, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/515/anId/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~515~anId~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "A 200 description"},
                        "201": {"description": "A 201 description"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                    "tags": ["Described tag"],
                }
            },
            "/test/529/anId2/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~529~anId2~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "A 200 description"},
                        "201": {"description": "A 201 description"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                    "tags": ["Described tag"],
                }
            },
        },
        "tags": [{"description": "This tag has a lovely description.", "name": "Described tag"}],
    }

    run_asserts(response, expected)


def test_path_with_multiple_methods_does_not_repeat_tags(openapi__mod_bp_doc):
    """
    Test tags on paths with multiple methods are not repeated
    """
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path_with_multiple_methods_does_not_repeat_tags", strict_slashes=strict_slashes,)

    app.blueprint(openapi_blueprint)

    @app.get("/test/609/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    @doc.response(200, description="A 200 description")
    @doc.response(201, description="A 201 description")
    @doc.tag("Described tag", description="This tag has a lovely description.")
    def test_id(_, an_id: int):
        return sanic.response.json(locals())

    @app.post("/test/609/<an_id:int>")  # <<-- the detail under test.
    @doc.parameter(
        name="an_id", description="An ID", required=True, choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    @doc.response(200, description="A 200 description")
    @doc.response(201, description="A 201 description")
    @doc.tag("Described tag", description="This tag has a lovely description.")
    def test_id2(_, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/609/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~609~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "A 200 description"},
                        "201": {"description": "A 201 description"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                    "tags": ["Described tag"],
                },
                "post": {
                    "operationId": "POST~~~test~609~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "A 200 description"},
                        "201": {"description": "A 201 description"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                    "tags": ["Described tag"],
                },
            }
        },
        "tags": [{"description": "This tag has a lovely description.", "name": "Described tag"}],
    }

    run_asserts(response, expected)


def test_path_with_multiple_equal_tags_does_not_repeat_tags(openapi__mod_bp_doc):
    """
    Test duplicated tags on paths  are not repeated
    """
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path_with_multiple_equal_tags_does_not_repeat_tags", strict_slashes=strict_slashes,)

    app.blueprint(openapi_blueprint)

    @app.get("/test/609/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    @doc.response(200, description="A 200 description")
    @doc.response(201, description="A 201 description")
    @doc.tag("Described tag", description="This tag has a lovely description.")
    @doc.tag("Described tag", description="This tag has a lovely description.")  # <<-- the detail under test.
    def test_id(_, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/609/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~609~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "A 200 description"},
                        "201": {"description": "A 201 description"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                    "tags": ["Described tag"],
                }
            }
        },
        "tags": [{"description": "This tag has a lovely description.", "name": "Described tag"}],
    }

    run_asserts(response, expected)


# ------------------------------------------------------------ #
#  responses details
# ------------------------------------------------------------ #


def test_responses_takes_description(openapi__mod_bp_doc):
    """Test we can describe the responses by their status codes."""
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_responses_takes_description", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/612/anId")
    @doc.response(200, description="A 200 description")
    @doc.response(201, description="A 201 description")
    def test_id(_):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/612/anId": {
                "get": {
                    "operationId": "GET~~~test~612~anId",
                    "responses": {
                        "200": {"description": "A 200 description"},
                        "201": {"description": "A 201 description"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                }
            }
        },
    }

    run_asserts(response, expected)


def test_list_is_a_list_in_query(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_list_is_a_list_in_path", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/644/some_ids")
    @doc.parameter(
        name="an_id",
        description="An ID",
        required=True,
        choices=[1, 3, 5, 7, 11, 13],
        _in="query",
        schema=sanic_openapi3e.oas_types.Schema.Integers,
    )
    def test_some_ids(req):
        args = req.args
        ids = args.getlist("a_param_that_is_not_there")
        return sanic.response.json({"args": args, "ids": ids})

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/644/some_ids": {
                "get": {
                    "operationId": "GET~~~test~644~some_ids",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "query",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "items": {"type": "integer"}, "type": "array"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                }
            }
        },
    }

    run_asserts(response, expected)

    _, response = app.test_client.get("/test/644/some_ids?ids=1&ids=5")
    assert response.status == 200
    resp = json.loads(response.body.decode())
    # TODO - notice that these `ids` are a list, but of str not int. This is expected and users need to
    # TODO - handle this.
    assert resp == {"args": {"ids": ["1", "5"]}, "ids": null}


@pytest.mark.xfail(reason="Enda is not to spec")
def test_param__name_in(openapi__mod_bp_doc):
    # TODO test_field_names_cannot_be_repeated_in_different_locations ?
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_param__name_in", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/699/some_ids/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, choices=[0, 2, 4, 8, 16], _in="path",
    )
    @doc.parameter(
        name="an_id",
        description="An ID",
        required=True,
        choices=[1, 3, 5, 7, 11, 13],
        _in="query",
        schema=sanic_openapi3e.oas_types.Schema.Integers,
    )
    def test_some_ids(req, an_id):
        args = req.args
        ids = args.getlist("an_id")
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"title": "API", "version": "1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/some_ids": {
                "get": {
                    "operationId": "test_some_ids",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "query",
                            "name": "an_id",
                            "required": true,
                            "schema": {"items": {"type": "integer"}, "type": "array"},
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }

    run_asserts(response, expected)

    _, response = app.test_client.get("/test/some_ids?ids=1&ids=5")
    assert response.status == 200
    resp = json.loads(response.body.decode())
    # TODO - notice that these `ids` are a list, but of str not int. This is expected and users need to
    # TODO - handle this.
    assert resp == {"args": {"ids": ["1", "5"]}, "ids": null, "req": {}}


def test_path_params_must_be_required(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path_params_must_be_required", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/759/anId2/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path"
    )  # <<-- note: there is no `required=True` here!
    def test_id2(_, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/759/anId2/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~759~anId2~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,  # <<-- note: detail under test
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                }
            }
        },
    }

    run_asserts(response, expected)


def test_path_without_parameter(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path_without_consumes", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/798/anId/<an_id:int>")
    def test_id(_, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/798/anId/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~798~anId~an_id",
                    "parameters": [{"in": "path", "name": "an_id", "required": true, "schema": {"type": "integer"}}],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                }
            }
        },
    }

    run_asserts(response, expected)


@pytest.mark.xfail(reason="The type is not being updated as expected yet.")
def test_path_parameter_conflicting_types(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path_parameter_conflicting_types", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/833/anId/<an_id>")
    @doc.parameter(
        name="an_id",
        description="An ID",
        choices=[1, 3, 5, 7, 11, 13],
        _in="path",
        # This is the conflict - path says str (implicitly), this next line says int
        schema=sanic_openapi3e.oas_types.Schema.Integer,
    )
    def test_id(_, an_id: int):
        return sanic.response.json(locals())

    spec = sanic_openapi3e.openapi._build_openapi_spec(
        app, hide_openapi_self=True, hide_excluded=True, show_unused_tags=False
    )

    expected = {
        "info": {"description": "Description", "title": "API", "version": "1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/833/anId/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~833~anId~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"items": {"type": "integer"}, "type": "array", "enum": [1, 3, 5, 7, 11, 13],},
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }
    if spec:
        import pprint

        pprint.pprint(spec)
    run_asserts(spec, expected)


def test_path_exclude(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path_exclude", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/878/path_exclude/<an_id:int>")
    @doc.exclude()
    @doc.parameter(
        name="an_id", description="An ID w/ desx", choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    def path_exclude(_, an_id: int):
        return sanic.response.json(locals())

    @app.get("/test/889/test_path_not_exclude/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID w/desc", choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    def path_not_exclude(_, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/889/test_path_not_exclude/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~889~test_path_not_exclude~an_id",
                    "parameters": [
                        {
                            "description": "An ID w/desc",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                }
            }
        },
    }
    run_asserts(response, expected)


def test_path_methods(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path_methods", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/925/item/<an_id:int>")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def get_item(_, an_id: int):
        return sanic.response.json(locals())

    @app.put("/test/925/item/<an_id:int>")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def put_item(_, an_id: int):
        return sanic.response.json(locals())

    @app.post("/test/925/item/<an_id:int>")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def post_item(_, an_id: int):
        return sanic.response.json(locals())

    @app.delete("/test/925/item/<an_id:int>")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def delete_item(_, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/925/item/{an_id}": {
                "delete": {
                    "operationId": "DELETE~~~test~925~item~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                },
                "get": {
                    "operationId": "GET~~~test~925~item~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                },
                "post": {
                    "operationId": "POST~~~test~925~item~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                },
                "put": {
                    "operationId": "PUT~~~test~925~item~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                },
            }
        },
    }
    run_asserts(response, expected)


@pytest.mark.xfail(reason="This works when in use by a single app, it seems that testing it needs more work")
def test_show_unused_tag_v1(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_show_unused_tag_v1", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/1033/getitem/<an_id:int>")
    @doc.tag("Tag 1 - used")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def get_item(_, an_id: int):
        return sanic.response.json(locals())

    @app.put("/test/1041/putitem/<an_id:int>")
    @doc.tag("Tag 1 - used")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def put_item(_, an_id: int):
        return sanic.response.json(locals())

    @app.post("/test/1049/postitem/<an_id:int>")
    @doc.tag("Tag 1 - used")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def post_item(_, an_id: int):
        return sanic.response.json(locals())

    @app.delete("/test/1057/deleteitem/<an_id:int>")
    @doc.tag("Tag 2 - not used")
    @doc.exclude()
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def delete_item(_, an_id: int):
        return sanic.response.json(locals())

    # noinspection PyProtectedMember
    spec = sanic_openapi3e.openapi._build_openapi_spec(
        app, hide_openapi_self=True, hide_excluded=True, show_unused_tags=True
    )
    expected = {
        "info": {"description": "Description", "title": "API", "version": "1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/getitem/{an_id}": {
                "get": {
                    "operationId": "test_openapi3e::get_item",
                    "parameters": [{"in": "path", "name": "an_id", "required": true, "schema": {"type": "integer"},}],
                    "responses": {"200": {"description": "Success"}},
                }
            },
            "/test/postitem/{an_id}": {
                "post": {
                    "operationId": "test_openapi3e::post_item",
                    "parameters": [{"in": "path", "name": "an_id", "required": true, "schema": {"type": "integer"},}],
                    "responses": {"200": {"description": "Success"}},
                }
            },
            "/test/putitem/{an_id}": {
                "put": {
                    "operationId": "test_openapi3e::put_item",
                    "parameters": [{"in": "path", "name": "an_id", "required": true, "schema": {"type": "integer"},}],
                    "responses": {"200": {"description": "Success"}},
                }
            },
        },
    }

    run_asserts(spec, expected)


@pytest.mark.xfail(reason="This works when in use by a single app, it seems that testing it needs more work")
def test_show_unused_tag_v2(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_show_unused_tag_v2", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/1131/getitem/<an_id:int>")
    @doc.tag("Tag 1 - used")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def get_item(_, an_id: int):
        return sanic.response.json(locals())

    @app.put("/test/1139/putitem/<an_id:int>")
    @doc.tag("Tag 1 - used")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def put_item(_, an_id: int):
        return sanic.response.json(locals())

    @app.post("/test/1147/postitem/<an_id:int>")
    @doc.tag("Tag 1 - used")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def post_item(_, an_id: int):
        return sanic.response.json(locals())

    @app.delete("/test/1155/deleteitem/<an_id:int>")
    @doc.tag("Tag 2 - not used")
    @doc.exclude()
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def delete_item(_, an_id: int):
        return sanic.response.json(locals())

    # noinspection PyProtectedMember
    spec = sanic_openapi3e.openapi._build_openapi_spec(
        app, hide_openapi_self=True, hide_excluded=True, show_unused_tags=True
    )
    expected = {
        "info": {"description": "Description", "title": "API", "version": "1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/getitem/{an_id}": {
                "get": {
                    "operationId": "test_openapi3e::get_item",
                    "parameters": [{"in": "path", "name": "an_id", "required": true, "schema": {"type": "integer"},}],
                    "responses": {"200": {"description": "Success"}},
                }
            },
            "/test/postitem/{an_id}": {
                "post": {
                    "operationId": "test_openapi3e::post_item",
                    "parameters": [{"in": "path", "name": "an_id", "required": true, "schema": {"type": "integer"},}],
                    "responses": {"200": {"description": "Success"}},
                }
            },
            "/test/putitem/{an_id}": {
                "put": {
                    "operationId": "test_openapi3e::put_item",
                    "parameters": [{"in": "path", "name": "an_id", "required": true, "schema": {"type": "integer"},}],
                    "responses": {"200": {"description": "Success"}},
                }
            },
        },
    }

    run_asserts(spec, expected)

    print("Now with show_unused_tags=False")
    # noinspection PyProtectedMember
    spec = sanic_openapi3e.openapi._build_openapi_spec(
        app,
        hide_openapi_self=True,
        hide_excluded=True,
        show_unused_tags=False,  # <<-- notice show_unused_tags is False
    )
    expected = {
        "info": {"description": "Description", "title": "API", "version": "1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/item/{an_id}": {
                "get": {
                    "operationId": "test_openapi3e::get_item",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                    "tags": ["Tag 1 - used"],
                },
                "post": {
                    "operationId": "test_openapi3e::post_item",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                    "tags": ["Tag 1 - used"],
                },
                "put": {
                    "operationId": "test_openapi3e::put_item",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                    "tags": ["Tag 1 - used"],
                },
            }
        },
        "tags": [{"name": "Tag 1 - used"}],
    }

    run_asserts(spec, expected)


def test_path_param_w_reference(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path_param_w_reference", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)
    schemas = {
        "int.min4": sanic_openapi3e.oas_types.Schema(
            title="int.min4", _type="integer", _format="int32", minimum=4, description="Minimum: 4",
        )
    }
    components = sanic_openapi3e.oas_types.Components(schemas=schemas)
    app.config.OPENAPI_COMPONENTS = components
    int_min_4_ref = sanic_openapi3e.oas_types.Reference("#/components/schemas/int.min4")

    @app.get("/examples/1300/test_id_min/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, _in="path", schema=int_min_4_ref,
    )
    def test_id_min(request, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    assert response.json["components"]["schemas"]["int.min4"], response.json
    assert response.json["paths"]["/examples/1300/test_id_min/{an_id}"]["get"]["parameters"][0]["schema"] == {
        "$ref": "#/components/schemas/int.min4"
    }


#######################################################################################################################
# POST


def test_post_with_body(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    assert openapi
    app = Sanic("test_post_with_body", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.post("/examples/1335/test_post")
    @doc.request_body(
        description="some content", content={"application/json": {}}, required=True,
    )
    def test_id_min(request):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    assert response.json


def test_camel_case_operation_id(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_camel_case_operation_id", strict_slashes=strict_slashes)
    app.config.OPENAPI_OPERATION_ID_FN = sanic_openapi3e.openapi.camel_case_operation_id_fn  # <<-- item under test

    app.blueprint(openapi_blueprint)

    @app.get("/test/1523/path_exclude/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID w/ desx", choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    def get_test_line_path_element(_, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/1523/path_exclude/{an_id}": {
                "get": {
                    "operationId": "getTestLinePathElement",
                    "parameters": [
                        {
                            "description": "An ID w/ desx",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                }
            }
        },
    }

    run_asserts(response, expected)


def test_camel_case_operation_id_for_composite_view(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_camel_case_operation_id_for_composite_view", strict_slashes=strict_slashes)
    app.config.OPENAPI_OPERATION_ID_FN = sanic_openapi3e.openapi.camel_case_operation_id_fn  # <<-- item under test

    app.blueprint(openapi_blueprint)

    @app.route("/test/1570/path_exclude/<an_id:int>", {"GET", "PUT", "delete"})
    @doc.parameter(
        name="an_id", description="An ID w/ desx", choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    def test_line_path_element(_, an_id: int):
        return sanic.response.json(locals())

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/1570/path_exclude/{an_id}": {
                "delete": {
                    "operationId": "deleteTestLinePathElement",
                    "parameters": [
                        {
                            "description": "An ID w/ desx",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                },
                "get": {
                    "operationId": "getTestLinePathElement",
                    "parameters": [
                        {
                            "description": "An ID w/ desx",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                },
                "put": {
                    "operationId": "putTestLinePathElement",
                    "parameters": [
                        {
                            "description": "An ID w/ desx",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"enum": [1, 3, 5, 7, 11, 13], "type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "401": {"$ref": "#/components/responses/401"},
                        "403": {"$ref": "#/components/responses/403"},
                        "404": {"$ref": "#/components/responses/404"},
                        "405": {"$ref": "#/components/responses/405"},
                        "410": {"$ref": "#/components/responses/410"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                },
            }
        },
    }

    run_asserts(response, expected)


@pytest.mark.skipif("sys.version_info < (3, 7)")
def test_schemas_are_listed_alphabetically(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_schemas_are_listed_alphabetically", strict_slashes=strict_slashes)
    app.config.OPENAPI_OPERATION_ID_FN = sanic_openapi3e.openapi.camel_case_operation_id_fn

    app.blueprint(openapi_blueprint)
    days_of_week = doc.Schema(
        _type="string",
        description="Days of the week, short, English",
        enum=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    )
    schemas = {
        "int.min4": doc.Schema(
            title="int.min4", _type="integer", _format="int32", minimum=4, description="Minimum: 4",
        ),
        "days": days_of_week,
    }
    components = doc.Components(schemas=schemas)
    app.config.OPENAPI_COMPONENTS = components
    int_min_4_ref = doc.Reference("#/components/schemas/int.min4")
    dow_ref = doc.Reference("#/components/schemas/days")

    @app.get("/simple/01/from/<start>/to/<end>/in/<hops:int>")
    @doc.parameter(name="start", description="Start day", required=True, _in="path", schema=dow_ref)
    @doc.parameter(name="end", description="End day", required=True, _in="path", schema=dow_ref)
    @doc.parameter(
        name="hops", description="hops to use", required=True, _in="path", schema=int_min_4_ref,
    )
    @doc.tag("Tag 1", description="Tag 1 desc")
    @doc.tag("Tag 2", description="Tag 2 desc")
    def get_start_end_hops(request, start: str, end: str, hops: int):
        d = locals()
        del d["request"]  # not JSON serializable
        return sanic.response.json(d)

    _, response = app.test_client.get("/openapi/spec.json")

    resp_components = response.json["components"]
    resp_components_schemas = resp_components["schemas"]
    assert list(resp_components_schemas.keys()) == ["days", "int.min4"], resp_components_schemas


def test_yaml_spec(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_yaml_spec", strict_slashes=strict_slashes)
    app.config.OPENAPI_OPERATION_ID_FN = sanic_openapi3e.openapi.camel_case_operation_id_fn

    app.blueprint(openapi_blueprint)

    int_min_4 = doc.Schema(_type="integer", _format="int32", minimum=4, description="Minimum value: 4")
    an_id_ex1 = doc.Example(summary="A small number", description="Desc: Numbers less than ten", value=7)
    an_id_ex2 = doc.Example(
        summary="A big number", description="Desc: Numbers more than one million!", value=123456789,
    )
    days_of_week = doc.Schema(
        _type="string",
        description="Days of the week, short, English",
        enum=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    )

    app = Sanic(name=__file__, strict_slashes=True)
    app.blueprint(openapi_blueprint)

    schemas = {
        "str.min4": doc.Schema(title="str.min4", _type="string", minimum=4, description="A string of len >= 4",),
        "int.min4": doc.Schema(
            title="int.min4", _type="integer", _format="int32", minimum=4, description="Minimum: 4",
        ),
    }
    components = doc.Components(schemas=schemas)
    app.config.OPENAPI_COMPONENTS = components
    app.config.SHOW_OPENAPI_EXCLUDED = True
    int_min_4_ref = doc.Reference("#/components/schemas/int.min4")

    @app.get("/41/test_id/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, _in="path", schema=doc.Schema.Integer,
    )
    @doc.tag("Tag 1", description="A tag desc")
    def test_id(request, an_id: int):
        d = locals()
        del d["request"]  # not JSON serializable
        return sanic.response.json(d)

    @app.get("/47/test_id_min/<an_id:int>")
    @doc.parameter(name="an_id", description="An ID", required=True, _in="path", schema=int_min_4_ref)
    @doc.response("200", description="You got a 200!", headers={"x-prize": doc.Header(description="free money")})
    def test_id_min(request, an_id: int):
        d = locals()
        del d["request"]  # not JSON serializable
        return sanic.response.json(d)

    @app.get("/55/test_id_examples/<an_id:int>")
    @doc.parameter(
        name="an_id",
        description="An ID",
        required=True,
        _in="path",
        schema=int_min_4,
        examples={"small": an_id_ex1, "big": an_id_ex2},
    )
    @doc.summary("A path with parameter examples")
    @doc.description(
        "Unfortunately, the swagger UIs do not show the examples, but you can see them here:\n\n`{}`".format(
            {"small": an_id_ex1, "big": an_id_ex2}
        )
    )
    def test_id_examples(request, an_id: int):
        d = locals()
        del d["request"]  # not JSON serializable
        return sanic.response.json(d)

    @app.get("/74/test_path__deprecated/<an_id:int>/<another>")
    @doc.parameter(
        name="an_id",
        description="An ID",
        required=True,
        _in="path",
        schema=int_min_4,
        examples={"small": an_id_ex1, "big": an_id_ex2},
    )
    @doc.summary("A path with parameter examples")
    @doc.description("This should be marked as being deprecated")
    @doc.deprecated()
    def path__deprecated(request, an_id: int, another: str):
        d = locals()
        del d["request"]  # not JSON serializable
        return sanic.response.json(d)

    @app.get("/1760/test_parameter__deprecated/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, _in="path", deprecated=True, schema=doc.Schema.Integer,
    )
    @doc.summary("A path deprecated parameter")
    @doc.description("The parameter should be marked as deprecated")
    def param__deprecated(request, an_id: int):
        d = locals()
        del d["request"]  # not JSON serializable
        return sanic.response.json(d)

    @app.get("/100/excluded-route")
    @doc.summary("An excluded path")
    @doc.description("The parameter should not be seen in the spec")
    @doc.exclude()
    def path__excluded(request):
        d = locals()
        del d["request"]  # not JSON serializable
        return sanic.response.json(d)

    @app.get("/109/some_ids")
    @doc.parameter(
        name="ids",
        description="Some IDs",
        required=True,
        choices=[1, 3, 5, 7, 11, 13],
        _in="query",
        schema=doc.Schema.Integers,
    )
    def test_some_ids(request: sanic.request.Request):
        query = request.query_string
        return sanic.response.json(query)

    @app.post("/123/post_some_ids")
    @doc.parameter(
        name="ids",
        description="Some IDs",
        required=True,
        choices=[1, 3, 5, 7, 11, 13],
        _in="query",
        schema=doc.Schema.Integers,
    )
    def test_post_some_ids(request: sanic.request.Request):
        query = request.query_string
        return sanic.response.json(query)

    @app.put("/137/put_some_ids")
    @doc.parameter(
        name="ids",
        description="Some IDs",
        required=True,
        choices=[1, 3, 5, 7, 11, 13],
        _in="query",
        schema=doc.Schema.Integers,
    )
    def test_put_some_ids(request: sanic.request.Request):
        query = request.query_string
        return sanic.response.json(query)

    @app.options("/151/options_some_ids")
    @doc.parameter(
        name="ids",
        description="Some IDs",
        required=True,
        choices=[1, 3, 5, 7, 11, 13],
        _in="query",
        schema=doc.Schema.Integers,
    )
    def test_options_some_ids(request: sanic.request.Request):
        query = request.query_string
        return sanic.response.json(query)

    @app.delete("/165/delete_some_ids")
    @doc.parameter(
        name="ids",
        description="Some IDs",
        required=True,
        choices=[1, 3, 5, 7, 11, 13],
        _in="query",
        schema=doc.Schema.Integers,
    )
    def test_delete_some_ids(request: sanic.request.Request):
        query = request.query_string
        return sanic.response.json(query)

    @app.head("/179/head_some_ids")
    @doc.parameter(
        name="ids",
        description="Some IDs",
        required=True,
        choices=[1, 3, 5, 7, 11, 13],
        _in="query",
        schema=doc.Schema.Integers,
    )
    def test_head_some_ids(request: sanic.request.Request):
        query = request.query_string
        return sanic.response.json(query)

    @app.patch("/194/patch_some_ids")
    @doc.parameter(
        name="ids",
        description="Some IDs",
        required=True,
        choices=[1, 3, 5, 7, 11, 13],
        _in="query",
        schema=doc.Schema.Integers,
    )
    def test_patch_some_ids(request: sanic.request.Request):
        query = request.query_string
        return sanic.response.json(query)

    @app.patch("/test/excluded_path_with_unique_tag")
    @doc.tag("a unique, but should not be seen, tag")
    @doc.exclude()
    def excluded_path_with_unique_tag(_):
        return sanic.response.json({})

    _, response = app.test_client.get("/openapi/spec.yml")

    assert response.content.decode("utf8").splitlines() == [
        """openapi: 3.0.2""",
        """info:""",
        """  title: API""",
        """  version: v1.0.0""",
        """  description: Description""",
        """paths:""",
        """  /41/test_id/{an_id}:""",
        """    get:""",
        """      tags:""",
        """      - Tag 1""",
        """      operationId: GET~~~41~test_id~an_id""",
        """      parameters:""",
        """      - name: an_id""",
        """        description: An ID""",
        """        in: path""",
        """        required: true""",
        """        schema:""",
        """          type: integer""",
        """      responses:""",
        """        '200':""",
        """          $ref: '#/components/responses/200'""",
        """        '400':""",
        """          $ref: '#/components/responses/400'""",
        """        '401':""",
        """          $ref: '#/components/responses/401'""",
        """        '403':""",
        """          $ref: '#/components/responses/403'""",
        """        '404':""",
        """          $ref: '#/components/responses/404'""",
        """        '405':""",
        """          $ref: '#/components/responses/405'""",
        """        '410':""",
        """          $ref: '#/components/responses/410'""",
        """        '500':""",
        """          $ref: '#/components/responses/500'""",
        """  /47/test_id_min/{an_id}:""",
        """    get:""",
        """      operationId: GET~~~47~test_id_min~an_id""",
        """      parameters:""",
        """      - name: an_id""",
        """        description: An ID""",
        """        in: path""",
        """        required: true""",
        """        schema:""",
        """          $ref: '#/components/schemas/int.min4'""",
        """      responses:""",
        """        '200':""",
        """          description: You got a 200!""",
        """          headers:""",
        """            x-prize:""",
        """              description: free money""",
        """        '400':""",
        """          $ref: '#/components/responses/400'""",
        """        '401':""",
        """          $ref: '#/components/responses/401'""",
        """        '403':""",
        """          $ref: '#/components/responses/403'""",
        """        '404':""",
        """          $ref: '#/components/responses/404'""",
        """        '405':""",
        """          $ref: '#/components/responses/405'""",
        """        '410':""",
        """          $ref: '#/components/responses/410'""",
        """        '500':""",
        """          $ref: '#/components/responses/500'""",
        """  /55/test_id_examples/{an_id}:""",
        """    get:""",
        """      summary: A path with parameter examples""",
        """      description: 'Unfortunately, the swagger UIs do not show the examples, but you""",
        """        can see them here:""",
        """""",
        """""",
        """        `{''small'': Example{"description": "Desc: Numbers less than ten", "summary":""",
        """        "A small number", "value": 7}, ''big'': Example{"description": "Desc: Numbers""",
        """        more than one million!", "summary": "A big number", "value": 123456789}}`'""",
        """      operationId: GET~~~55~test_id_examples~an_id""",
        """      parameters:""",
        """      - name: an_id""",
        """        description: An ID""",
        """        in: path""",
        """        required: true""",
        """        schema:""",
        """          minimum: 4""",
        """          type: integer""",
        """          description: 'Minimum value: 4'""",
        """          format: int32""",
        """        examples:""",
        """          small:""",
        """            summary: A small number""",
        """            description: 'Desc: Numbers less than ten'""",
        """            value: 7""",
        """          big:""",
        """            summary: A big number""",
        """            description: 'Desc: Numbers more than one million!'""",
        """            value: 123456789""",
        """      responses:""",
        """        '200':""",
        """          $ref: '#/components/responses/200'""",
        """        '400':""",
        """          $ref: '#/components/responses/400'""",
        """        '401':""",
        """          $ref: '#/components/responses/401'""",
        """        '403':""",
        """          $ref: '#/components/responses/403'""",
        """        '404':""",
        """          $ref: '#/components/responses/404'""",
        """        '405':""",
        """          $ref: '#/components/responses/405'""",
        """        '410':""",
        """          $ref: '#/components/responses/410'""",
        """        '500':""",
        """          $ref: '#/components/responses/500'""",
        """  /74/test_path__deprecated/{an_id}/{another}:""",
        """    get:""",
        """      summary: A path with parameter examples""",
        """      description: This should be marked as being deprecated""",
        """      operationId: GET~~~74~test_path__deprecated~an_id~another""",
        """      parameters:""",
        """      - name: an_id""",
        """        description: An ID""",
        """        in: path""",
        """        required: true""",
        """        schema:""",
        """          minimum: 4""",
        """          type: integer""",
        """          description: 'Minimum value: 4'""",
        """          format: int32""",
        """        examples:""",
        """          small:""",
        """            summary: A small number""",
        """            description: 'Desc: Numbers less than ten'""",
        """            value: 7""",
        """          big:""",
        """            summary: A big number""",
        """            description: 'Desc: Numbers more than one million!'""",
        """            value: 123456789""",
        """      - name: another""",
        """        in: path""",
        """        required: true""",
        """        schema:""",
        """          type: string""",
        """      responses:""",
        """        '200':""",
        """          $ref: '#/components/responses/200'""",
        """        '400':""",
        """          $ref: '#/components/responses/400'""",
        """        '401':""",
        """          $ref: '#/components/responses/401'""",
        """        '403':""",
        """          $ref: '#/components/responses/403'""",
        """        '404':""",
        """          $ref: '#/components/responses/404'""",
        """        '405':""",
        """          $ref: '#/components/responses/405'""",
        """        '410':""",
        """          $ref: '#/components/responses/410'""",
        """        '500':""",
        """          $ref: '#/components/responses/500'""",
        """      deprecated: true""",
        """  /1760/test_parameter__deprecated/{an_id}:""",
        """    get:""",
        """      summary: A path deprecated parameter""",
        """      description: The parameter should be marked as deprecated""",
        """      operationId: GET~~~1760~test_parameter__deprecated~an_id""",
        """      parameters:""",
        """      - name: an_id""",
        """        description: An ID""",
        """        in: path""",
        """        required: true""",
        """        deprecated: true""",
        """        schema:""",
        """          type: integer""",
        """      responses:""",
        """        '200':""",
        """          $ref: '#/components/responses/200'""",
        """        '400':""",
        """          $ref: '#/components/responses/400'""",
        """        '401':""",
        """          $ref: '#/components/responses/401'""",
        """        '403':""",
        """          $ref: '#/components/responses/403'""",
        """        '404':""",
        """          $ref: '#/components/responses/404'""",
        """        '405':""",
        """          $ref: '#/components/responses/405'""",
        """        '410':""",
        """          $ref: '#/components/responses/410'""",
        """        '500':""",
        """          $ref: '#/components/responses/500'""",
        """  /109/some_ids:""",
        """    get:""",
        """      operationId: GET~~~109~some_ids""",
        """      parameters:""",
        """      - name: ids""",
        """        description: Some IDs""",
        """        in: query""",
        """        required: true""",
        """        schema:""",
        """          enum:""",
        """          - 1""",
        """          - 3""",
        """          - 5""",
        """          - 7""",
        """          - 11""",
        """          - 13""",
        """          type: array""",
        """          items:""",
        """            type: integer""",
        """      responses:""",
        """        '200':""",
        """          $ref: '#/components/responses/200'""",
        """        '400':""",
        """          $ref: '#/components/responses/400'""",
        """        '401':""",
        """          $ref: '#/components/responses/401'""",
        """        '403':""",
        """          $ref: '#/components/responses/403'""",
        """        '404':""",
        """          $ref: '#/components/responses/404'""",
        """        '405':""",
        """          $ref: '#/components/responses/405'""",
        """        '410':""",
        """          $ref: '#/components/responses/410'""",
        """        '500':""",
        """          $ref: '#/components/responses/500'""",
        """  /123/post_some_ids:""",
        """    post:""",
        """      operationId: POST~~~123~post_some_ids""",
        """      parameters:""",
        """      - name: ids""",
        """        description: Some IDs""",
        """        in: query""",
        """        required: true""",
        """        schema:""",
        """          enum:""",
        """          - 1""",
        """          - 3""",
        """          - 5""",
        """          - 7""",
        """          - 11""",
        """          - 13""",
        """          type: array""",
        """          items:""",
        """            type: integer""",
        """      responses:""",
        """        '200':""",
        """          $ref: '#/components/responses/200'""",
        """        '400':""",
        """          $ref: '#/components/responses/400'""",
        """        '401':""",
        """          $ref: '#/components/responses/401'""",
        """        '403':""",
        """          $ref: '#/components/responses/403'""",
        """        '404':""",
        """          $ref: '#/components/responses/404'""",
        """        '405':""",
        """          $ref: '#/components/responses/405'""",
        """        '410':""",
        """          $ref: '#/components/responses/410'""",
        """        '500':""",
        """          $ref: '#/components/responses/500'""",
        """  /137/put_some_ids:""",
        """    put:""",
        """      operationId: PUT~~~137~put_some_ids""",
        """      parameters:""",
        """      - name: ids""",
        """        description: Some IDs""",
        """        in: query""",
        """        required: true""",
        """        schema:""",
        """          enum:""",
        """          - 1""",
        """          - 3""",
        """          - 5""",
        """          - 7""",
        """          - 11""",
        """          - 13""",
        """          type: array""",
        """          items:""",
        """            type: integer""",
        """      responses:""",
        """        '200':""",
        """          $ref: '#/components/responses/200'""",
        """        '400':""",
        """          $ref: '#/components/responses/400'""",
        """        '401':""",
        """          $ref: '#/components/responses/401'""",
        """        '403':""",
        """          $ref: '#/components/responses/403'""",
        """        '404':""",
        """          $ref: '#/components/responses/404'""",
        """        '405':""",
        """          $ref: '#/components/responses/405'""",
        """        '410':""",
        """          $ref: '#/components/responses/410'""",
        """        '500':""",
        """          $ref: '#/components/responses/500'""",
        """  /151/options_some_ids:""",
        """    options:""",
        """      operationId: OPTIONS~~~151~options_some_ids""",
        """      parameters:""",
        """      - name: ids""",
        """        description: Some IDs""",
        """        in: query""",
        """        required: true""",
        """        schema:""",
        """          enum:""",
        """          - 1""",
        """          - 3""",
        """          - 5""",
        """          - 7""",
        """          - 11""",
        """          - 13""",
        """          type: array""",
        """          items:""",
        """            type: integer""",
        """      responses:""",
        """        '200':""",
        """          $ref: '#/components/responses/200'""",
        """        '400':""",
        """          $ref: '#/components/responses/400'""",
        """        '401':""",
        """          $ref: '#/components/responses/401'""",
        """        '403':""",
        """          $ref: '#/components/responses/403'""",
        """        '404':""",
        """          $ref: '#/components/responses/404'""",
        """        '405':""",
        """          $ref: '#/components/responses/405'""",
        """        '410':""",
        """          $ref: '#/components/responses/410'""",
        """        '500':""",
        """          $ref: '#/components/responses/500'""",
        """  /165/delete_some_ids:""",
        """    delete:""",
        """      operationId: DELETE~~~165~delete_some_ids""",
        """      parameters:""",
        """      - name: ids""",
        """        description: Some IDs""",
        """        in: query""",
        """        required: true""",
        """        schema:""",
        """          enum:""",
        """          - 1""",
        """          - 3""",
        """          - 5""",
        """          - 7""",
        """          - 11""",
        """          - 13""",
        """          type: array""",
        """          items:""",
        """            type: integer""",
        """      responses:""",
        """        '200':""",
        """          $ref: '#/components/responses/200'""",
        """        '400':""",
        """          $ref: '#/components/responses/400'""",
        """        '401':""",
        """          $ref: '#/components/responses/401'""",
        """        '403':""",
        """          $ref: '#/components/responses/403'""",
        """        '404':""",
        """          $ref: '#/components/responses/404'""",
        """        '405':""",
        """          $ref: '#/components/responses/405'""",
        """        '410':""",
        """          $ref: '#/components/responses/410'""",
        """        '500':""",
        """          $ref: '#/components/responses/500'""",
        """  /179/head_some_ids:""",
        """    head:""",
        """      operationId: HEAD~~~179~head_some_ids""",
        """      parameters:""",
        """      - name: ids""",
        """        description: Some IDs""",
        """        in: query""",
        """        required: true""",
        """        schema:""",
        """          enum:""",
        """          - 1""",
        """          - 3""",
        """          - 5""",
        """          - 7""",
        """          - 11""",
        """          - 13""",
        """          type: array""",
        """          items:""",
        """            type: integer""",
        """      responses:""",
        """        '200':""",
        """          $ref: '#/components/responses/200'""",
        """        '400':""",
        """          $ref: '#/components/responses/400'""",
        """        '401':""",
        """          $ref: '#/components/responses/401'""",
        """        '403':""",
        """          $ref: '#/components/responses/403'""",
        """        '404':""",
        """          $ref: '#/components/responses/404'""",
        """        '405':""",
        """          $ref: '#/components/responses/405'""",
        """        '410':""",
        """          $ref: '#/components/responses/410'""",
        """        '500':""",
        """          $ref: '#/components/responses/500'""",
        """  /194/patch_some_ids:""",
        """    patch:""",
        """      operationId: PATCH~~~194~patch_some_ids""",
        """      parameters:""",
        """      - name: ids""",
        """        description: Some IDs""",
        """        in: query""",
        """        required: true""",
        """        schema:""",
        """          enum:""",
        """          - 1""",
        """          - 3""",
        """          - 5""",
        """          - 7""",
        """          - 11""",
        """          - 13""",
        """          type: array""",
        """          items:""",
        """            type: integer""",
        """      responses:""",
        """        '200':""",
        """          $ref: '#/components/responses/200'""",
        """        '400':""",
        """          $ref: '#/components/responses/400'""",
        """        '401':""",
        """          $ref: '#/components/responses/401'""",
        """        '403':""",
        """          $ref: '#/components/responses/403'""",
        """        '404':""",
        """          $ref: '#/components/responses/404'""",
        """        '405':""",
        """          $ref: '#/components/responses/405'""",
        """        '410':""",
        """          $ref: '#/components/responses/410'""",
        """        '500':""",
        """          $ref: '#/components/responses/500'""",
        """components:""",
        """  schemas:""",
        """    int.min4:""",
        """      description: 'Minimum: 4'""",
        """      format: int32""",
        """      minimum: 4""",
        """      title: int.min4""",
        """      type: integer""",
        """    str.min4:""",
        """      description: A string of len >= 4""",
        """      minimum: 4""",
        """      title: str.min4""",
        """      type: string""",
        """  responses:""",
        """    '200':""",
        """      description: OK""",
        """    '400':""",
        """      description: Bad Request""",
        """    '401':""",
        """      description: Unauthorized""",
        """    '403':""",
        """      description: Forbidden""",
        """    '404':""",
        """      description: Not Found""",
        """    '405':""",
        """      description: Method Not Allowed""",
        """    '410':""",
        """      description: Gone""",
        """    '500':""",
        """      description: Internal Server Error""",
        """tags:""",
        """- name: Tag 1""",
        """  description: A tag desc""",
    ]
