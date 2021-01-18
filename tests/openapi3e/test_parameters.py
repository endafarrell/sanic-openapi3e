import json

import pytest
import sanic
import sanic.response
from sanic import Sanic

import sanic_openapi3e
import sanic_openapi3e.oas_types
from tests.conftest import false, null, run_asserts, strict_slashes, true


@pytest.mark.asyncio
async def test_param_cannot_be_in_multiple_places(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc

    with pytest.raises(AssertionError):
        app = Sanic("test_param_cannot_be_in_multiple_places", strict_slashes=strict_slashes)
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
            _in="query",  # <<-- item under test. `an_id` cannot be in `query` as it is already in `path` (above)
            schema=sanic_openapi3e.oas_types.Schema.Integers,
        )
        async def test_some_ids(req, an_id):
            return sanic.response.json(locals())  # pragma: no cover

        _, response = await app.test_client.get("/openapi/spec.json")


def test_param_in_query(openapi__mod_bp_doc):
    # TODO test_field_names_cannot_be_repeated_in_different_locations ?
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc

    app = Sanic("test_param_in_query", strict_slashes=strict_slashes)
    app.blueprint(openapi_blueprint)

    @app.get("/test/699/some_ids_in_query")
    @doc.parameter(
        name="an_id",
        description="An ID",
        required=True,
        choices=[1, 3, 5, 7, 11, 13],
        _in="query",
        schema=sanic_openapi3e.oas_types.Schema.Integers,
    )
    async def test_some_ids(req):
        args = req.args
        ids = args.getlist("an_id")
        d = locals()
        del d["req"]
        return sanic.response.json(d)

    _, response = app.test_client.get("/openapi/spec.json")
    expected = {
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/test/699/some_ids_in_query": {
                "get": {
                    "operationId": "GET~~~test~699~some_ids_in_query",
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

    _, response = app.test_client.get("/test/699/some_ids_in_query?ids=1&ids=5")
    assert response.status == 200
    resp = json.loads(response.body.decode())
    # TODO - notice that these `ids` are a list, but of str not int. This is expected and users need to
    # TODO - handle this.
    assert resp == {
        "args": {"ids": ["1", "5"]},
        "ids": null,
    }


def test_path_params_must_be_required(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path_params_must_be_required", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/759/anId2/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", choices=[1, 3, 5, 7, 11, 13], _in="path"
    )  # <<-- note: there is no `required=True` here!
    def test_id2(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

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


@pytest.mark.xfail(reason="The type is not being updated as expected yet.")
def test_path_parameter_conflicting_types(openapi__mod_bp_doc):
    # The param was not explicitly typed, but the
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
        return sanic.response.json(locals())  # pragma: no cover

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
            "/test/833/anId/{an_id}": {
                "get": {
                    "operationId": "testId",
                    "parameters": [
                        {
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
    run_asserts(spec, expected)


def test_path_params_w_schema_wo_choices(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    # schemas = {
    #     "int.min4": sanic_openapi3e.oas_types.Schema(
    #         title="int.min4", _type="integer", _format="int32", minimum=4, description="Minimum: 4",
    #     )
    # }
    # components = sanic_openapi3e.oas_types.Components(schemas=schemas)

    app = Sanic("test_path_params_w_schema_wo_choices", strict_slashes=strict_slashes)
    # app.config.OPENAPI_COMPONENTS = components
    app.blueprint(openapi_blueprint)

    @app.get("/test/759/anId2/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", _in="path", schema=sanic_openapi3e.oas_types.Schema.Integer,
    )  # <<-- note: there is no `required=True` here!
    def test_id2(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

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


def test_path_params_wo_schema_w_choices(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path_params_wo_schema_w_choices", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/759/anId2/<an_id>")
    @doc.parameter(
        name="an_id", description="An ID", _in="path", choices=["a", "b", "o"],
    )  # <<-- note: there is no `required=True` here!
    def test_id2(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

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
                            "required": true,
                            "schema": {
                                "enum": ["a", "b", "o"],
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "nullable": false,
                                "readOnly": false,
                                "type": "string",
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


def test_path_params_wo_schema_wo_choices(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    app = Sanic("test_path_params_wo_schema_wo_choices", strict_slashes=strict_slashes)

    app.blueprint(openapi_blueprint)

    @app.get("/test/759/anId2/<an_id>")
    @doc.parameter(name="an_id", description="An ID", _in="path")  # <<-- note: there is no `required=True` here!
    def test_id2(_, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

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
                            "required": true,
                            "schema": {
                                "exclusiveMaximum": false,
                                "exclusiveMinimum": false,
                                "nullable": false,
                                "readOnly": false,
                                "type": "string",
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


def test_path_params_w_reference_schema_and_choices(openapi__mod_bp_doc):
    openapi, openapi_blueprint, doc = openapi__mod_bp_doc
    with pytest.raises(ValueError):
        app = Sanic("test_path_params_w_reference_schema_and_choices", strict_slashes=strict_slashes)
        schemas = {
            "int.min4": sanic_openapi3e.oas_types.Schema(
                title="int.min4", _type="integer", _format="int32", minimum=4, description="Minimum: 4",
            )
        }
        components = sanic_openapi3e.oas_types.Components(schemas=schemas)

        app.config.OPENAPI_COMPONENTS = components
        app.blueprint(openapi_blueprint)

        @app.get("/test/759/anId2/<an_id>/<another_id:int>")
        @doc.parameter(
            name="an_id",
            description="An ID",
            _in="path",
            schema=sanic_openapi3e.doc.Schema.String,
            choices=["a", "b", "o"],
        )
        @doc.parameter(
            name="another_id",
            description="Another ID",
            _in="path",
            schema=sanic_openapi3e.doc.Reference("#/components/schemas/int.min4"),
            choices=[1, 2, 3],  # <<-- item under test - can't add choices to a reference schema
        )
        def test_id2(_, an_id: int):  # pragma: no cover
            # `pragma: no cover` as the ValueError is raised during import of this module, before the method is defined.
            return sanic.response.json(locals())
