#!/usr/bin/env bash
# shellcheck source=/dev/null enable=all disable=SC2250

set -e -u -o pipefail

base_dir=$(dirname "$0")
base_dir=$(readlink -fv "$base_dir")

# shellcheck disable=SC2016
help='Usage: ./x [COMMON-OPTIONS] X-COMMAND ...

Common options:

  -W
    Enables Python warnings. (PYTHONWARNINGS=always)

  --venv-activate
    Starts Python with "source .venv/bin/activate" instead of "uv run".
    Use it when the repository owner is not the running user (e.g. www-data).
    Works with ./x commands: python, python3, FILE.py, cron, log, serve

  --coverage-run
    Collects Python code coverage data.
    Similar to "./x coverage run FILE.py", but affects all subprocesses.
    Use "./x coverage combine [--append]" and "./x coverage html" to render it.
    Works with ./x commands: python, python3, FILE.py, cron, log, serve

Commands:

  ./x install [OPTIONS]
    Downloads dependencies to "./.venv" (Py) and "./node_modules" (JS).
    It'\''s best to rerun it after every "git pull" in case they were updated.
    Options:
      --uv={local|system}      use system-wide uv or download it locally
      --nodejs={local|system}  use system-wide Node.js or download it locally
      --pnpm={local|system}    use system-wide pnpm or download it locally
      --prod-deps              install prod-only dependencies (e.g. saml)
      --no-dev-deps            omit dev-only dependencies (e.g. eslint)
      --clean                  reinstall everything from scratch

  ./x upgrade-py
  ./x upgrade-js
  ./x upgrade
    Upgrades {Python|JavaScript|both} dependencies to the latest versions.

  ./x uv UV-COMMAND [ARGS]
    Runs uv (the Python package manager).
    See https://docs.astral.sh/uv/reference/cli/

  ./x run [UV-OPTIONS] PROGRAM [ARGS]
    Alias for "./x uv run".
    Downloads Python dependencies to ".venv/" if uv.lock has changed.
    Runs PROGRAM with ".venv/bin" added to its $PATH.

  ./x python [ARGS]
  ./x python3 [ARGS]
  ./x FILE.py [ARGS]
    Runs Python, using dependencies in "./.venv".
    See https://docs.python.org/3/using/cmdline.html
    Uses "uv run" by default, but see --venv-activate and --coverage-run.

  ./x node [ARGS]
    Runs Node.js (the server-side JavaScript runtime).
    See https://nodejs.org/api/cli.html

  ./x pnpm PNPM-COMMAND [ARGS]
  ./x pnpx NPM-PACKAGE [ARGS]
    Runs pnpm (the JavaScript package manager).
    See https://pnpm.io/pnpm-cli

  ./x lint
    Checks for code warnings.

  ./x format
    Autoformats code.

  ./x build-docs
    Generates HTML API docs from source code docstrings.

  ./x coverage COVERAGE-COMMAND [ARGS]
    Runs Coverage.py.
    See https://coverage.readthedocs.io/en/latest/commands/
    Notable commands:
      ./x coverage run something.py
      ./x --coverage-run something.py (see above)
      ./x coverage combine [--append]
      ./x coverage html

  ./x serve [SERVE-OPTIONS]
    Runs the Python HTTP server.
    Options:
      --bind=ADDRESS           listen on X.X.X.X:N or unix:/PATH
                                 (default: 127.0.0.1:5000)
      --no-debug               don'\''t show tracebacks on exception pages
      --no-static              don'\''t serve /static/
      --no-watch-js            don'\''t rebuild JS/CSS files on change
      --no-watch-py            don'\''t reload Python code on change
      --proxy-fix              read X-Forwarded-... headers
      --https                  serve HTTPS with a self-signed cert
      --root-path=PREFIX       URL path prefix
      --access-logfile=FILE    where to write access logs (default: stderr)
      --error-logfile=FILE     where to write error logs (default: stderr)
      --log-level=LEVEL        verbosity (ERROR, WARNING, INFO, DEBUG)
      --log-label=NAME         name of this process for logs

  ./x cron
    Runs periodic processing and cleanup of sessions and log files.

  ./x log tag +TAGNAME1 -TAGNAME2 SESSID1:LINENO1 SESSID2:LINENO2 ...
    Adds or removes tags to the given row(s) in the error log database.

  ./x log view SESSID-OR-FILENAME
    Pretty-prints the log file in a pager.
    Options:
      -c, --color           print colored output

  ./x log path SESSID1 SESSID2 ...
    Prints the log filename for each sessid. Only rarely useful.

  ./x log process FILENAME...
    Scans log files for errors and adds them to the error log database.
    Usually done by cron. This command is only for manual testing.

  ./x log list [PATTERN] ...
    Lists rows in the error logs database.
    Options:
      -n, --not PATTERN     do not select lines matching PATTERN
      -F, --from YYYYMMDD   match only lines logged since the given date
      -T, --to YYYYMMDD     match only lines logged until the given date
      -c, --color           print colored output
      -s, --sessids         print list of matching sessids
      -l, --linenos         print list of matching sessid:linenos
      -f, --files           print list of matching filenames
