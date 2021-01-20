from typing import Set

import sanic.response
from sanic import Sanic

from sanic_openapi3e.oas_types import (
    Contact,
    ExternalDocumentation,
    License,
    PathItem,
    Paths,
    Schema,
    Tag,
)

########################################################################################################################
# Contact
########################################################################################################################
from tests.conftest import an_id_ex1, an_id_ex2, false, int_min_4, run_asserts
from tests.test_openapi3e import strict_slashes, true


def test_contact():
    contact = Contact(name="name", url="www.url.com", email="email@url.com")
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


def test_external_documentation(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_external_documentation", strict_slashes=strict_slashes)
    app.config.OPENAPI_EXTERNAL_DOCS = ExternalDocumentation("http://wikipedia.org/", description="Fabulous resource")

    app.blueprint(openapi_blueprint)

    @app.get("/examples/44/test_external_docs/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, _in="path", schema=Schema.Integer,
    )
    @doc.summary("A path with docs")
    @doc.description("The route should have extra docs")
    @doc.external_docs("https://tools.ietf.org/html/rfc2616", description="HTTP1.1 RFC")
    def param__deprecated(request, an_id: int):
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
        "externalDocs": {"description": "Fabulous resource", "url": "http://wikipedia.org/"},
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/examples/44/test_external_docs/{an_id}": {
                "get": {
                    "description": "The route should have extra docs",
                    "externalDocs": {"description": "HTTP1.1 RFC", "url": "https://tools.ietf.org/html/rfc2616"},
                    "operationId": "GET~~~examples~44~test_external_docs~an_id",
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
                    "summary": "A path with docs",
                }
            }
        },
    }

    run_asserts(response, expected)


########################################################################################################################
# License
########################################################################################################################


def test_license():
    _license = License(name="name", url="www.url.com")
    assert _license.serialize() == {"name": "name", "url": "www.url.com"}


########################################################################################################################
# Parameter
########################################################################################################################


def test_path_integer_min(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_consumes_from_path_does_not_duplicate_parameters", strict_slashes=strict_slashes,)

    app.blueprint(openapi_blueprint)

    @app.get("/test/148/anId/<an_id:int>")
    @doc.parameter(name="an_id", description="An ID", required=True, _in="path", schema=int_min_4)
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
            "/test/148/anId/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~148~anId~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
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
        schema=Schema.Integer,
        deprecated=True,  # <<-- detail under test
    )
    @doc.summary("A path deprecated parameter")
    @doc.description("The parameter should be marked as deprecated")
    def param__deprecated(request, an_id: int):
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
                    "summary": "A path deprecated parameter",
                }
            }
        },
    }

    run_asserts(response, expected)


########################################################################################################################
# Paths, PathItem
########################################################################################################################


def test_pathitem():
    pi = PathItem(x_exclude=True)
    assert pi.x_exclude

    ps = Paths([("test_pathitem", pi)])
    pi = ps["test_pathitem"]
    assert pi.x_exclude


def test_schema():
    assert Schema(_type="string").as_yamlable_object() == {
        "exclusiveMaximum": False,
        "exclusiveMinimum": False,
        "nullable": False,
        "readOnly": False,
        "type": "string",
        "uniqueItems": False,
        "writeOnly": False,
    }


def test_schema_integer():
    assert Schema.Integer.as_yamlable_object() == {
        "exclusiveMaximum": False,
        "exclusiveMinimum": False,
        "nullable": False,
        "readOnly": False,
        "type": "integer",
        "uniqueItems": False,
        "writeOnly": False,
    }


def test_schema_integer_w_choices():
    schema = Schema.Integer.clone()
    schema.add_enum([1, 2, 3])
    assert schema.as_yamlable_object() == {
        "enum": [1, 2, 3],
        "exclusiveMaximum": False,
        "exclusiveMinimum": False,
        "nullable": False,
        "readOnly": False,
        "type": "integer",
        "uniqueItems": False,
        "writeOnly": False,
    }


########################################################################################################################
# Tag
########################################################################################################################


def test_tag_eq():
    tag = Tag("name", "desc")
    assert tag == tag
    assert tag == Tag("name", "desc")


def test_set_of_tags():
    tags: Set[Tag] = set()
    tags.add(Tag("name", "desc"))
    tags.add(Tag("name", "desc"))
    assert len(tags) == 1, tags


def test_sorted_tags():
    tags: Set[Tag] = set()
    tags.add(Tag("nameB", "descB"))
    tags.add(Tag("nameA", "descA"))
    assert sorted(tags) == [Tag("nameA", "descA"), Tag("nameB", "descB")]
