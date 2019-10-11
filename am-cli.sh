#!/usr/bin/env bash

if [[ "$OSTYPE" == *darwin* ]]; then
     if command -v greadlink>/dev/null 2>&1; then
        scriptPath=$(dirname "$(greadlink -f "$0")")
     else
        echo "greadlink command not found"
        exit 1
     fi
else
     scriptPath=$(dirname "$(readlink -f "$0")")
fi
cd "${scriptPath}/" || exit 1

source ./env/bin/activate

if [[ $? ]]; then
    python -m cli $@
    deactivate
else
    echo "Could not activate virtual environment required for this tool"
    echo "Please create it by using (in the same folder as the script):"
    echo "  virtualenv -p python3 env"
    echo "  source ./env/bin/activate"
    echo "  pip install -r requirements.txt"
fi