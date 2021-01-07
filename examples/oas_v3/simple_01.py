import sanic.request
import sanic.response
from sanic import Sanic

# This line is here only to ensure that the version your app uses is from this checkout.
import sys; import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent.absolute()))

from sanic_openapi3e import openapi_blueprint, swagger_blueprint, doc


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
    ),
    "days": days_of_week,
}
components = doc.Components(schemas=schemas)
app.config.OPENAPI_COMPONENTS = components
int_min_4_ref = doc.Reference("#/components/schemas/int.min4")
dow_ref = doc.Reference("#/components/schemas/days")


@app.get("/simple/01/from/<start>/to/<end>/in/<hops:int>")
@doc.parameter(
    name="start", description="Start day", required=True, _in="path", schema=dow_ref
)
@doc.parameter(
    name="end", description="End day", required=True, _in="path", schema=dow_ref
)
@doc.parameter(
    name="hops",
    description="hops to use",
    required=True,
    _in="path",
    schema=int_min_4_ref,
)
def get_start_end_hops(request, start: str, end: str, hops: int):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)


app.go_fast(port=8002)
