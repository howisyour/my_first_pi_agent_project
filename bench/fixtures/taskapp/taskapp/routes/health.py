"""Health check."""

from taskapp import __version__
from taskapp.constants import HTTP_OK


def health(store, request):
    return HTTP_OK, {"status": "ok", "version": __version__}
