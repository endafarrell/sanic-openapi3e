import json

import pytest
import sanic
import sanic.response
from sanic import Sanic
from sanic.views import CompositionView

import sanic_openapi3e
import sanic_openapi3e.oas_types
from tests.conftest import null, run_asserts, strict_slashes, true


def test_two_routes_for_same_uri(openapi__mod_bp_doc):

    openapi, openapi_blueprint, doc = openapi__mod_bp_doc

    app = Sanic("test_two_routes_for_same_uri", strict_slashes=strict_slashes)
    app.blueprint(openapi_blueprint)

    def test_get_class_id(req):
        d = locals()
        del d["req"]
        return sanic.response.json(d)

    def test_head_class_id(req):
        d = locals()
        del d["req"]
        return sanic.response.json(d)

    view = CompositionView()
    view.add(["GET"], lambda request: test_get_class_id)
    view.add(["POST", "PUT"], lambda request: test_head_class_id)
    app.add_route(view, "/")

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
            "/": {
                "get": {
                    "operationId": "GET~~~",
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "404": {"$ref": "#/components/responses/404"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                },
                "post": {
                    "operationId": "POST~~~",
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "404": {"$ref": "#/components/responses/404"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                },
                "put": {
                    "operationId": "PUT~~~",
                    "responses": {
                        "200": {"$ref": "#/components/responses/200"},
                        "400": {"$ref": "#/components/responses/400"},
                        "404": {"$ref": "#/components/responses/404"},
                        "500": {"$ref": "#/components/responses/500"},
                    },
                },
            }
        },
    }

    run_asserts(response, expected)
