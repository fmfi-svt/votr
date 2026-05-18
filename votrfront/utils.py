import json
import time
from starlette.exceptions import HTTPException
from votrfront.base import var_path


def check_header(request, name, allowed_values):
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
