
import json
from werkzeug.routing import Rule
from werkzeug.wrappers import Response


content = '''
<!DOCTYPE html>
<meta charset="UTF-8">
<title>Votr</title>
<link rel="stylesheet" type="text/css" href="static/style.css">
<div id="votr"></div>
<noscript>JavaScript required.</noscript>
<script>/*INSERT*/</script>
<script src="static/jquery.js"></script>
<script src="static/main.js"></script>
'''.lstrip()
# TODO: add some nice noscript content for search engines etc.


def front(request):
    my_data = {}
    # TODO: add relevant settings to my_data.

    my_content = content.replace('/*INSERT*/',
        'Votr = ' + json.dumps(my_data).replace('</', '<\\/'))
    return Response(my_content, content_type='text/html; charset=UTF-8')


def die(request):
    # allows easy access to debugger on /500 if it's enabled.
    raise Exception()


def get_routes():
    yield Rule('/', methods=['GET'], endpoint=front)
    yield Rule('/500', endpoint=die)
