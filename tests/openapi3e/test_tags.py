import pytest
import sanic.response
from sanic import Sanic

import sanic_openapi3e
from tests.conftest import false, run_asserts, strict_slashes, true

# ------------------------------------------------------------ #
#  tag details
# ------------------------------------------------------------ #


@pytest.mark.xfail(reason="Works for apps, but within multiple tests refactoring is needed")
def test_show_unused_tag_v1(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    assert not doc.module_tags, doc.module_tags
    app = Sanic("test_show_unused_tag_v1", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/1033/getitem/<an_id:int>")
    @doc.tag("Tag 1 - used")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def get_item(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    @app.put("/test/1041/putitem/<an_id:int>")
    @doc.tag("Tag 1 - used")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def put_item(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    @app.post("/test/1049/postitem/<an_id:int>")
    @doc.tag("Tag 1 - used")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def post_item(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    @app.delete("/test/1057/deleteitem/<an_id:int>")
    @doc.tag("Tag 2 - not used", description="Not used as teh only route with it is excluded")
    @doc.exclude()
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def delete_item(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    # noinspection PyProtectedMember
    spec = sanic_openapi3e.openapi._build_openapi_spec(
        app, operation_id_fn=sanic_openapi3e.openapi.default_operation_id_fn, hide_openapi_self=True, hide_excluded=True
    )
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/1033/getitem/{an_id}": {
                "get": {
                    "operationId": "GET~~~test~1033~getitem~an_id",
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
                    "tags": ["Tag 1 - used"],
                }
            },
            "/test/1041/putitem/{an_id}": {
                "put": {
                    "operationId": "PUT~~~test~1041~putitem~an_id",
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
                    "tags": ["Tag 1 - used"],
                }
            },
            "/test/1049/postitem/{an_id}": {
                "post": {
                    "operationId": "POST~~~test~1049~postitem~an_id",
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
                    "tags": ["Tag 1 - used"],
                }
            },
            "/test/1057/deleteitem/{an_id}": {
                "delete": {
                    "operationId": "DELETE~~~test~1057~deleteitem~an_id",
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
            },
        },
    }

    run_asserts(spec, expected)


def test_show_unused_tag_v2(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_show_unused_tag_v2", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/1131/getitem/<an_id:int>")
    @doc.tag("Tag 1 - used")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def get_item(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    @app.put("/test/1139/putitem/<an_id:int>")
    @doc.tag("Tag 1 - used", description="A desc for Tag 1")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def put_item(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    @app.post("/test/1147/postitem/<an_id:int>")
    @doc.tag("Tag 1 - used")
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def post_item(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    @app.delete("/test/1155/deleteitem/<an_id:int>")
    @doc.tag("Tag 2 - not used")
    @doc.exclude()
    @doc.parameter(name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path")
    def delete_item(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    # noinspection PyProtectedMember
    spec = sanic_openapi3e.openapi._build_openapi_spec(
        app,
        operation_id_fn=sanic_openapi3e.openapi.camel_case_operation_id_fn,
        hide_openapi_self=True,
        hide_excluded=True,
    )
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/1131/getitem/{an_id}": {
                "get": {
                    "operationId": "getItem",
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
            },
            "/test/1139/putitem/{an_id}": {
                "put": {
                    "operationId": "putItem",
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
            },
            "/test/1147/postitem/{an_id}": {
                "post": {
                    "operationId": "postItem",
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
            },
            "/test/1155/deleteitem/{an_id}": {
                "delete": {
                    "operationId": "deleteItem",
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
            },
        },
    }

    run_asserts(spec, expected)

    print("Now with show_unused_tags=False")
    # noinspection PyProtectedMember
    spec = sanic_openapi3e.openapi._build_openapi_spec(
        app,
        operation_id_fn=sanic_openapi3e.openapi.camel_case_operation_id_fn,
        hide_openapi_self=True,
        hide_excluded=True,
    )
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/1131/getitem/{an_id}": {
                "get": {
                    "operationId": "getItem",
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
            },
            "/test/1139/putitem/{an_id}": {
                "put": {
                    "operationId": "putItem",
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
            },
            "/test/1147/postitem/{an_id}": {
                "post": {
                    "operationId": "postItem",
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
            },
            "/test/1155/deleteitem/{an_id}": {
                "delete": {
                    "operationId": "deleteItem",
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
            },
        },
    }

    run_asserts(spec, expected)


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
        return sanic.response.json(locals())  # pragma: no cover

    with pytest.raises(AssertionError, match=r"^Conflicting tag.description for tag"):

        @app.get("/test/398/anId2/<an_id:int>")
        @doc.parameter(
            name="an_id", description="An ID", required=True, choices=[1, 3, 5, 7, 11, 13], _in="path",
        )
        @doc.response(200, description="A 200 description")
        @doc.response(201, description="A 201 description")
        @doc.tag("Described tag", description="This same tag has a conflicting description")  # <<-- detail under test
        def test_id2(_, an_id: int):
            return sanic.response.json(locals())  # pragma: no cover


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
        return sanic.response.json(locals())  # pragma: no cover

    @app.get("/test/437/anId2/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    @doc.response(200, description="A 200 description")
    @doc.response(201, description="A 201 description")
    @doc.tag("Described tag")  # <<-- detail under test
    def test_id2(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

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
        return sanic.response.json(locals())  # pragma: no cover

    @app.get("/test/529/anId2/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    @doc.response(200, description="A 200 description")
    @doc.response(201, description="A 201 description")
    @doc.tag("Described tag", description="This tag has a lovely description.")  # <<-- the detail under test.
    def test_id2(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

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
        return sanic.response.json(locals())  # pragma: no cover

    @app.post("/test/609/<an_id:int>")  # <<-- the detail under test.
    @doc.parameter(
        name="an_id", description="An ID", required=True, choices=[1, 3, 5, 7, 11, 13], _in="path",
    )
    @doc.response(200, description="A 200 description")
    @doc.response(201, description="A 201 description")
    @doc.tag("Described tag", description="This tag has a lovely description.")
    def test_id2(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

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
        return sanic.response.json(locals())  # pragma: no cover

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
