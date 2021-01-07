import pathlib
import sanic
import sanic.response

# This line is here only to ensure that the version your app uses is from this checkout.
import sys; sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.absolute()))

from sanic_openapi3e import openapi_blueprint, swagger_blueprint, doc

app = sanic.Sanic(strict_slashes=True)
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
    content={
        "application/json": {
            "schema": {
                "type": "object"
            }
        }
    }
)
@doc.response(201, "User created")
async def post_user(request):
    body = request.json
    d = {
        "body": body,
        "headers": dict(request.headers)
    }
    return sanic.response.json(d, status=201)

app.go_fast(port=8001)
