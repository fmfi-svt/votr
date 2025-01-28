#!/usr/bin/env bash
# shellcheck disable=SC2250

set -e -u -o pipefail

base_dir=$(dirname "$0")
base_dir=$(readlink -fv "$base_dir")

help1='Usage:

  ./x install [OPTIONS]
    Downloads dependencies to "./.venv" (Py) and "./node_modules" (JS).
    It'\''s best to rerun it after every "git pull" in case they were updated.
    Options:
      --uv={local|system}      use system-wide uv or download it locally
      --nodejs={local|system}  use system-wide Node.js or download it locally
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
  ./x corepack [ARGS]
    Alias for "./x uv run ...".

  ./x pnpm [ARGS]
    Runs a pnpm command. Implemented as "./x uv run corepack pnpm ...".
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

case "${1:---help}" in
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
  exec "$@"
  ;;

run)
  add_uv_path
  exec uv "$@"
  ;;

node | python | python3 | corepack | *.py)
  add_uv_path
  exec uv run "$@"
  ;;

pnpm)
  add_uv_path
  exec uv run corepack "$@"
  ;;

serve | cron | log)
  add_uv_path
  exec uv run "$base_dir/console.py" "$@"
  ;;

upgrade-py)
  shift
  add_uv_path
  exec uv sync --upgrade "$@"
  ;;

upgrade-js)
  # Upgrade pnpm itself. Edits "packageManager" in package.json.
  "$0" corepack use pnpm@latest
  # Upgrade all minor/patch versions (and their deps).
  "$0" pnpm update
  # Upgrade major versions of selected direct dependencies (and their deps).
  "$0" pnpm update --latest --interactive
  ;;

upgrade)
  "$0" upgrade-py
  "$0" upgrade-js
  ;;

install)
  # Detect which options were used last time, if any.
  olduv=system
  oldnodejs=system
  [[ -e "$base_dir/.x_local_uv_env/uv" ]] && olduv=local
  [[ -e "$base_dir/.venv/bin/node" ]] && oldnodejs=local

  # Parse arguments.
  uv=$olduv
  nodejs=$oldnodejs
  clean=
  proddeps=
  devdeps=y
  shift
  for arg; do
    case "$arg" in
    --uv=system | --uv=local) uv=${arg#*=} ;;
    --nodejs=system | --nodejs=local) nodejs=${arg#*=} ;;
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
  if [[ $proddeps ]]; then
    uvsyncopts+=' --group prod'
  fi
  if [[ ! $devdeps ]]; then
    uvsyncopts+=' --no-dev'
    pnpmopts+=' --production'
  fi

  trap 'if [[ $? != 0 ]]; then echo -e "${bright}${red}>>> Failed!${normal}"; fi' EXIT

  if [[ "$PWD" != "$base_dir" ]]; then
    log_and_run "" "cd ${base_dir@Q}"
  fi

  if [[ "$clean" == y ]]; then
    log_and_run "Deleting the previous installation. " "rm -rf .x_local_uv_env .venv node_modules"
  elif [[ -d .venv ]] && [[ "$uv" != "$olduv" || "$nodejs" != "$oldnodejs" ]]; then
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
  elif [[ -e .venv/bin/node ]]; then
    log "./.venv/bin/node already exists. Reusing it."
  else
    log_and_run "Installing nodeenv. " "uv pip install nodeenv"
    if [[ -n "${X_NODE_VERSION:-}" ]]; then
      log_and_run "Installing local node. " "uv run nodeenv -p -n \"\$X_NODE_VERSION\""
    else
      log_and_run "Installing local node (latest because \$X_NODE_VERSION is unset). " "uv run nodeenv -p"
    fi
    log_and_run "Cleaning up unnecessary files. " "rm -rf .venv/include/node .venv/src/node*"
    log_and_run "Uninstalling nodeenv. " "uv sync$uvsyncopts"
  fi

  if [[ -d node_modules ]]; then
    log "./node_modules already exists. Reusing it."
  fi

  log_and_run "Installing JavaScript dependencies to './node_modules'. " "uv run corepack pnpm install$pnpmopts"

  log "Success!"
  ;;

-*)
  echo >&2 "Unknown option: $1"
  "$0" --help
  exit 1
  ;;

*)
  echo >&2 "Unknown command: $1"
  "$0" --help
  exit 1
  ;;
esac
