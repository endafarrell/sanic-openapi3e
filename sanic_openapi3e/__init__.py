"""
The sanic_openapi3e module makes creating OpenAPI specs for your endpoints a breeze. See the README.md for more.
"""
from . import doc
from .openapi import blueprint as openapi_blueprint
from .swagger import blueprint as swagger_blueprint

__version__ = "0.9.2"
__all__ = ["openapi_blueprint", "swagger_blueprint", "doc"]
