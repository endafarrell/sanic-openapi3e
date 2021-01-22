import random
from typing import List

import sanic.request
import sanic.response
from sanic import Sanic

from tests.conftest import false, run_asserts, true


def test_security_override(openapi__mod_bp_doc):
    openapi_mod, openapi_blueprint, doc = openapi__mod_bp_doc

    int_min_4_ref = doc.Reference("#/components/schemas/int.min4")

    schemas = {
        "str.min4": doc.Schema(title="str.min4", _type="string", minimum=4, description="A string of len >= 4",),
        "int.min4": doc.Schema(
            title="int.min4", _type="integer", _format="int32", minimum=4, description="Minimum: 4",
        ),
    }
    components = doc.Components(schemas=schemas)
    security: List[doc.SecurityRequirement] = [doc.SecurityRequirement({"bearerAuth": []})]

    app = Sanic(name=__file__, strict_slashes=True)
    app.blueprint(openapi_blueprint)

    app.config.API_TITLE = __file__
    app.config.API_DESCRIPTION = "This file has a simple example adding security "
    app.config.OPENAPI_COMPONENTS = components
    app.config.OPENAPI_SECURITY = security
    app.config.API_LICENSE_NAME = "A license name"
    app.config.API_LICENSE_URL = "https://license.url"
    app.config.API_CONTACT_NAME = "developer"
    app.config.API_CONTACT_URL = "https://developer.dev"

    @app.get("/object/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, _in="path", schema=doc.Schema.Integer,
    )
    @doc.tag("Tag 1", description="A tag desc")
    @doc.security([])
    def get_id(request, an_id: int):
        d = locals()
        del d["request"]  # not JSON serializable
        return sanic.response.json(d)

    @app.head("/object/<an_id:int>")
    @doc.parameter(name="an_id", description="An ID", required=True, _in="path", schema=int_min_4_ref)
    @doc.response("200", description="You got a 200!", headers={"x-prize": doc.Header(description="free money")})
    @doc.security([])
    def head_id(request, an_id: int):
        d = locals()
        del d["request"]  # not JSON serializable
        return sanic.response.json(d)

    @app.post("/object/")
    def test_post(request: sanic.request.Request):
        query = request.query_string
        return sanic.response.json({"query": query, "id": random.randint(1, 100)})

    @app.put("/object/<an_id:int>")
    def put_id(request: sanic.request.Request, an_id: int):
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
            "contact": {"name": "developer", "url": "https://developer.dev"},
            "description": "This file has a simple example adding security ",
            "license": {"name": "A license name", "url": "https://license.url"},
            "title": "/Users/efarrell/Workspaces/github/endafarrell/sanic-openapi3e/tests/openapi3e/test_security.py",
            "version": "v1.0.0",
        },
        "openapi": "3.0.2",
        "paths": {
            "/object/": {
                "post": {
                    "operationId": "POST~~~object~",
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "404": {"$ref": "#/components/responses/404"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                }
            },
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
                        "404": {"$ref": "#/components/responses/404"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                    "security": [],
                    "tags": ["Tag 1"],
                },
                "head": {
                    "operationId": "HEAD~~~object~an_id",
                    "parameters": [
                        {
                            "description": "An ID",
                            "in": "path",
                            "name": "an_id",
                            "required": true,
                            "schema": {"$ref": "#/components/schemas/int.min4"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "You got a 200!",
                            "headers": {
                                "x-prize": {
                                    "allowEmptyValue": false,
                                    "allowReserved": false,
                                    "description": "free money",
                                    "explode": false,
                                    "required": false,
                                }
                            },
                        },
                        "400": {"$ref": "#/components/responses/400"},
                        "404": {"$ref": "#/components/responses/404"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                    "security": [],
                },
                "put": {
                    "operationId": "PUT~~~object~an_id",
                    "parameters": [{"in": "path", "name": "an_id", "required": true, "schema": {"type": "integer"}}],
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "404": {"$ref": "#/components/responses/404"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                },
            },
        },
        "security": [{"bearerAuth": []}],
        "tags": [{"description": "A tag desc", "name": "Tag 1"}],
    }

    run_asserts(response, expected)
