from typing import Dict, List, Optional, Union

import sanic.request
import sanic.response
from sanic import Sanic

from tests.conftest import false, run_asserts, strict_slashes, true


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
                "404": {"description": "Not Found"},
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
                        "404": {"$ref": "#/components/responses/404"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                }
            }
        },
    }

    run_asserts(response, expected)


def test_multiple_responses(openapi__mod_bp_doc):
    openapi_mod, openapi_blueprint, doc = openapi__mod_bp_doc

    schemas: Optional[Dict[str, Union[doc.Schema, doc.Reference]]] = {
        "str.min4": doc.Schema(title="str.min4", _type="string", minimum=4, description="A string of len >= 4",),
        "int.min4": doc.Schema(
            title="int.min4", _type="integer", _format="int32", minimum=4, description="Minimum: 4",
        ),
    }
    components = doc.Components(schemas=schemas)
    security: List[doc.SecurityRequirement] = [doc.SecurityRequirement({"bearerAuth": []})]
    responses_200only = doc.Responses({"200": doc.Reference("#/components/responses/200")}, no_defaults=True)

    app = Sanic(name=__file__, strict_slashes=True)
    app.blueprint(openapi_blueprint)

    app.config.API_TITLE = __file__
    app.config.API_DESCRIPTION = "This has an example adding multiple responses in a single `@doc.responses` call"
    app.config.OPENAPI_COMPONENTS = components
    app.config.OPENAPI_SECURITY = security

    @app.get("/object/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, _in="path", schema=doc.Schema.Integer,
    )
    @doc.tag("Tag 1", description="A tag desc")
    @doc.responses(
        {
            200: {"r": doc.Reference("#/components/responses/200")},
            404: {"d": "Not there", "h": None, "c": None, "l": None},
            401: {},
            403: {"d": None},
            405: None,
            410: None,
            500: None,
        }
    )
    def get_id(request, an_id: int):
        d = locals()
        del d["request"]  # not JSON serializable
        return sanic.response.json(d)

    @app.get("/object2/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, _in="path", schema=doc.Schema.Integer,
    )
    @doc.tag("Tag 1", description="A tag desc")
    @doc.responses(responses_200only)
    def get_id2(request, an_id: int):
        d = locals()
        del d["request"]  # not JSON serializable
        return sanic.response.json(d)

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "components": {
            "responses": {
                "200": {"description": "OK"},
                "400": {"description": "Bad Request"},
                "404": {"description": "Not Found"},
                "500": {"description": "Internal Server Error"},
            },
            "schemas": {
                "int.min4": {
                    "description": "Minimum: 4",
                    "format": "int32",
                    "minimum": 4,
                    "title": "int.min4",
                    "type": "integer",
                },
                "str.min4": {
                    "description": "A string of len >= 4",
                    "minimum": 4,
                    "title": "str.min4",
                    "type": "string",
                },
            },
        },
        "info": {
            "description": "This has an example adding multiple responses in a single `@doc.responses` call",
            "title": "/Users/efarrell/Workspaces/github/endafarrell/sanic-openapi3e/tests/openapi3e/test_responses.py",
            "version": "v1.0.0",
        },
        "openapi": "3.0.2",
        "paths": {
            "/object/{an_id}": {
                "get": {
                    "operationId": "GET~~~object~an_id",
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
                        "404": {"description": "Not there"},
                    },
                    "tags": ["Tag 1"],
                }
            },
            "/object2/{an_id}": {
                "get": {
                    "operationId": "GET~~~object2~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {"200": {"$ref": "#/components/responses/200"}},
                    "tags": ["Tag 1"],
                }
            },
        },
        "security": [{"bearerAuth": []}],
        "tags": [{"description": "A tag desc", "name": "Tag 1"}],
    }

    run_asserts(response, expected)
