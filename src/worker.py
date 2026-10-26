"""Cloudflare Python Worker adapter for the existing Gargand Flask application.

Secrets are provided as Worker bindings and copied into os.environ before app.py
is imported, so Flask never needs credentials committed into the repository.
"""
import base64
import importlib
import mimetypes
import os
from pathlib import PurePosixPath

from flask import Response, request
from jinja2 import BaseLoader, TemplateNotFound
from pyodide.ffi import run_sync
from workers import WorkerEntrypoint, wsgi

ENV_KEYS = (
    "ADMIN_DISCORD_USER_IDS",
    "ADMIN_PASSWORD",
    "DATABASE_URL",
    "DISCORD_BOT_TOKEN",
    "DISCORD_CLIENT_ID",
    "DISCORD_CLIENT_SECRET",
    "DISCORD_REDIRECT_URI",
    "DISCORD_TOKEN",
    "GARGAND_BOT_TOKEN",
    "GARGAND_BRIDGE_SECRET",
    "GARGAND_YOUTUBE_CHANNEL_ID",
    "INVITE_URL",
    "NIGHTFALL_BRIDGE_SECRET",
    "NIGHTFALL_YOUTUBE_CHANNEL_ID",
    "OPENROUTER_API_KEY",
    "OPENROUTER_TEXT_MODEL",
    "ROBLOX_BRIDGE_SECRET",
    "ROBLOX_OAUTH_CLIENT_ID",
    "ROBLOX_OAUTH_CLIENT_SECRET",
    "ROBLOX_OAUTH_REDIRECT_URI",
    "SESSION_SECRET",
)

_site_module = None
_flask_app = None


def _worker_assets():
    worker_env = request.environ.get("workers.env")
    return getattr(worker_env, "ASSETS", None) if worker_env is not None else None


def _asset_bytes(path):
    assets = _worker_assets()
    if assets is None:
        return None
    safe_path = str(path or "").replace("\\", "/").lstrip("/")
    parts = PurePosixPath(safe_path).parts
    if not safe_path or any(part in ("", ".", "..") for part in parts):
        return None
    response = run_sync(assets.fetch("https://assets.local/" + safe_path))
    if response.status < 200 or response.status >= 300:
        return None
    return run_sync(response.bytes())


class CloudflareTemplateLoader(BaseLoader):
    """Load Jinja templates from the Worker Static Assets binding."""

    def get_source(self, environment, template):
        name = str(template or "").replace("\\", "/")
        parts = PurePosixPath(name).parts
        if not name or name.startswith("/") or any(part in ("", ".", "..") for part in parts):
            raise TemplateNotFound(template)
        content = _asset_bytes("templates/" + name)
        if content is None:
            raise TemplateNotFound(template)
        source = content.decode("utf-8")
        return source, name, lambda: True


def _static_file(filename):
    content = _asset_bytes("static/" + filename)
    if content is None:
        return Response("Asset not found", status=404, mimetype="text/plain")
    response = Response(content, mimetype=mimetypes.guess_type(filename)[0] or "application/octet-stream")
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["X-Gargand-Edge"] = "Cloudflare"
    return response


def _lion_image():
    encoded = _asset_bytes("static/gargand-pfp.jpg.b64")
    if encoded:
        try:
            body = base64.b64decode(encoded.strip(), validate=True)
            return Response(body, mimetype="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})
        except ValueError:
            pass
    fallback = _asset_bytes("static/gargand-mark.svg")
    if fallback:
        return Response(fallback, mimetype="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})
    return Response("GARGAND image unavailable", status=404, mimetype="text/plain")


def _gold_bar():
    encoded = _asset_bytes("static/gargand-gold-bar.gif.b64")
    if not encoded:
        return Response("GARGAND image unavailable", status=404, mimetype="text/plain")
    try:
        body = base64.b64decode(encoded.strip(), validate=True)
    except ValueError:
        return Response("GARGAND image unavailable", status=404, mimetype="text/plain")
    return Response(body, mimetype="image/gif", headers={"Cache-Control": "public, max-age=86400"})


def _load_flask_app(env):
    global _site_module, _flask_app
    if _flask_app is not None:
        return _flask_app

    # Runtime bindings take precedence. Missing optional bindings are removed so
    # that build-time values cannot accidentally masquerade as runtime secrets.
    for key in ENV_KEYS:
        try:
            value = getattr(env, key, None)
        except Exception:
            value = None
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = str(value)

    _site_module = importlib.import_module("app")
    site = _site_module
    flask_app = site.app
    flask_app.jinja_env.loader = CloudflareTemplateLoader()
    flask_app.jinja_env.auto_reload = False

    if "static" in flask_app.view_functions:
        flask_app.view_functions["static"] = _static_file
    site.gargand_lion_asset = _lion_image
    site.gargand_bar_asset = _gold_bar
    flask_app.view_functions["gargand_lion_asset"] = _lion_image
    flask_app.view_functions["gargand_bar_asset"] = _gold_bar

    _flask_app = flask_app
    return _flask_app


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        flask_app = _load_flask_app(self.env)
        return await wsgi.fetch(flask_app, request, self.env)
