#!/usr/bin/env bash
# shellcheck disable=SC2250

set -e -u -o pipefail

base_dir=$(dirname "$0")
base_dir=$(readlink -fv "$base_dir")

help1='Usage:

  ./x install [OPTIONS]
    Downloads dependencies to "./venv" (Py) and "./node_modules" (JS).
    It'\''s best to rerun it after every "git pull" in case they were updated.
    Options:
      --python={local|system}  use system-wide Python or download it locally
      --nodejs={local|system}  use system-wide Node.js or download it locally
      --yarn={local|system}    use system-wide Yarn or download it locally
      --clean                  reinstall everything from scratch
'

# shellcheck disable=SC2016
help2='
  ./x run PROGRAM [ARGS]
    Runs a single program with ./venv activated.
    (That roughly means: with ./venv/bin added to its $PATH.)

  ./x console.py [ARGS]   (or any other *.py file)
  ./x node [ARGS]
  ./x python [ARGS]
  ./x python3 [ARGS]
  ./x yarn [ARGS]
    Convenience shortcuts for running the programs with ./venv activated.
'

normal=$'\e[0m'
bright=$'\e[1m'
red=$'\e[31m'
yellow=$'\e[33m'
blue=$'\e[34m'

run_with_venv() {
  if ! [[ -d "$base_dir/venv" ]]; then
    echo >&2 'Error: ./venv does not exist. You must run "./x install" first.'
    return 1
  fi
  (
    set +u # TODO: Remove this when https://github.com/ekalinin/nodeenv/pull/345 is fixed.
    # shellcheck source=/dev/null
    source "$base_dir/venv/bin/activate"
    exec -- "$@"
  )
}

log() {
  echo >&2 "${bright}${yellow}>>> ${normal}${yellow}${1}${normal}"
}

log_and_run() {
  echo >&2 "${bright}${yellow}>>> ${normal}${yellow}${1}Running: ${blue}${2}${normal}"
  eval "$2"
}

log_and_run_with_venv() {
  echo >&2 "${bright}${yellow}>>> ${normal}${yellow}${1}Running with ./venv: ${blue}${2}${normal}"
  eval "run_with_venv $2"
}

case "${1:---help}" in
--help)
  if [[ -d "$base_dir/venv" ]]; then
    echo >&2 "$help1$help2"
    run_with_venv env -C "$base_dir" python console.py 2>&1 | sed '/^usage:$/d; s!^  console.py!  ./x!' >&2
  else
    echo >&2 "$help1"
    echo >&2 'More commands will be available after running "./x install".'
  fi
  ;;

run)
  shift
  if [[ $# == 0 ]]; then
    echo >&2 "No command specified"
    exit 1
  fi
  run_with_venv "$@"
  ;;

node | python | python3 | yarn)
  run_with_venv "$@"
  ;;

*.py)
  run_with_venv python "$@"
  ;;

serve | cron | log)
  run_with_venv python "$base_dir/console.py" "$@"
  ;;