'

normal=$'\e[0m'
bright=$'\e[1m'
red=$'\e[31m'
yellow=$'\e[33m'
blue=$'\e[34m'

log() {
  echo >&2 "${bright}${yellow}>>> ${normal}${yellow}${1}${normal}"
}

log_and_run() {
  echo >&2 "${bright}${yellow}>>> ${normal}${yellow}${1}Running: ${blue}${2}${normal}"
  eval "$2"
}

add_uv_path() {
  if [[ -d "$base_dir/.x_local_uv_env" ]]; then
    PATH=$base_dir/.x_local_uv_env:$PATH
  fi
}

log_and_cd_to_basedir() {
  if [[ "$PWD" != "$base_dir" ]]; then
    log_and_run "" "cd ${base_dir@Q}"
  fi
}

install_local_node() {
  if [[ -e .venv/bin/node && "$(.venv/bin/node --version || true)" == "$(< .node-version)" ]]; then
    log "Local node is already the correct version. Reusing it."
  else
    if [[ -d .venv/lib/node_modules ]]; then
      log_and_run "Deleting the previous node version. " "rm -rf .venv/lib/node_modules"
    fi
    log_and_run "Installing nodeenv. " "uv pip install nodeenv"
    log_and_run "Installing local node. " "uv run nodeenv -p"
    log_and_run "Cleaning up unnecessary files. " "rm -rf .venv/include/node .venv/src/node*"
    log_and_run "Uninstalling nodeenv. " "uv pip uninstall nodeenv"
  fi
}

install_local_pnpm() {
  if [[ -e .venv/bin/pnpm && -e .venv/lib/node_modules/pnpm && "$(uv run pnpm --version || true)" == "$(< .pnpm-version)" ]]; then
    log "Local pnpm is already the correct version. Reusing it."
  else
    log_and_run "Installing local pnpm to './.venv'. " "uv run npm install 'pnpm@$(< .pnpm-version)' -g --prefix=.venv"
  fi
}

exec_using_venv_activate() {
  source "$base_dir/.venv/bin/activate"
  exec "$@"
}

exec_using_uv_with_coverage() {
  # - See https://coverage.readthedocs.io/en/latest/subprocess.html
  # - The docs have a section that says you should create a .pth file, but
  #   that's out of date. The requisite .pth file is now included with Coverage.
  # - ".coveragerc" is a special value - it reads "pyproject.toml" too.
  export COVERAGE_PROCESS_START=.coveragerc
  add_uv_path
  exec uv run --with coverage "$@"
}

exec_using_uv() {
  add_uv_path
  exec uv run "$@"
}

python_exec_mode=exec_using_uv

