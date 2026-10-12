import json
import time
from starlette.exceptions import HTTPException
from typing import TYPE_CHECKING
from votrfront.base import var_path

if TYPE_CHECKING:
    from starlette.requests import Request
    from votrfront.base import VotrState


def check_header(request: Request[VotrState], name: str, allowed_values: set[str]) -> None:
    value = request.headers.get(name)
    if value is not None and value not in allowed_values:
        # TODO: Temporary log. Decide what to do with it once we see the data.
        # Either remove it or make it per-month. Maybe merge with reportlogs.
        payload = {
            'type': 'fetchmeta',
            'name': name,
            'value': value,
            'allowed_values': sorted(allowed_values),
            'time': int(time.time()),
            'url': str(request.url),
            'client': request.scope['client'],
            'headers': [
                [k.decode('latin1'), v.decode('latin1')]
                for k, v in request.scope['headers']
            ],
        }
        with var_path('fetchmetalog').open('at') as f:
            f.write(json.dumps(payload, sort_keys=True) + '\n')

        raise HTTPException(403, f'Unexpected {name} header value')
