import json
from pathlib import Path

import sanic
import sanic.request
import sanic.response
from sanic import Sanic

import sanic_openapi3e
from tests.conftest import run_asserts, strict_slashes


def test_yaml_spec_00(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = create_medium_sized_app_00("test_yaml_spec_00", doc, openapi_blueprint)

    _, response = app.test_client.get("/openapi/spec.yml")

    expected = (Path(__file__).absolute().parent / "expected_spec_for_medium_sized_app_00.yml").read_text(
        encoding="utf8"
    )
    assert response.content.decode("utf8").splitlines() == expected.splitlines()


def test_json_spec_00(openapi__mod_bp_doc):
    _, openapi_blueprint, doc = openapi__mod_bp_doc
    app = create_medium_sized_app_00("test_json_spec_00", doc, openapi_blueprint)

    _, response = app.test_client.get("/openapi/spec.json")

    with open(Path(__file__).absolute().parent / "expected_spec_for_medium_sized_app_00.json") as _f:
        expected = json.load(_f)
    run_asserts(response, expected)


def create_medium_sized_app_00(sanic_name: str, doc, openapi_blueprint):
    app = Sanic(sanic_name, strict_slashes=strict_slashes)
    app.config.OPENAPI_OPERATION_ID_FN = sanic_openapi3e.openapi.camel_case_operation_id_fn
    app.blueprint(openapi_blueprint)
    int_min_4 = doc.Schema(_type="integer", _format="int32", minimum=4, description="Minimum value: 4")
    an_id_ex1 = doc.Example(summary="A small number", description="Desc: Numbers less than ten", value=7)
    an_id_ex2 = doc.Example(
        summary="A big number", description="Desc: Numbers more than one million!", value=123456789,
    )
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
        return sanic.response.json(locals())  # pragma: no cover

    @app.get("/47/test_id_min/<an_id:int>")
    @doc.parameter(name="an_id", description="An ID", required=True, _in="path", schema=int_min_4_ref)
    @doc.response("200", description="You got a 200!", headers={"x-prize": doc.Header(description="free money")})
    def test_id_min(request, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

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
        return sanic.response.json(locals())  # pragma: no cover

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
        return sanic.response.json(locals())  # pragma: no cover

    @app.get("/90/test_parameter__deprecated/<an_id:int>")
    @doc.parameter(
        name="an_id", description="An ID", required=True, _in="path", deprecated=True, schema=doc.Schema.Integer,
    )
    @doc.summary("A path deprecated parameter")
    @doc.description("The parameter should be marked as deprecated")
    def param__deprecated(request, an_id: int):
        return sanic.response.json(locals())  # pragma: no cover

    @app.get("/100/excluded-route")
    @doc.summary("An excluded path")
    @doc.description("The parameter should not be seen in the spec")
    @doc.exclude()
    def path__excluded(request):
        return sanic.response.json(locals())  # pragma: no cover

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
        return sanic.response.json(locals())  # pragma: no cover

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
        return sanic.response.json(locals())  # pragma: no cover

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
        return sanic.response.json(locals())  # pragma: no cover

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
        return sanic.response.json(locals())  # pragma: no cover

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
        return sanic.response.json(locals())  # pragma: no cover

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
        return sanic.response.json(locals())  # pragma: no cover

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
        return sanic.response.json(locals())  # pragma: no cover

    @app.patch("/test/excluded_path_with_unique_tag")
    @doc.tag("a unique, but should not be seen, tag")
    @doc.exclude()
    def excluded_path_with_unique_tag(_):
        return sanic.response.json(locals())  # pragma: no cover

    return app


# Sometimes really useful ;-)
# if __name__ == "__main__":
#     from sanic_openapi3e import doc, openapi_blueprint, swagger_blueprint
#
#     app = create_medium_sized_app_00(doc, openapi_blueprint)
#     app.blueprint(swagger_blueprint)
#     app.go_fast()