while true; do
  case "${1:-}" in
  -W) shift; export PYTHONWARNINGS=always;;
  --venv-activate) shift; python_exec_mode=exec_using_venv_activate;;
  --coverage-run) shift; python_exec_mode=exec_using_uv_with_coverage;;
  *) break;;
  esac
done

case "${1:-}" in
run) set -- uv "$@";;
coverage) set -- uv run --with coverage "$@";;
*.py) set -- python3 "$@";;
cron) shift; set -- python3 -Pm votrfront.cron "$@";;
log) shift; set -- python3 -Pm votrfront.logutil "$@";;
serve) shift; set -- python3 -Pm votrfront.serve "$@";;
*) ;;
esac

command=${1:---help}
shift || true

case "$command" in
--help)
  echo -n "$help" >&2
  ;;

uv)
  add_uv_path
  exec uv "$@"
  ;;

node | pnpm | pnpx)
  exec_using_venv_activate "$command" "$@"
  ;;

python | python3)
  "$python_exec_mode" "$command" "$@"
  ;;

upgrade-py)
  log_and_cd_to_basedir
  printf -v uvcmd ' %q' uv sync --upgrade "$@"
  log_and_run "Upgrading Python dependencies. " "./x$uvcmd"
  ;;

upgrade-js)
  log_and_cd_to_basedir
  add_uv_path

  # See also https://github.com/nodejs/nodejs-dist-indexer
  log_and_run "Determining latest Node.js version. " "curl -fsSL https://nodejs.org/download/release/index.tab | sed -n '2s/\t.*//p' > .node-version"

  # The filename ".pnpm-version" is not standard. Only ./x uses it.
  log_and_run "Determining latest pnpm version. " "./x pnpm view pnpm version > .pnpm-version"

  if ! [[ -e .venv/bin/node ]]; then
    log "Using system-wide node. Therefore an update won't be attempted."
  else
    install_local_node
  fi

  if ! [[ -e .venv/bin/pnpm || -L .venv/bin/pnpm ]]; then
    log "Using system-wide pnpm. Therefore an update won't be attempted."
  else
    install_local_pnpm
  fi

  log_and_run "Upgrading JavaScript: minor versions of all dependencies. " "./x pnpm update"
  log_and_run "Upgrading JavaScript: major versions of chosen direct dependencies, and minor versions of their dependencies. " "./x pnpm update --latest --interactive"
  ;;

upgrade)
  log_and_cd_to_basedir
  ./x upgrade-py
  ./x upgrade-js
  ;;

lint)
  log_and_cd_to_basedir
  combined_status=0
  lint_run() {
    # shellcheck disable=SC2310 # `&& true` intentionally disarms `set -e` within log_and_run
    log_and_run "$@" && true
    status=$?
    if (( status )); then
      combined_status=$status
      echo >&2 "${bright}${red}>>> ${normal}${red}Failed with status ${status}.${normal}"
    fi
  }
  lint_run "Checking Prettier formatting. " "./x pnpm prettier --check ."
  lint_run "Checking TypeScript. " "./x pnpm tsc --noEmit"
  lint_run "Checking ESLint. " "./x pnpm eslint ."
  lint_run "Checking Python types with Pyrefly. " "./x run pyrefly check"
  lint_run "Checking Python types with basedpyright. " "./x pnpm basedpyright"
  exit "$combined_status"
  ;;

format)
  log_and_cd_to_basedir
  log_and_run "" "./x pnpm prettier --write ."
  ;;

build-docs)
  log_and_cd_to_basedir
  log_and_run "" "./x uv run --with sphinx,sphinx-rtd-theme make -C docs html"
  ;;

