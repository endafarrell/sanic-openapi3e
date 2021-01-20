import pathlib

import sanic.request
import sanic.response
from sanic import Sanic

# isort: off
# These two lines are to ensure that the version of `sanic_openapi3e` your app uses is from this checkout.
import sys

sys.path.insert(0, str(pathlib.Path(__file__).absolute().parent.parent))
from sanic_openapi3e import doc, openapi_blueprint, swagger_blueprint

# isort: on

app = Sanic(name=__file__, strict_slashes=True)
app.config.SHOW_OPENAPI_EXCLUDED = True
app.config.API_TITLE = __file__
app.config.API_DESCRIPTION = f"""This app was configured with `app.config.SHOW_OPENAPI_EXCLUDED = True` so you can:\n
\n
* In the black swagger top-nav above, manually change the value of 
`/openapi/spec.json` to `/openapi/spec.all.json`;
* click "Explore"
* Now see the excluded routes in the UI.

It is not recommended to set this flag for production builds, but it can be helpful during development.
"""
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)


@app.get("/test_id/<an_id:int>")
@doc.parameter(
    name="an_id", description="An ID", required=True, _in="path", schema=doc.Schema.Integer,
)
@doc.tag("Tag 1", description="A tag desc")
def get_id_19(request, an_id: int):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)


@app.get("/22/test_id/<an_id:int>")
@doc.exclude()
@doc.tag("Tag excluded", description="You shouldn'd usually see this...")
@doc.parameter(
    name="an_id", description="An ID", required=True, _in="path", schema=doc.Schema.Integer,
)
def get_id_29(request, an_id: int):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)


example_port = 8002


@app.listener("after_server_start")
async def notify_server_started(app: sanic.app.Sanic, __):
    print("\n\n************* sanic-openapi3e ********************************")
    print(f"* See your openapi swagger on http://127.0.0.1:{example_port}/swagger/ *")
    print("************* sanic-openapi3e ********************************\n\n")


app.go_fast(port=example_port)
