
import os
import re
from collections import defaultdict

base_path = os.path.join(os.path.dirname(__file__), 'static/build/')

_use_re = re.compile(r'\bVotr\.(\w+)')
_define_re = re.compile(r'\bVotr\.(\w+)\s*=')
_dontdepend_re = re.compile(r'@dontdepend +Votr\.(\w+)')


def find_dependencies():
    defines = defaultdict(set)
    uses = defaultdict(set)
    dontdepend = set()
    dependencies = defaultdict(set)

    for dirpath, dirnames, filenames in os.walk(base_path):
        for filename in filenames:
            if not filename.endswith('.js'): continue
            module_path = os.path.join(dirpath, filename)
            module_name = module_path[len(base_path):]

            with open(module_path, encoding='ascii', errors='replace') as f:
                content = f.read()

            for match in  _use_re.finditer(content):
                uses[module_name].add(match.group(1))
            for match in _define_re.finditer(content):
                defines[match.group(1)].add(module_name)
            for match in _dontdepend_re.finditer(content):
                dontdepend.add(match.group(1))

        dirnames[:] = [name for name in dirnames if not name.startswith('.')]

    for var, sources in defines.items():
        if var in dontdepend: continue
        if len(sources) > 1:
            raise Exception("Multiple files assign to {}: {}".format(
                var, ', '.join(sources)))

    for module_name, vars in uses.items():
        for var in vars:
            if var in dontdepend: continue
            if var not in defines:
                raise Exception("{} uses {} which isn't set anywhere".format(
                    module_name, var))
            [source_name] = defines[var]
            if source_name == module_name: continue
            yield (module_name, source_name, var)


def order_dependencies(*roots):
    dependencies = defaultdict(set)
    for filefrom, fileto, var in find_dependencies():
        dependencies[filefrom].add(fileto)

    visiting = set()
    visited = set()
    stack = []
    result = []

    def process(filename):
        if filename in visited: return
        stack.append(filename)
        if filename in visiting:
            raise Exception("Circular dependencies: " + " -> ".join(stack))
        visiting.add(filename)
        for dep in sorted(dependencies[filename]):
            process(dep)
        result.append(filename)
        visited.add(filename)
        visiting.remove(filename)
        stack.pop()

    for filename in roots:
        process(filename)

    return result


if __name__ == '__main__':
    import sys
    argv = sys.argv[1:]
    if argv == ['--deps']:
        for filefrom, fileto, var in sorted(find_dependencies()):
            print("{} -> {} ({})".format(filefrom, fileto, var))
    elif argv == ['--dot']:
        print("digraph jsdeps {")
        for filefrom, fileto, var in sorted(find_dependencies()):
            print('"{}" -> "{}" [label="{}"];'.format(filefrom, fileto, var))
        print("}")
    elif argv and all(os.path.exists(base_path + name) for name in argv):
        for dep in order_dependencies(*argv):
            print(dep)
    else:
        print("Usage:", sys.argv[0], "{--deps|--dot|main.js}", file=sys.stderr)
