
import os
import re

base_path = os.path.dirname(__file__) + '/static/build/'

_require_re = re.compile(r'@require +([\w\-./]+) *[\r\n]')


def get_module_dependencies(filename):
    with open(base_path + filename) as f:
        return [m.group(1) for m in _require_re.finditer(f.read())]


def resolve_dependencies(*roots):
    visiting = set()
    visited = set()
    result = []

    def process(filename):
        filename = os.path.normpath('/' + filename)[1:]
        if filename in visited: return
        if filename in visiting:
            raise Exception("Circular dependency with {}".format(filename))
        visiting.add(filename)
        for dep in get_module_dependencies(filename):
            process(dep)
        result.append(filename)
        visiting.remove(filename)
        visited.add(filename)

    for filename in roots:
        process(filename)

    return result


if __name__ == '__main__':
    import sys
    for dep in resolve_dependencies(*sys.argv[1:]):
        print(dep)
