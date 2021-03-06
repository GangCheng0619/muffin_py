"""Muffin is a web framework to build ASGI applications."""

# Package information
# ===================

__version__ = "0.86.0"
__project__ = "muffin"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "MIT"

from asgi_tools import (  # noqa
    Request, Response, ResponseText, ResponseHTML, ResponseJSON, ResponseError,
    ResponseFile, ResponseRedirect, ResponseStream, ResponseSSE, ResponseWebSocket,
    ASGIMethodNotAllowed, ASGINotFound, ASGIConnectionClosed, ASGIError)
from asgi_tools.tests import ASGITestClient as TestClient  # noqa


class MuffinException(ASGIError):

    """Base class for Muffin Errors."""

    pass


CONFIG_ENV_VARIABLE = 'MUFFIN_CONFIG'


from .app import Application    # noqa
from .handler import Handler    # noqa
