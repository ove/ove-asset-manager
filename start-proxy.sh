#!/usr/bin/env bash

scriptPath=$(dirname "$(readlink -f "$0")")
cd "${scriptPath}" || exit

jarName="ove-am-kreadproxy-*-jar-with-dependencies.jar"

function display_help() {
  echo "Start OVE AM Read Proxy"
  echo
  echo "usage: start.sh [option]..."
  echo "   --port          Service port"
  echo "   --config        Service auth config"
  echo "   --environment   Properties file for environment substitution"
}

function detectPath() {
    jarPath=$( find . -name "${jarName}" | tail -n 1 )
    if [[ -z ${jarPath} && -d target ]]; then
        jarPath=$( find target/ -name "${jarName}" | tail -n 1 )
    fi
    if [[ -z ${jarPath} && -d ../target ]]; then
        jarPath=$( find ../target/ -name "${jarName}" | tail -n 1 )
    fi
    if [[ -z ${jarPath} ]]; then
        echo "Could not find ${jarName}"
        exit 1
    fi
}

[[ ! -z "${SERVICE_PORT}" ]] || SERVICE_PORT="6081"
[[ ! -z "${SERVICE_CONFIG}" ]] || SERVICE_CONFIG="config/credentials.json"
[[ ! -z "${WHITELIST_CONFIG}" ]] || WHITELIST_CONFIG="config/whitelist.json"
[[ ! -z "${SERVICE_ENVIRONMENT}" ]] || SERVICE_CONFIG="config/environment.properties"
[[ ! -z "${SERVICE_OTHER_OPTIONS}" ]] || SERVICE_OTHER_OPTIONS=""

while [[ $# -gt 0 ]]; do
  key="$1"
  case ${key} in
    -h|--help)
      display_help
      exit 0
      ;;
    --port)
      SERVICE_PORT="$2"
      shift
      ;;
    --config)
      SERVICE_CONFIG="$2"
      shift
      ;;
    --whitelist)
      WHITELIST_CONFIG="$2"
      shift
      ;;
    --environment)
      SERVICE_ENVIRONMENT="$2"
      shift
      ;;
    *)
      SERVICE_OTHER_OPTIONS="${SERVICE_OTHER_OPTIONS} $key"
      ;;
  esac
  shift
done

echo "Environment variables:"
echo "  SERVICE_PORT=${SERVICE_PORT}"
echo "  SERVICE_CONFIG=${SERVICE_CONFIG}"
echo "  SERVICE_ENVIRONMENT=${SERVICE_ENVIRONMENT}"
echo "  WHITELIST_CONFIG=${WHITELIST_CONFIG}"
echo "  SERVICE_OTHER_OPTIONS=${SERVICE_OTHER_OPTIONS}"
echo ""

detectPath && java -server -XX:+UnlockExperimentalVMOptions -XX:+UseStringDeduplication -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -jar "${jarPath}" \
                   --port "${SERVICE_PORT}" --config "${SERVICE_CONFIG}" --environment "${SERVICE_ENVIRONMENT}" --whitelist "${WHITELIST_CONFIG}" "${SERVICE_OTHER_OPTIONS}"