import sanic.response
from sanic import Sanic

from tests.conftest import false, run_asserts, true


def test_servers(openapi__mod_bp_doc):
    openapi_mod, openapi_blueprint, doc = openapi__mod_bp_doc
    example_port = 8002
    days_of_week = doc.Schema(
        _type="string",
        description="Days of the week, short, English",
        enum=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    )

    app = Sanic(name=__file__, strict_slashes=True)
    app.blueprint(openapi_blueprint)

    servers = [doc.Server(f"http://localhost:{example_port}", "this server")]
    app.config.OPENAPI_SERVERS = servers
    app.config.OPENAPI_OPERATION_ID_FN = openapi_mod.camel_case_operation_id_fn
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
    @doc.servers(servers + [doc.Server("https://my-server.url", description="An alt server")])
    def get_start_end_hops(request, start: str, end: str, hops: int):
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
            },
            "schemas": {
                "days": {
                    "description": "Days of the week, short, English",
                    "enum": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    "exclusiveMaximum": false,
                    "exclusiveMinimum": false,
                    "nullable": false,
                    "readOnly": false,
                    "type": "string",
                    "uniqueItems": false,
                    "writeOnly": false,
                },
                "int.min4": {
                    "description": "Minimum: 4",
                    "exclusiveMaximum": false,
                    "exclusiveMinimum": false,
                    "format": "int32",
                    "minimum": 4,
                    "nullable": false,
                    "readOnly": false,
                    "title": "int.min4",
                    "type": "integer",
                    "uniqueItems": false,
                    "writeOnly": false,
                },
            },
        },
        "info": {"description": "Description", "title": "API", "version": "v1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/simple/01/from/{start}/to/{end}/in/{hops}": {
                "get": {
                    "operationId": "getStartEndHops",
                    "parameters": [
                        {
                            "description": "Start day",
                            "in": "path",
                            "name": "start",
                            "required": true,
                            "schema": {"$ref": "#/components/schemas/days"},
                        },
                        {
                            "description": "End day",
                            "in": "path",
                            "name": "end",
                            "required": true,
                            "schema": {"$ref": "#/components/schemas/days"},
                        },
                        {
                            "description": "hops to use",
                            "in": "path",
                            "name": "hops",
                            "required": true,
                            "schema": {"$ref": "#/components/schemas/int.min4"},
                        },
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
                    "servers": [
                        {"description": "this server", "url": "http://localhost:8002"},
                        {"description": "An alt server", "url": "https://my-server.url"},
                    ],
                }
            }
        },
        "servers": [{"description": "this server", "url": "http://localhost:8002"}],
    }

    run_asserts(response, expected)
