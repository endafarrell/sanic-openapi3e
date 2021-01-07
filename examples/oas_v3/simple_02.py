import sanic.request
import sanic.response
from sanic import Sanic

# This line is here only to ensure that the version your app uses is from this checkout.
import sys; import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent.absolute()))

from sanic_openapi3e import openapi_blueprint, swagger_blueprint, doc


app = Sanic(strict_slashes=True)
app.config.SHOW_OPENAPI_EXCLUDED = True
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)


@app.get("/15/test_id/<an_id:int>")
@doc.parameter(name="an_id", description="An ID", required=True, _in="path", schema=doc.Schema.Integer)
@doc.tag("Tag 1", description="A tag desc")
def get_id_19(request, an_id: int):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)


@app.get("/22/test_id/<an_id:int>")
@doc.exclude()
@doc.tag("Tag excluded", description="You shouldn's usually see this...")
@doc.parameter(name="an_id", description="An ID", required=True, _in="path", schema=doc.Schema.Integer)
def get_id_29(request, an_id: int):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)


app.go_fast(port=8002)