install)
  # Detect which options were used last time, if any.
  oldpython=system
  oldnodejs=system
  oldyarn=system
  [[ "$(readlink -f "$base_dir/venv/bin/python" || true)" == */baseenv/* ]] && oldpython=local
  [[ -e "$base_dir/venv/bin/node" ]] && oldnodejs=local
  [[ -e "$base_dir/venv/bin/yarn" ]] && oldyarn=local

  # Parse arguments.
  python=$oldpython
  nodejs=$oldnodejs
  yarn=$oldyarn
  clean=
  shift
  for arg; do
    case "$arg" in
    --python=system | --python=local) python=${arg#*=} ;;
    --nodejs=system | --nodejs=local) nodejs=${arg#*=} ;;
    --yarn=system | --yarn=local) yarn=${arg#*=} ;;
    --clean) clean=y ;;
    *)
      echo >&2 "Unknown option: $arg"
      exit 1
      ;;
    esac
  done

  trap 'if [[ $? != 0 ]]; then echo -e "${bright}${red}>>> Failed!${normal}"; fi' EXIT

  if [[ "$PWD" != "$base_dir" ]]; then
    log_and_run "" "cd ${base_dir@Q}"
  fi

  if [[ "$clean" == y ]]; then
    log_and_run "Deleting the previous installation. " "rm -rf baseenv venv node_modules"
  elif [[ -d venv ]] && [[ "$python" != "$oldpython" || "$nodejs" != "$oldnodejs" || "$yarn" != "$oldyarn" ]]; then
    log_and_run "Deleting venv because options have changed. " "rm -rf venv"
  fi

  if [[ -d venv ]]; then
    log "./venv already exists. Reusing it."
  else
    "$base_dir/x" "internal-create-venv-with-$python-python" ./venv

    if [[ $nodejs == local ]]; then
      log_and_run_with_venv "Installing nodeenv. " "pip install nodeenv"
      if [[ -n "${X_NODE_VERSION:-}" ]]; then
        log_and_run_with_venv "Installing local node. " "nodeenv -p -n \"\$X_NODE_VERSION\""
      else
        log_and_run_with_venv "Installing local node (latest because \$X_NODE_VERSION is unset). " "nodeenv -p"
      fi
      log_and_run "Cleaning up unnecessary files. " "rm -rf venv/include/node venv/src/node*"
    else
      log "Using system node."
    fi

    if [[ $yarn == local ]]; then
      log_and_run_with_venv "Installing local yarn. " "npm install yarn -g --prefix venv"
    else
      log "Using system yarn."
    fi
  fi

  log_and_run_with_venv "Installing Python dependencies to './venv'. " "pip install -r requirements.txt"

  if [[ -d node_modules ]]; then
    log "./node_modules already exists. Reusing it."
  fi

  log_and_run_with_venv "Installing JavaScript dependencies to './node_modules'. " "yarn install"

  log "Success!"
  ;;

internal-create-venv-with-system-python)
  destination=$2

  current_python=$(command -v python3 || true)
  if [[ "$current_python" != /* ]]; then
    echo >&2 "Command python3 not found."
    exit 1
  fi

  # If some venv is already active, try to find the original.
  # This is not multiplatform (e.g. Windows venv doesn't use symlinks, and some
  # Python binaries on macOS reportedly use too many symlinks) but it should be
  # good enough on Linux.
  current_python=$(readlink -fv "$current_python")

  # If we found /.../python3.X, try /.../python3 (just because it's nicer).
  if [[ "$current_python" =~ ^.*/python3\.[0-9]+$ ]] && [[ -e "${current_python%.*}" ]] && [[ "$(readlink -f "${current_python%.*}" || true)" == "$current_python" ]]; then
    current_python=${current_python%.*}
  fi

  log_and_run "Creating virtual environment ${destination@Q} using system-wide Python ($current_python). " "${current_python@Q} -m venv --upgrade-deps ${destination@Q}"
  ;;

internal-create-venv-with-local-python)
  destination=$2

  if [[ -d baseenv ]]; then
    log "./baseenv already exists. Reusing it."
  else
    log_and_run "Preparing to install local Python. " "mkdir baseenv"
    log_and_run "" "cd baseenv"
    log_and_run "Downloading version list. " "curl -fLsS 'https://api.github.com/repos/indygreg/python-build-standalone/releases/latest' -o versions.txt"
    log "Looking for ${X_PYTHON_VERSION:-newest Python version} (\$X_PYTHON_VERSION) and ${X_PYTHON_ARCH:-x86_64_v3} (\$X_PYTHON_ARCH)."
    best=$(grep -o '"cpython[^"\\]*"' versions.txt | tr -d '"' | grep install_only | grep -F -- "${X_PYTHON_VERSION:-.}" | grep -F -- "${X_PYTHON_ARCH:-x86_64_v3}" | grep gnu | grep -v '\.sha' | sort -V | tail -n1)
    log "Choosing version: $best"
    pythonurl=https://github.com/indygreg/python-build-standalone/releases/latest/download/$best
    log_and_run "Downloading it. " "curl -fLO# ${pythonurl@Q}"
    log_and_run "Extracting it. " "tar xzf ${best@Q}"
    if [[ -n "${X_KEEP_TMP:-}" ]]; then
      log "\$X_KEEP_TMP is set."
    else
      log_and_run "\$X_KEEP_TMP is not set. Cleaning up. " "rm -f ${best@Q} versions.txt"
    fi
    log_and_run "" "cd .."
  fi

  log_and_run "Creating virtual environment ${destination@Q} using local Python. " "./baseenv/python/bin/python3 -m venv --upgrade-deps ${destination@Q}"
  ;;

*)
  echo >&2 "Unknown option: $1"
  "$0" --help
  exit 1
  ;;
esac
