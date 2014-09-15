
import json
from werkzeug.routing import Rule
from werkzeug.wrappers import Response
from .jsdeps import resolve_dependencies


content = '''
<!DOCTYPE html>
<meta charset="UTF-8">
<title>Votr</title>
<link rel="stylesheet" type="text/css" href="static/style.css">
<div id="votr"></div>
<noscript>JavaScript required.</noscript>
<script>/*INSERT*/</script>
'''.lstrip()
# TODO: add some nice noscript content for search engines etc.

for script in resolve_dependencies('main.js'):
    content += '<script src="static/build/{}"></script>\n'.format(script)


def front(request):
    my_data = {}
    my_data['url_root'] = request.url_root
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
