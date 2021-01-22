import pathlib

import sanic
import sanic.response

# isort: off
# These two lines are to ensure that the version of `sanic_openapi3e` your app uses is from this checkout.
import sys

sys.path.insert(0, str(pathlib.Path(__file__).absolute().parent.parent))
from sanic_openapi3e import doc, openapi_blueprint, swagger_blueprint

# isort: on

app = sanic.Sanic(name=__file__, strict_slashes=True)
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)


@app.get("/user/<user_id:int>")
@doc.summary("Fetches a user by ID")
@doc.response(200, "The user")
async def get_user(request, user_id):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)


@app.post("/user")
@doc.summary("Creates a new user")
@doc.request_body(
    description="A (JSON) user object",
    required=True,
    content={"application/json": doc.MediaType(schema=doc.Schema.Object)},
)
@doc.response(201, "User created")
async def post_user(request):
    body = request.json
    d = {"body": body, "headers": dict(request.headers)}
    return sanic.response.json(d, status=201)


example_port = 8002


@app.listener("after_server_start")
async def notify_server_started(app: sanic.app.Sanic, __):
    print("\n\n************* sanic-openapi3e ********************************")
    print(f"* See your openapi swagger on http://127.0.0.1:{example_port}/swagger/ *")
    print("************* sanic-openapi3e ********************************\n\n")


app.go_fast(port=example_port)
