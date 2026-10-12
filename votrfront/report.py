import json
import time
from datetime import datetime, UTC
from starlette.routing import Route
from starlette.responses import PlainTextResponse
from starlette.exceptions import HTTPException
from votrfront.base import var_path
from votrfront.sessions import get_sessid_from_cookie
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.requests import Request
    from votrfront.base import VotrState


async def report(request: Request[VotrState]) -> PlainTextResponse:
    try:
        body = await request.json()
        type = request.query_params['type']
    except Exception as e:
        raise HTTPException(400, repr(e)) from e

    payload = {
        'body': body,
        'type': type,
        'ua': request.headers.get('user-agent', ''),
        'sessid': get_sessid_from_cookie(request),
        'time': int(time.time()),
    }

    filename = datetime.now(UTC).strftime('%Y%m')
    with var_path('reportlogs', filename).open('at') as f:
        f.write(json.dumps(payload, sort_keys=True) + '\n')
    return PlainTextResponse('OK')


routes = [
    Route('/report', methods=['POST'], endpoint=report),
]