install)
  # Detect which options were used last time, if any.
  olduv=system
  oldnodejs=system
  oldpnpm=system
  [[ -e "$base_dir/.x_local_uv_env/uv" ]] && olduv=local
  [[ -e "$base_dir/.venv/bin/node" ]] && oldnodejs=local
  [[ -e "$base_dir/.venv/bin/pnpm" ]] && oldpnpm=local

  # Parse arguments.
  uv=$olduv
  nodejs=$oldnodejs
  pnpm=$oldpnpm
  clean=
  proddeps=
  devdeps=y
  for arg; do
    case "$arg" in
    --uv=system | --uv=local) uv=${arg#*=} ;;
    --nodejs=system | --nodejs=local) nodejs=${arg#*=} ;;
    --pnpm=system | --pnpm=local) pnpm=${arg#*=} ;;
    --clean) clean=y ;;
    --no-clean) clean= ;;
    --prod-deps) proddeps=y ;;
    --no-prod-deps) proddeps= ;;
    --dev-deps) devdeps=y ;;
    --no-dev-deps) devdeps= ;;
    *)
      echo >&2 "Unknown option: $arg"
      exit 1
      ;;
    esac
  done

  uvsyncopts=
  pnpmopts=
  if [[ -n $proddeps ]]; then
    uvsyncopts+=' --group prod'
  fi
  if [[ -n $devdeps ]]; then
    # It's better to use --dev than using --no-dev and putting "dev" in
    # tool.uv.default-groups. `uv run` is asymmetric: it automatically installs
    # packages it thinks are missing, but it won't uninstall packages that seem
    # unnecessary. So this makes `uv run` obey the last `uv sync`.
    # Related: https://github.com/astral-sh/uv/issues/12558
    uvsyncopts+=' --dev'
  else
    pnpmopts+=' --production'
  fi

  trap 'if (( $? )); then echo >&2 "${bright}${red}>>> Failed!${normal}"; fi' EXIT

  log_and_cd_to_basedir

  if [[ "$clean" == y ]]; then
    log_and_run "Deleting the previous installation. " "rm -rf .x_local_uv_env .venv node_modules"
    # votrfront/local_settings.py is never reset, even if --clean is on.
  elif [[ -d .venv ]] && [[ "$uv" != "$olduv" || "$nodejs" != "$oldnodejs" || "$pnpm" != "$oldpnpm" ]]; then
    log_and_run "Deleting .venv because options have changed. " "rm -rf .venv"
  fi

  if [[ -d .x_local_uv_env ]]; then
    log_and_run "" "rm -rf .x_local_uv_env"
  fi

  if [[ $uv == system ]]; then
    log "Using system uv."
    uv --version
  else
    log_and_run "Installing local uv. " "curl -LsSf https://astral.sh/uv/install.sh | env UV_UNMANAGED_INSTALL=.x_local_uv_env sh"
    add_uv_path
  fi

  if [[ -d .venv ]]; then
    log "./.venv already exists. Reusing it."
  fi

  log_and_run "Installing Python dependencies to './.venv'. " "uv sync$uvsyncopts"

  if [[ $nodejs == system ]]; then
    log "Using system node."
    node --version
  else
    install_local_node
  fi

  if [[ $pnpm == system ]]; then
    log "Using system pnpm."
    pnpm --version
  else
    install_local_pnpm
  fi

  if [[ -d node_modules ]]; then
    log "./node_modules already exists. Reusing it."
  fi

  log_and_run "Installing JavaScript dependencies to './node_modules'. " "uv run pnpm install$pnpmopts"

  if [[ -f votrfront/local_settings.py ]]; then
    log "votrfront/local_settings.py already exists. Keeping it."
  else
    log "Creating votrfront/local_settings.py."
    printf "'''Add custom settings here. Defaults can be seen in default_settings.py.'''\nfrom .default_settings import *\n" > votrfront/local_settings.py
  fi

  log "Success!"
  ;;

-*)
  echo >&2 "Unknown option: $command"
  echo >&2 "Try: $0 --help"
  exit 1
  ;;

*)
  echo >&2 "Unknown command: $command"
  echo >&2 "Try: $0 --help"
  exit 1
  ;;
esac
