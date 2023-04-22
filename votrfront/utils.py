
import json
import time
from werkzeug.exceptions import Forbidden


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
            'request': { k: v for k, v in request.environ.items() if isinstance(v, (int, str, bool)) },
        }
        with open(request.app.var_path('fetchmetalog'), 'at') as f:
            f.write(json.dumps(payload, sort_keys=True) + '\n')

        raise Forbidden('Unexpected %s header value' % name)
