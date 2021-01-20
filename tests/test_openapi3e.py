"""Basic tests for the openapi_blueprint."""
import json

import pytest
import sanic.request
import sanic.response
from sanic import Sanic

import sanic_openapi3e.oas_types
from tests.conftest import an_id_ex1, an_id_ex2, int_min_4, run_asserts

# # Some ~static~ reusable objects
# int_min_4 = sanic_openapi3e.oas_types.Schema(
#     _type="integer", _format="int32", minimum=4, description="Minimum: 4"
# )  # type: sanic_openapi3e.oas_types.Schema
#
# an_id_ex1 = sanic_openapi3e.oas_types.Example(
#     summary="A small number", description="description: Numbers less than ten", value=7
# )  # type: sanic_openapi3e.oas_types.Example
#
# an_id_ex2 = sanic_openapi3e.oas_types.Example(
#     summary="A big number", description="description: Numbers more than one million!", value=123456789,
# )  # type: sanic_openapi3e.oas_types.Example


strict_slashes = True
true = True
false = False
null = None


# # ------------------------------------------------------------ #
# # pytest fixtures. Given that the sanic_openapi3e state is held
# # in the module, we need to have them as fixtures to avoid the
# # routes from all tests being visible together.
# #
# # While `scope="function"` is the default, it's helpful to be
# # explicitly clear about it.
# # ------------------------------------------------------------ #
#
#
# @pytest.fixture(scope="function")
# def openapi__mod_bp_doc():
#     for t_unimport in (
#         "sanic_openapi3e",
#         "sanic_openapi3e.doc",
#         "sanic_openapi3e.openapi",
#     ):
#         if t_unimport in sys.modules:
#             del sys.modules[t_unimport]
#     import sanic_openapi3e.openapi
#     from sanic_openapi3e import doc, openapi_blueprint
#
#     yield sanic_openapi3e.openapi, openapi_blueprint, doc
#
#     # The teardown - so when each function that uses this fixture has finished, these
#     # modules are uninstalled and thus they will be re-imported anew for the next use.
#     for t_unimport in (
#         "sanic_openapi3e",
#         "sanic_openapi3e.doc",
#         "sanic_openapi3e.openapi",
#     ):
#         del sys.modules[t_unimport]
#
#
# def run_asserts(
#     response: Union[
#         sanic.response.HTTPResponse, sanic.response.StreamingHTTPResponse, Dict, sanic_openapi3e.oas_types.OpenAPIv3,
#     ],
#     expected: Dict,
# ):
#     """
#     Helper to run the assert and print the values if needed.
#
#     :param response: What was returned by the test call
#     :param expected: What was expected to be returned
#
#     """
#     if isinstance(response, dict):
#         spec = response
#     elif isinstance(response, sanic_openapi3e.oas_types.OpenAPIv3):
#         spec = response.serialize()
#     else:
#         assert response.status == 200
#         spec = json.loads(response.body.decode())
#
#     if not json.dumps(spec, sort_keys=True) == json.dumps(expected, sort_keys=True):
#         print("\n   actual:", json.dumps(spec, sort_keys=True))
#         print("expected:", json.dumps(expected, sort_keys=True))
#
#     assert json.loads(json.dumps(spec, sort_keys=True)) == json.loads(json.dumps(expected, sort_keys=True))


