#!/bin/bash

# https://github.com/AnyLifeZLB/FaceVerificationSDK/blob/main/install_newest_mediapipe_on_macos.md
export SYSTEM_VERSION_COMPAT=0

# Must use arm64 version of Python
# python > 3.10.2 is required
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        "$cmd" -c "
import sys
version = sys.version_info
if not (version.major == 3 and (version.minor > 10 or (version.minor == 10 and version.micro > 2))):
    sys.exit(1)
"
        if [ $? -eq 0 ]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Python > 3.10.2 is required."
    echo "Could not find a compatible python version. Please install python > 3.10.2 and make sure it is in your PATH as 'python' or 'python3'."
    exit 1
fi

echo "Using python: $PYTHON_CMD"

arch=$($PYTHON_CMD -c "import platform;print(platform.uname())")
if [[ $arch == *"x86_64"* ]]; then
  echo "Please use the python in arm64 arch"
  exit 1
fi

# remove old env
if [ -d "venv" ]; then
  rm -rf venv
fi

if [ -d "worker" ]; then
  rm -rf worker
fi

# prepare the server
$PYTHON_CMD -m venv venv
source ./venv/bin/activate
pip install -r requirements_desktop.txt
pip install .

# prepare the worker
mkdir worker
cp crynux-worker/crynux_worker_process.py worker/
cd worker
$PYTHON_CMD -m venv venv
source ./venv/bin/activate

cd ../stable-diffusion-task
pip install -r requirements_macos.txt
pip install .

cd ../gpt-task
pip install -r requirements_macos.txt
pip install .

cd ../crynux-worker
pip install -r requirements.txt
pip install .

# go back to server venv
cd ../
source ./venv/bin/activate
