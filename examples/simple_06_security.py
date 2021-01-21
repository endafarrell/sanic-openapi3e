import pathlib
import random
from typing import List

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
int_min_4_ref = doc.Reference("#/components/schemas/int.min4")
an_id_ex1 = doc.Example(summary="A small number", description="Desc: Numbers less than ten", value=7)
an_id_ex2 = doc.Example(summary="A big number", description="Desc: Numbers more than one million!", value=123456789,)
days_of_week = doc.Schema(
    _type="string",
    description="Days of the week, short, English",
    enum=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
)

schemas = {
    "str.min4": doc.Schema(title="str.min4", _type="string", minimum=4, description="A string of len >= 4",),
    "int.min4": doc.Schema(title="int.min4", _type="integer", _format="int32", minimum=4, description="Minimum: 4",),
}
components = doc.Components(schemas=schemas)
security: List[doc.SecurityRequirement] = [doc.SecurityRequirement({"bearerAuth": []})]


app = Sanic(name=__file__, strict_slashes=True)
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)

app.config.API_TITLE = __file__
app.config.API_DESCRIPTION = "This file has a simple example adding security "
app.config.OPENAPI_COMPONENTS = components
app.config.OPENAPI_SECURITY = security


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


example_port = 8002


@app.listener("after_server_start")
async def notify_server_started(_, __):
    print("\n\n************* sanic-openapi3e ********************************")
    print(f"* See your openapi swagger on http://127.0.0.1:{example_port}/swagger/ *")
    print("************* sanic-openapi3e ********************************\n\n")


app.go_fast(port=example_port)
