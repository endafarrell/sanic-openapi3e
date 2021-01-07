import sanic.request
import sanic.response
from sanic import Sanic

# This line is here only to ensure that the version your app uses is from this checkout.
import sys; import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent.absolute()))

from sanic_openapi3e import openapi_blueprint, swagger_blueprint, doc


int_min_4 = doc.Schema(
    _type="integer", _format="int32", minimum=4, description="Minimum value: 4"
)  # type: doc.Schema
an_id_ex1 = doc.Example(
    summary="A small number", description="Desc: Numbers less than ten", value=7
)  # type: doc.Example
an_id_ex2 = doc.Example(
    summary="A big number",
    description="Desc: Numbers more than one million!",
    value=123456789,
)  # type: doc.Example
days_of_week = doc.Schema(
    _type="string",
    description="Days of the week, short, English",
    enum=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
)

app = Sanic(strict_slashes=True)
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)

schemas = {
    "int.min4": doc.Schema(
        title="int.min4",
        _type="integer",
        _format="int32",
        minimum=4,
        description="Minimum: 4",
    )
}
components = doc.Components(schemas=schemas)
app.config.OPENAPI_COMPONENTS = components
app.config.SHOW_OPENAPI_EXCLUDED = True
int_min_4_ref = doc.Reference("#/components/schemas/int.min4")


@app.get("/41/test_id/<an_id:int>")
@doc.parameter(name="an_id", description="An ID", required=True, _in="path", schema=doc.Schema.Integer)
@doc.tag("Tag 1", description="A tag desc")
def test_id(request, an_id: int):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)


@app.get("/47/test_id_min/<an_id:int>")
@doc.parameter(
    name="an_id", description="An ID", required=True, _in="path", schema=int_min_4_ref
)
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


@app.get("/74/test_path__deprecated/<an_id:int>")
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
def path__deprecated(request, an_id: int):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)


@app.get("/90/test_parameter__deprecated/<an_id:int>")
@doc.parameter(
    name="an_id", description="An ID", required=True, _in="path", deprecated=True, schema=doc.Schema.Integer
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


app.go_fast(port=8002)
