#!/bin/bash
set -eux

# This script is executed inside the LXC container by distrobuilder.
# The current working directory is /app-source, which contains the entire project source code.
# The final runtime artifacts will be placed in /app.

echo "Installing Node.js 18 and setting up Yarn via corepack..."
mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
apt-get update
apt-get install -y nodejs
corepack enable
corepack prepare yarn@stable --activate

echo "Building Web UI..."
cd src/webui
yarn --immutable && yarn build
mkdir -p /app
mv dist /app/dist
cd /app-source # Return to source root

echo "Installing Go 1.21.0 for cgo build..."
curl -O -L "https://golang.org/dl/go1.21.0.linux-amd64.tar.gz"
tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
rm go1.21.0.linux-amd64.tar.gz

echo "Installing CUDA Toolkit 12.3.1..."
wget https://developer.download.nvidia.com/compute/cuda/12.3.1/local_installers/cuda-repo-ubuntu2204-12-3-local_12.3.1-545.23.08-1_amd64.deb
dpkg -i cuda-repo-ubuntu2204-12-3-local_12.3.1-545.23.08-1_amd64.deb
cp /var/cuda-repo-ubuntu2204-12-3-local/cuda-*-keyring.gpg /usr/share/keyrings/
apt-get update
apt-get -y install --no-install-recommends cuda-toolkit-12-3
rm -f cuda-repo-ubuntu2204-12-3-local_12.3.1-545.23.08-1_amd64.deb

echo "Setting up main application venv in /app..."
python3.10 -m venv /app/venv
/app/venv/bin/pip install --no-cache-dir -r requirements_docker.txt
export CGO_ENABLED="1"
export PATH="/usr/local/go/bin:${PATH}"
/app/venv/bin/pip install --no-cache-dir .

echo "Setting up worker venv in /app..."
mkdir -p /app/worker
python3.10 -m venv /app/worker/venv

cd stable-diffusion-task
/app/worker/venv/bin/pip install --no-cache-dir -r requirements_cuda.txt
/app/worker/venv/bin/pip install --no-cache-dir .
cd /app-source

cd gpt-task
/app/worker/venv/bin/pip install --no-cache-dir -r requirements_cuda.txt
/app/worker/venv/bin/pip install --no-cache-dir .
cd /app-source

cd crynux-worker
/app/worker/venv/bin/pip install --no-cache-dir -r requirements.txt
/app/worker/venv/bin/pip install --no-cache-dir .
/app/worker/venv/bin/pip uninstall -y triton
cd /app-source

echo "Copying final artifacts to /app..."
cp crynux-worker/crynux_worker_process.py /app/worker/
cp build/docker/config.yml.example /app/config.yml.example
cp build/docker/start.sh /app/start.sh
chmod +x /app/start.sh
if [ -d "build/data" ]; then
  cp -r build/data/* /app/
fi

echo "Installing and enabling systemd service..."
# The service file was copied to / by the YAML file, which is a safe location.
cp /crynux-node.service /etc/systemd/system/crynux-node.service
systemctl enable crynux-node.service

echo "Setting up environment variables..."
cat <<'EOF' > /etc/profile.d/crynux.sh
export PATH="/app/venv/bin:/usr/local/go/bin:${PATH}"
export LD_LIBRARY_PATH="/usr/local/cuda-12.3/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
EOF

echo "Cleaning up build artifacts..."
rm -rf /usr/local/go
sed -i 's|:/usr/local/go/bin||g' /etc/profile.d/crynux.sh
rm -rf /app-source
