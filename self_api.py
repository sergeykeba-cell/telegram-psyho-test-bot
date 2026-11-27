"""Self-check scoring API. Stateless: nothing is stored, request bodies and user ids are never logged."""
import json
import logging

from aiohttp import web

from self_scoring import ScoreError, score

HOST = "127.0.0.1"
PORT = 8083
MAX_BODY = 16 * 1024

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("self_api")

HEADERS = {"Cache-Control": "no-store"}


def _err(status, msg):
    return web.json_response({"error": msg}, status=status, headers=HEADERS)


async def handle_score(request):
    if request.content_type != "application/json":
        return _err(415, "content type must be application/json")
    try:
        data = json.loads(await request.read())
    except (ValueError, UnicodeDecodeError):
        return _err(400, "invalid json")
    if not isinstance(data, dict):
        return _err(400, "invalid json")
    try:
        result = score(data.get("test"), data.get("answers"), data.get("sex"))
    except ScoreError as e:
        return _err(400, str(e))
    except Exception:
        # no exc_info and no input in the log line: it could contain answers
        log.error("unexpected scoring failure")
        return _err(500, "internal error")
    return web.json_response(result, headers=HEADERS)


def make_app():
    app = web.Application(client_max_size=MAX_BODY)
    app.router.add_post("/self-api/score", handle_score)
    return app


if __name__ == "__main__":
    web.run_app(make_app(), host=HOST, port=PORT, access_log=None, print=None)
