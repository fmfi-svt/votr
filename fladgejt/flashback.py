import gzip
import json
import os
import sys
import time
from fladgejt.base import BaseClient

_STATEFUL = {
    "prihlas_na_termin",
    "odhlas_z_terminu",
    "zapis_plan_pridaj_predmety",
    "zapis_ponuka_pridaj_predmety",
    "zapis_odstran_predmety",
    "create_zapisny_list",
}

def _tuplify(obj):
    if isinstance(obj, (list, tuple)):
        return tuple(_tuplify(mem) for mem in obj)
    return obj

def _load_log(filename):
    rpcs = []
    current_rpc_name = None
    current_rpc_args = None
    fake_time_msec = None

    with (gzip.open(filename) if filename.endswith('.gz') else open(filename, 'rb')) as f:
        for line in f:
            line = json.loads(line)
            if line[1] == "rpc":
                if fake_time_msec is None:
                    fake_time_msec = int(line[0] * 1000)
                words = line[2].split(" ")
                if words[2] == "started":
                    current_rpc_name = words[1]
                    current_rpc_args = _tuplify(line[3])
                if words[2] == "finished":
                    assert words[1] == current_rpc_name
                    rpcs.append((current_rpc_name, current_rpc_args, (True, line[3])))
                if words[2] == "failed":
                    assert words[1] == current_rpc_name
                    rpcs.append((current_rpc_name, current_rpc_args, (False, line[3])))

    grouped = {}
    last_stateful = None
    for i, (name, args, outcome) in enumerate(rpcs):
        if (name, args) not in grouped:
            grouped[(name, args)] = [(None, outcome)]
        elif grouped[(name, args)][-1][1] != outcome:
            grouped[(name, args)].append((rpcs[last_stateful][0:2], outcome))

        if name in _STATEFUL:
            last_stateful = i

    print("=====", file=sys.stderr)
    for key in sorted(grouped):
        print("- %s%r" % key, file=sys.stderr)
        for condition, outcome in grouped[key]:
            if condition != None:
                print("  - changes after %s%r" % condition, file=sys.stderr)

    return fake_time_msec, grouped

class TimeParadoxError(Exception):
    pass

class ReplayedError(Exception):
    pass

class FlashbackClient(BaseClient):
    def __init__(self, context, flashbacks_dir, file):
        super().__init__(context)
        if not os.path.exists(flashbacks_dir):
            raise Exception("Flashbacks are unavailable: %r does not exist" % flashbacks_dir)
        if not os.path.isdir(flashbacks_dir):
            raise Exception("Flashbacks are unavailable: %r is not a directory" % flashbacks_dir)
        if not file:
            if not os.listdir(flashbacks_dir):
                raise Exception("Flashbacks are unavailable: %r is empty" % flashbacks_dir)
            raise Exception("No flashback file selected")
        if '/' in file or '\\' in file or file.startswith('.'):
            raise Exception("Bad filename: %r" % file)
        filename = os.path.join(flashbacks_dir, file)
        if not os.path.isfile(filename):
            raise Exception("%r does not exist" % filename)

        self.fake_time_msec, self._rpcs = _load_log(filename)
        self._did = set()

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)

        def rpc_method(*args):
            args = _tuplify(args)
            found = self._rpcs.get((name, args))
            if not found:
                raise TimeParadoxError("RPC %s%r did not happen in the flashback" % (name, args))
            self._did.add((name, args))
            outcome = None
            self.context.log("flashback", "%s candidates" % len(found))
            for (condition, outcome_candidate) in found:
                if condition == None:
                    outcome = outcome_candidate
                elif condition in self._did:
                    self.context.log("flashback", "%s%r already happened" % condition)
                    outcome = outcome_candidate
                else:
                    self.context.log("flashback", "%s%r did not happen yet" % condition)

            # TODO: Configurable sleep.
            time.sleep(0.5)

            success, result = outcome
            if success:
                return result
            else:
                raise ReplayedError(result)

        return rpc_method
