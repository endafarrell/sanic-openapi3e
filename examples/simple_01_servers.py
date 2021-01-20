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

example_port = 8002
days_of_week = doc.Schema(
    _type="string",
    description="Days of the week, short, English",
    enum=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
)

app = Sanic(name=__file__, strict_slashes=True)
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)

app.config.OPENAPI_EXTERNAL_DOCS = doc.ExternalDocumentation("http://wikipedia.org/", description="Fabulous resource")
servers = [doc.Server(f"http://localhost:{example_port}", "this server")]
app.config.OPENAPI_SERVERS = servers
schemas = {
    "int.min4": doc.Schema(title="int.min4", _type="integer", _format="int32", minimum=4, description="Minimum: 4",),
    "days": days_of_week,
}
components = doc.Components(schemas=schemas)
app.config.OPENAPI_COMPONENTS = components
app.config.API_TITLE = __file__
app.config.API_DESCRIPTION = """This file has simple examples of adding servers and external docs to the spec. The 
`/simple/01/from/{start}/to/{end}/in/{hops}` endpoint also has a server of its own."""
int_min_4_ref = doc.Reference("#/components/schemas/int.min4")
dow_ref = doc.Reference("#/components/schemas/days")


@app.get("/simple/01/from/<start>/to/<end>/in/<hops:int>")
@doc.parameter(name="start", description="Start day", required=True, _in="path", schema=dow_ref)
@doc.parameter(name="end", description="End day", required=True, _in="path", schema=dow_ref)
@doc.parameter(
    name="hops", description="hops to use", required=True, _in="path", schema=int_min_4_ref,
)
@doc.servers(servers + [doc.Server("https://my-server.url", description="An alt server")])
@doc.external_docs("http://localhost:8002", "me! me!")
def get_start_end_hops(request, start: str, end: str, hops: int):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)


@app.listener("after_server_start")
async def notify_server_started(app: sanic.app.Sanic, __):
    print("\n\n************* sanic-openapi3e ********************************")
    print(f"* See your openapi swagger on http://127.0.0.1:{example_port}/swagger/ *")
    print("************* sanic-openapi3e ********************************\n\n")


app.go_fast(port=example_port)
