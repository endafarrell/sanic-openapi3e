import pathlib

import sanic.request
import sanic.response
import sanic.router
from sanic import Sanic

# isort: off
# These two lines are to ensure that the version of `sanic_openapi3e` your app uses is from this checkout.
import sys

sys.path.insert(0, str(pathlib.Path(__file__).absolute().parent.parent))
from sanic_openapi3e import doc, openapi_blueprint, swagger_blueprint

# isort: on


int_min_4 = doc.Schema(_type="integer", _format="int32", minimum=4, description="Minimum value: 4")
an_id_ex1 = doc.Example(summary="A small number", description="Desc: Numbers less than ten", value=7)
an_id_ex2 = doc.Example(summary="A big number", description="Desc: Numbers more than one million!", value=123456789,)
days_of_week = doc.Schema(
    _type="string",
    description="Days of the week, short, English",
    enum=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
)

app = Sanic(name=__file__, strict_slashes=True)
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)

schemas = {
    "str.min4": doc.Schema(title="str.min4", _type="string", minimum=4, description="A string of len >= 4",),
    "int.min4": doc.Schema(title="int.min4", _type="integer", _format="int32", minimum=4, description="Minimum: 4",),
}
components = doc.Components(schemas=schemas)
app.config.API_TITLE = __file__
app.config.API_DESCRIPTION = "This file has a simple exampleof cloaking all PUT/POST/DELETE methods. "
app.config.OPENAPI_COMPONENTS = components
app.config.SHOW_OPENAPI_EXCLUDED = True


def cloak(method: str, uri: str, route: sanic.router.Route) -> bool:
    assert uri  # unused for this cloak method
    assert route  # unused for this cloak method
    return method.lower().strip() in {"put", "post", "delete"}


app.config.OPENAPI_CLOAK_FN = cloak


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


@app.get("/90/test_parameter__deprecated/<an_id:int>")
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


example_port = 8002


@app.listener("after_server_start")
async def notify_server_started(_, __):
    print("\n\n************* sanic-openapi3e ********************************")
    print(f"* See your openapi swagger on http://127.0.0.1:{example_port}/swagger/ *")
    print("************* sanic-openapi3e ********************************\n\n")


app.go_fast(port=example_port)
