#!/bin/bash

if [[ "$OSTYPE" == *darwin* ]]; then
  if command -v greadlink >/dev/null 2>&1; then
    scriptPath=$(dirname "$(greadlink -f "$0")")
  else
    echo "greadlink command not found"
    exit 1
  fi
else
  scriptPath=$(dirname "$(readlink -f "$0")")
fi
cd "${scriptPath}/" || exit 1

function deactivate_env() {
  echo "Deactivating env variables ..."
  unset SERVICE_VERSION
}

function display_help() {
  echo "Build image for ove-asset-manager"
  echo
  echo "usage: build.sh [option]..."
  echo "   --push            Push the image"
  echo "   -v, --version     The version of the service"
}

version=$(git describe --tags --exact-match 2>/dev/null)
if [[ $? -ne 0 ]]; then
  version="latest"
fi
version="${version}-unstable"

pushImage=false
pullImage=false

while [[ $# -gt 0 ]]; do
  key="$1"
  case ${key} in
  -h | --help)
    display_help
    exit 0
    ;;
  -v | --version)
    version="$2"
    echo "Recognized user version = ${version}"
    shift
    ;;
  --push)
    pushImage=true
    ;;
  --pull)
    pullImage=true
    ;;
  *)
    echo "Unrecognised option: $key"
    echo
    display_help
    exit 1
    ;;
  esac
  shift
done

export SERVICE_VERSION=${version}
trap deactivate_env EXIT SIGINT SIGTERM

echo "Building version = ${SERVICE_VERSION}"

if [[ "${pullImage}" == true ]]; then
  docker-compose pull
fi

docker-compose build
if [[ $? -ne 0 ]]; then
  # fail if the image build process failed
  exit 1
fi

if [[ "${pushImage}" == true ]]; then
  docker-compose push
fi
