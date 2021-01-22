import pathlib
from typing import Dict, List, Optional, Union

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


schemas: Optional[Dict[str, Union[doc.Schema, doc.Reference]]] = {
    "str.min4": doc.Schema(title="str.min4", _type="string", minimum=4, description="A string of len >= 4",),
    "int.min4": doc.Schema(title="int.min4", _type="integer", _format="int32", minimum=4, description="Minimum: 4",),
}
components = doc.Components(schemas=schemas)
security: List[doc.SecurityRequirement] = [doc.SecurityRequirement({"bearerAuth": []})]
responses_200only = doc.Responses({"200": doc.Reference("#/components/responses/200")}, no_defaults=True)


app = Sanic(name=__file__, strict_slashes=True)
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)

app.config.API_TITLE = __file__
app.config.API_DESCRIPTION = "This has an example adding multiple responses in a single `@doc.responses` call"
app.config.OPENAPI_COMPONENTS = components
app.config.OPENAPI_SECURITY = security


@app.get("/object/<an_id:int>")
@doc.parameter(
    name="an_id", description="An ID", required=True, _in="path", schema=doc.Schema.Integer,
)
@doc.tag("Tag 1", description="A tag desc")
@doc.responses(
    {
        200: {"r": doc.Reference("#/components/responses/200")},
        404: {"d": "Not there", "h": None, "c": None, "l": None},
        401: None,
        403: None,
        405: None,
        410: None,
        500: None,
    }
)
def get_id(request, an_id: int):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)


@app.get("/object2/<an_id:int>")
@doc.parameter(
    name="an_id", description="An ID", required=True, _in="path", schema=doc.Schema.Integer,
)
@doc.tag("Tag 1", description="A tag desc")
@doc.responses(responses_200only)
def get_id2(request, an_id: int):
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
