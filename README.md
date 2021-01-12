# Sanic OpenAPI v3e

OpenAPI v3 support for Sanic. Document and describe all parameters, 
including sanic path params. python 3.6+

[![Pythons](https://img.shields.io/pypi/pyversions/sanic-openapi3e.svg)](https://img.shields.io/pypi/pyversions/sanic-openapi3e.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Downloads](https://pepy.tech/badge/sanic-openapi3e)](https://pepy.tech/project/sanic-openapi3e)
## Installation

```shell
pip install sanic-openapi3e
```

## Usage

### Import blueprint and use simple decorators to document routes:

```python
import sanic
import sanic.response
from sanic_openapi3e import openapi_blueprint, swagger_blueprint, doc

app = sanic.Sanic(strict_slashes=True)
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)

@app.get("/user/<user_id>")
@doc.summary("Fetches a user by ID")
@doc.response(200, "The user")
async def get_user(request, user_id):
    return sanic.response.json({"user_id": user_id})

app.go_fast()
```

You'll now have a specification at the URL `/openapi/spec.json`.
Your routes will be automatically categorized by their blueprints' 
names.

Run these simple examples and point your browser to 
http://127.0.0.1:8000/swagger/ to see this in action.


### Describe route path parameters

```python
import sanic
import sanic.response
from sanic_openapi3e import openapi_blueprint, swagger_blueprint, doc
app = sanic.Sanic(strict_slashes=True)
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)

@app.get("/examples/test_id/<an_id:int>")
@doc.parameter(name="an_id", description="An ID", required=True, _in="path")
def test_id(request, an_id):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)
    
app.go_fast()
```

``sanic-openapiv3`` will recognise that the path parameter ``an_id`` is
described with ``@doc.parameter`` and will merge the details together.

You may wish to specify that a parameter be limited to a set of choices,
such as day-of-week or that it has a minimum value. These can be done 
for parameters in ``path``, ``query``, ``header`` and ``cookie``:

```python
import sanic
import sanic.request
import sanic.response
from sanic_openapi3e import openapi_blueprint, swagger_blueprint, doc

app = sanic.Sanic(strict_slashes=True)
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)

int_min_4 = doc.Schema(
    _type="integer", _format="int32", minimum=4, description="Minimum: 4"
)  

@app.get("/test/some_ids")
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
     


@app.get("/examples/test_id_min/<an_id:int>")
@doc.parameter(
    name="an_id", description="An ID", required=True, _in="path", schema=int_min_4
)
def test_id_min(request, an_id: int):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)

app.go_fast()
```

### Describe your tags
OpenAPI uses "tags" (there can be more than one per route) to group the 
endpoints. It's nice to be able to group your endpoints into tags given
by the blueprint's name, but sometimes you will want to give them better
names: ``@doc.tag("tag name")``. Better still is to give a description 
to these tags (which shows up nicely in Swagger UI), so 
``@doc.tag("tag name", description="tag description")``. 

You don't have to add the description more than once, 
``sanic-openapiv3e`` will make it available, so while you'll want to 
decorate each endpoint with ``@doc.tag(...)``, only one of these will
need the description. If you try to set different descriptions for the 
same tag, ``sanic-openapiv3e`` will raise an exception showing the tag
name and the conflicting descriptions.

### Share and reuse common parameters in your app
You probably have some common parameters that appear in many places in 
your API. Days of the week? Pagination where the minimum value must be
greater than zero? OpenAPI v3 has the concept of "components" which can
be shared. Setting them up is easy:


```python
import sanic.request
import sanic.response
from sanic import Sanic
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

# ^^ the line above adds these to OAS v3's "components"
# the next two, which would ordinarily live in your blueprints's module,
# reuse these shared components.
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


app.go_fast()
```

### Deprecate route paths or parameters

A parameter can be marked as ``deprecated=True``:

```python
import sanic
import sanic.request
import sanic.response
from sanic_openapi3e import openapi_blueprint, swagger_blueprint, doc

app = sanic.Sanic(strict_slashes=True)
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)

@app.get("/examples/test_parameter__deprecated/<an_id:int>")
@doc.parameter(
    name="an_id", description="An ID", required=True, _in="path", deprecated=True
)
@doc.summary("A path deprecated parameter")
@doc.description("The parameter should be marked as deprecated")
def param__deprecated(request, an_id: int):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)
    
app.go_fast()
```

as can a whole route with ``@doc.deprecated()``:

```python
import sanic
import sanic.request
import sanic.response
from sanic_openapi3e import openapi_blueprint, swagger_blueprint, doc

app = sanic.Sanic(strict_slashes=True)
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)

@app.get("/examples/test_path__deprecated/<an_id:int>")
@doc.parameter(
    name="an_id",
    description="An ID",
    required=True,
    _in="path",
)
@doc.summary("A path with parameter examples")
@doc.description("This is marked as being deprecated")
@doc.deprecated()
def path__deprecated(request, an_id: int):
    d = locals()
    del d["request"]  # not JSON serializable
    return sanic.response.json(d)
    
app.go_fast()
```

Please note, that while many python decorators can be called without the `()`, this one really
does require the `()` at the end of `@doc.deprecated()`.


### Exclude routes from appearing in the OpenAPI spec (and swagger)

Need to soft-launch an endpoint, or keep your swagger simple? Add a 
`@doc.exclude` and it won't be in the OpenAPI spec at all (unless you
have set your `app.config.SHOW_OPENAPI_EXCLUDED = True` when a 
**second** spec at `/openapi/spec.all.json` will be created which will
have all routes, including excluded. 

```python
import sanic
import sanic.request
import sanic.response
from sanic_openapi3e import openapi_blueprint, swagger_blueprint, doc

app = sanic.Sanic(strict_slashes=True)
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)

@app.get("/test/alpha_release")
@doc.exclude
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
    
app.go_fast()
```

### Configure some of the things

```python
app.config.API_VERSION = '1.0.0'
app.config.API_TITLE = 'An API'
app.config.API_DESCRIPTION = 'An API description'
```

To have a `contact`, set at least one of (but preferably all) 
`app.config.API_CONTACT_NAME`, 
`app.config.API_CONTACT_URL` or
`app.config.API_CONTACT_EMAIL`. 

To have a `license`, `set app.config.API_LICENSE_NAME` and 
optionally `app.config.API_LICENSE_URL` (all str, but the Swagger UI expects this to be a URL).

To have a `termsOfService`, set
`app.config.API_TERMS_OF_SERVICE_URL` (a str, but the Swagger UI 
expects to use this as a URL). 

Setting `components`, `security` and `externalDocs` requires you to 

* first create the relevant objects somewhere in your code (near to 
  where you create the `app`),
* set the appropriate `app.config.OPENAPI_COMPONENTS`, 
  `app.config.OPENAPI_SECURITY`,  
  `app.config.OPENAPI_EXTERNAL_DOCS`.
  
#### Configure how the operationId is made

The default code for creating the operationId creates unique (as they must be) strings from
the following code:

```python
def default_operation_id_fn(method: str, uri: str, route: sanic.router.Route) -> str:
    uri_for_operation_id: str = uri
    for parameter in route.parameters:
      uri_for_operation_id = re.sub(
            "<" + parameter.name + ".*?>", parameter.name, uri_for_operation_id
        )

    return "{}~~{}".format(method.upper(), uri_for_operation_id).replace("/", "~")
```

You can implement your own code (as long as the method signature matches this), and set that to 
be used in the app config:
`app.config.OPENAPI_OPERATION_ID_FN = my_operation_id_fn`

For example, to make `camelCase` operationIds from the Routes' handlers (but be advised you that
you must ensure your handlers' function names are globally unique, not "just" unique within the
Blueprint), you could use the supplied `camel_case_operation_id_fn`:

```python
def camel_case_operation_id_fn(method: str, uri: str, route: sanic.router.Route) -> str:

  if hasattr(route.handler, "__class__") and hasattr(route.handler, "handlers"):
    # These are `sanic.view.CompositeView`s
    _method_handler = route.handler.handlers.get(method.upper())
    if _method_handler:
      handler_name = method + "_" + _method_handler.__name__
    else:
      raise ValueError(f"No {method.upper()} handler found for {uri} handlers: {route.handler.handlers}")
  elif hasattr(route.handler, "__name__"):
    if len(route.methods) > 1:
      # This fn will be called many times, once per method, but we should prefix the handler_name with this
      # prefix to make the operationIds globally unique. If the route is only used by one method, use that
      # handler's name.
      handler_name = method + "_" + route.handler.__name__
    else:
      handler_name = route.handler.__name__
  else:
    raise NotImplementedError()
  return simple_snake2camel(handler_name)
```

and set it like `app.config.OPENAPI_OPERATION_ID_FN = sanic_openapi3e.openapi.camel_case_operation_id_fn`

Note that this does not change the `parameter`'s  names.

**control spec generation**

    hide_openapi_self = app.config.get("HIDE_OPENAPI_SELF", True)
    show_excluded = app.config.get("SHOW_OPENAPI_EXCLUDED", False)
    show_unused_tags = app.config.get("SHOW_OPENAPI_UNUSED_TAGS", False)
    
In practice, you don't usually want to document the `/swagger` nor 
`/openapi` routes, but by setting `app.config.HIDE_OPENAPI_SELF = False`
you can have them appear in the generated spec (and therefore swagger 
too). 

Your `@doc.exclude` annotations are always respected, but if your 
config has `app.config.SHOW_OPENAPI_EXCLUDED = True` then a **second** 
spec at `/openapi/spec.all.json` is created. You generally won't want 
these to be on your production deployment, but you may want it for dev
and test purposes. 

