#!/usr/bin/env bash
# shellcheck enable=all disable=SC2250

set -e -u -o pipefail

base_dir=$(dirname "$0")
base_dir=$(readlink -fv "$base_dir")

help1='Usage: ./x [COMMON-OPTIONS] X-COMMAND ...

Common options:

  -W
    Enables Python warnings. (PYTHONWARNINGS=always)

Commands:

  ./x install [OPTIONS]
    Downloads dependencies to "./.venv" (Py) and "./node_modules" (JS).
    It'\''s best to rerun it after every "git pull" in case they were updated.
    Options:
      --uv={local|system}      use system-wide uv or download it locally
      --nodejs={local|system}  use system-wide Node.js or download it locally
      --pnpm={local|system}    use system-wide pnpm or download it locally
      --prod-deps              install prod-only dependencies (e.g. gunicorn)
      --no-dev-deps            omit dev-only dependencies (e.g. eslint)
      --clean                  reinstall everything from scratch
'

# shellcheck disable=SC2016
help2='
  ./x upgrade-py
  ./x upgrade-js
  ./x upgrade
    Upgrades {Python|JavaScript|both} dependencies to the latest versions.

  ./x uv COMMAND [ARGS]
    Runs uv. See https://docs.astral.sh/uv/reference/cli/

  ./x run [UV-OPTIONS] PROGRAM [ARGS]
    Alias for "./x uv run".
    Downloads Python dependencies to ".venv/" if uv.lock has changed.
    Runs PROGRAM with ".venv/bin" added to its $PATH.

  ./x console.py [ARGS]   (or any other *.py file)
  ./x python [ARGS]
  ./x python3 [ARGS]
  ./x node [ARGS]
  ./x pnpm [ARGS]
  ./x pnpx [ARGS]
    Alias for "./x uv run ...".

  ./x lint
    Checks for code warnings.

  ./x format
    Autoformats code.

  ./x build-docs
    Generates HTML API docs from source code docstrings.

  ./x coverage [COVERAGE-COMMAND] [ARGS]
    Runs Coverage.py. See https://coverage.readthedocs.io/en/latest/commands/
    Notable commands:
      ./x coverage run something.py
      ./x coverage combine [--append]
      ./x coverage html

  ./x coverage-serve [SERVE-OPTIONS]
    Runs "./x serve ..." with Coverage.py.

  ./x watch-and-serve [SERVE-OPTIONS]
    Runs both "./x pnpm watch" (JavaScript bundler) and "./x serve ..."
    (Python development server) in parallel.

  ./x watch-and-coverage-serve [SERVE-OPTIONS]
    Runs both "./x pnpm watch" (JavaScript bundler) and "./x coverage-serve ..."
    (Python development server with Coverage.py) in parallel.
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

while true; do
  case "${1:-}" in
  -W) shift; export PYTHONWARNINGS=always;;
  *) break;;
  esac
done

command=${1:---help}
shift || true

case "$command" in
--help)
  if [[ -d "$base_dir/.venv" ]]; then
    echo >&2 "$help1$help2"
    "$0" console.py 2>&1 | sed '/^usage:$/d; s!^  console.py!  ./x!' >&2
  else
    echo >&2 "$help1"
    echo >&2 'More commands will be available after running "./x install".'
  fi
  ;;

uv)
  add_uv_path
  exec uv "$@"
  ;;

run)
  add_uv_path
  exec uv run "$@"
  ;;

node | python | python3 | pnpm | pnpx | *.py)
  add_uv_path
  exec uv run "$command" "$@"
  ;;

serve | cron | log)
  add_uv_path
  exec uv run "$base_dir/console.py" "$command" "$@"
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

watch-and-serve | watch-and-coverage-serve)
  exec bash -c "env --default-signal ${0@Q} ${command#watch-and-} ${*@Q} & ${0@Q} pnpm watch"
  ;;

coverage)
  add_uv_path
  exec uv run --with coverage coverage "$@"
  ;;

coverage-serve)
  add_uv_path
  # https://coverage.readthedocs.io/en/latest/subprocess.html
  # https://github.com/dougn/coverage_pth/pull/7
  # ".coveragerc" is a special value, it reads "pyproject.toml" too.
  export COVERAGE_PROCESS_START=.coveragerc
  exec uv run --with coverage,git+https://github.com/TomiBelan/coverage_pth "$base_dir/console.py" serve "$@"
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