def test_fundamentals(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_fundamentals", strict_slashes=strict_slashes,)

    app.blueprint(openapi_blueprint)

    @app.get("/test/102/anId/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, _in="path", schema=sanic_openapi3e.oas_types.Schema.Integer,
    )
    def test_id(request, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "components": {
            "responses": {
                "200": {"description": "OK"},
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden"},
                "404": {"description": "Not Found"},
                "405": {"description": "Method Not Allowed"},
                "410": {"description": "Gone"},
                "500": {"description": "Internal Server Error"},
            }
        },
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
                            "schema": {
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "nullable": false,
                                "readOnly": false,
                                "type": "integer",
                                "uniqueItems": false,
                                "writeOnly": false,
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
        return sanic.response.json(locals())  # pragma: no cover

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "components": {
            "responses": {
                "200": {"description": "OK"},
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden"},
                "404": {"description": "Not Found"},
                "405": {"description": "Method Not Allowed"},
                "410": {"description": "Gone"},
                "500": {"description": "Internal Server Error"},
            }
        },
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
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "format": "int32",
                                "minimum": 4,
                                "nullable": false,
                                "readOnly": false,
                                "type": "integer",
                                "uniqueItems": false,
                                "writeOnly": false,
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
        return sanic.response.json(locals())  # pragma: no cover

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "components": {
            "responses": {
                "200": {"description": "OK"},
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden"},
                "404": {"description": "Not Found"},
                "405": {"description": "Method Not Allowed"},
                "410": {"description": "Gone"},
                "500": {"description": "Internal Server Error"},
            }
        },
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
    app = Sanic("test_list_is_a_list_in_query", strict_slashes=strict_slashes)

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
        "components": {
            "responses": {
                "200": {"description": "OK"},
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden"},
                "404": {"description": "Not Found"},
                "405": {"description": "Method Not Allowed"},
                "410": {"description": "Gone"},
                "500": {"description": "Internal Server Error"},
            }
        },
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
                            "schema": {
                                "enum": [1, 3, 5, 7, 11, 13],
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "items": {
                                    "exclusiveMaximum": false,
                                    "exclusiveMinimum": false,
                                    "nullable": false,
                                    "readOnly": false,
                                    "type": "integer",
                                    "uniqueItems": false,
                                    "writeOnly": false,
                                },
                                "nullable": false,
                                "readOnly": false,
                                "type": "array",
                                "uniqueItems": false,
                                "writeOnly": false,
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


def test_path_without_parameter(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path_without_consumes", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/798/anId/<an_id:int>")
    def test_id(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "components": {
            "responses": {
                "200": {"description": "OK"},
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden"},
                "404": {"description": "Not Found"},
                "405": {"description": "Method Not Allowed"},
                "410": {"description": "Gone"},
                "500": {"description": "Internal Server Error"},
            }
        },
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/798/anId/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~798~anId~an_id",
                    "parameters": [
                        {
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "nullable": false,
                                "readOnly": false,
                                "type": "integer",
                                "uniqueItems": false,
                                "writeOnly": false,
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
                }
            }
        },
    }

    run_asserts(response, expected)


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
        return sanic.response.json(locals())  # pragma: no cover

    @app.get("/test/889/test_path_not_exclude/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID w/desc", choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    def path_not_exclude(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "components": {
            "responses": {
                "200": {"description": "OK"},
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden"},
                "404": {"description": "Not Found"},
                "405": {"description": "Method Not Allowed"},
                "410": {"description": "Gone"},
                "500": {"description": "Internal Server Error"},
            }
        },
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
                            "schema": {
                                "enum": [1, 3, 5, 7, 11, 13],
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "nullable": false,
                                "readOnly": false,
                                "type": "integer",
                                "uniqueItems": false,
                                "writeOnly": false,
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
        return sanic.response.json(locals())  # pragma: no cover

    @app.put("/test/925/item/<an_id:int>")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def put_item(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    @app.post("/test/925/item/<an_id:int>")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def post_item(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    @app.delete("/test/925/item/<an_id:int>")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def delete_item(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "components": {
            "responses": {
                "200": {"description": "OK"},
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden"},
                "404": {"description": "Not Found"},
                "405": {"description": "Method Not Allowed"},
                "410": {"description": "Gone"},
                "500": {"description": "Internal Server Error"},
            }
        },
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
                            "schema": {
                                "enum": [1, 3, 5, 7, 11, 13],
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "nullable": false,
                                "readOnly": false,
                                "type": "integer",
                                "uniqueItems": false,
                                "writeOnly": false,
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
                },
                "get": {
                    "operationId": "GET~~~test~925~item~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {
                                "enum": [1, 3, 5, 7, 11, 13],
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "nullable": false,
                                "readOnly": false,
                                "type": "integer",
                                "uniqueItems": false,
                                "writeOnly": false,
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
                },
                "post": {
                    "operationId": "POST~~~test~925~item~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {
                                "enum": [1, 3, 5, 7, 11, 13],
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "nullable": false,
                                "readOnly": false,
                                "type": "integer",
                                "uniqueItems": false,
                                "writeOnly": false,
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
                },
                "put": {
                    "operationId": "PUT~~~test~925~item~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {
                                "enum": [1, 3, 5, 7, 11, 13],
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "nullable": false,
                                "readOnly": false,
                                "type": "integer",
                                "uniqueItems": false,
                                "writeOnly": false,
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
                },
            }
        },
    }
    run_asserts(response, expected)


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
        return sanic.response.json(locals())  # pragma: no cover

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
        return sanic.response.json(locals())  # pragma: no cover

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "components": {
            "responses": {
                "200": {"description": "OK"},
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden"},
                "404": {"description": "Not Found"},
                "405": {"description": "Method Not Allowed"},
                "410": {"description": "Gone"},
                "500": {"description": "Internal Server Error"},
            }
        },
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
                            "schema": {
                                "enum": [1, 3, 5, 7, 11, 13],
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "nullable": false,
                                "readOnly": false,
                                "type": "integer",
                                "uniqueItems": false,
                                "writeOnly": false,
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
        return sanic.response.json(locals())  # pragma: no cover

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "components": {
            "responses": {
                "200": {"description": "OK"},
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden"},
                "404": {"description": "Not Found"},
                "405": {"description": "Method Not Allowed"},
                "410": {"description": "Gone"},
                "500": {"description": "Internal Server Error"},
            }
        },
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
                            "schema": {
                                "enum": [1, 3, 5, 7, 11, 13],
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "nullable": false,
                                "readOnly": false,
                                "type": "integer",
                                "uniqueItems": false,
                                "writeOnly": false,
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
                },
                "get": {
                    "operationId": "getTestLinePathElement",
                    "parameters": [
                        {
                            "description": "An ID w/ desx",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {
                                "enum": [1, 3, 5, 7, 11, 13],
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "nullable": false,
                                "readOnly": false,
                                "type": "integer",
                                "uniqueItems": false,
                                "writeOnly": false,
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
                },
                "put": {
                    "operationId": "putTestLinePathElement",
                    "parameters": [
                        {
                            "description": "An ID w/ desx",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {
                                "enum": [1, 3, 5, 7, 11, 13],
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "nullable": false,
                                "readOnly": false,
                                "type": "integer",
                                "uniqueItems": false,
                                "writeOnly": false,
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
        return sanic.response.json(locals())  # pragma: no cover

    _, response = app.test_client.get("/openapi/spec.json")

    resp_components = response.json["components"]
    resp_components_schemas = resp_components["schemas"]
    assert list(resp_components_schemas.keys()) == ["days", "int.min4"], resp_components_schemas
