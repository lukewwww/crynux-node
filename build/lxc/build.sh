#!/bin/bash
set -eux

echo "Installing Node.js 18 and setting up Yarn via corepack..."
mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
apt-get update
apt-get install -y nodejs
# Enable corepack and explicitly activate the latest stable Yarn version.
corepack enable
corepack prepare yarn@stable --activate

echo "Building Web UI..."
# /crynux-node is the default mount point for the project source in distrobuilder
mkdir -p /app
cp -r /crynux-node/src/webui /app/webui
cd /app/webui
yarn --immutable && yarn build

echo "Installing Go 1.21.0..."
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

echo "Setting up main application environment..."
python3.10 -m venv /app/venv
# Temporarily copy source to build the package
mkdir -p /app/build_dir/crynux-node
cp -r /crynux-node/src /app/build_dir/crynux-node/
cp /crynux-node/pyproject.toml /crynux-node/setup.py /crynux-node/requirements_docker.txt /crynux-node/MANIFEST.in /crynux-node/go.mod /crynux-node/go.sum /app/build_dir/crynux-node/
cd /app/build_dir/crynux-node
/app/venv/bin/pip install --no-cache-dir -r requirements_docker.txt
# Set CGO_ENABLED and PATH for building with imhash
export CGO_ENABLED="1"
export PATH="/usr/local/go/bin:${PATH}"
/app/venv/bin/pip install --no-cache-dir .

echo "Setting up worker environment..."
python3.10 -m venv /app/worker_venv
mkdir -p /app/build_dir/worker
cp -r /crynux-node/stable-diffusion-task /crynux-node/gpt-task /crynux-node/crynux-worker /app/build_dir/worker/

cd /app/build_dir/worker/stable-diffusion-task
/app/worker_venv/bin/pip install --no-cache-dir -r requirements_cuda.txt
/app/worker_venv/bin/pip install --no-cache-dir .

cd /app/build_dir/worker/gpt-task
/app/worker_venv/bin/pip install --no-cache-dir -r requirements_cuda.txt
/app/worker_venv/bin/pip install --no-cache-dir .

cd /app/build_dir/worker/crynux-worker
/app/worker_venv/bin/pip install --no-cache-dir -r requirements.txt
/app/worker_venv/bin/pip install --no-cache-dir .
/app/worker_venv/bin/pip uninstall -y triton

echo "Finalizing image..."
# Clean up build directory
rm -rf /app/build_dir
# Move worker venv to its final destination
mkdir -p /app/worker
mv /app/worker_venv /app/worker/venv
# Copy other artifacts
cp /crynux-node/crynux-worker/crynux_worker_process.py /app/worker/crynux_worker_process.py
cp /crynux-node/build/docker/config.yml.example /app/config.yml.example
cp /crynux-node/build/docker/start.sh /app/start.sh
chmod +x /app/start.sh
mv /app/webui/dist /app/dist
rm -rf /app/webui
if [ -d "/crynux-node/build/data" ]; then
  cp -r /crynux-node/build/data/* /app/
fi

echo "Installing and enabling systemd service for Crynux Node..."
cp /crynux-node/build/lxc/crynux-node.service /etc/systemd/system/crynux-node.service
systemctl enable crynux-node.service

echo "Setting up environment variables..."
cat <<'EOF' > /etc/profile.d/crynux.sh
export PATH="/app/venv/bin:/usr/local/go/bin:${PATH}"
export LD_LIBRARY_PATH="/usr/local/cuda-12.3/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
EOF

echo "Cleaning up build-time dependencies..."
# Yarn, managed by corepack, will be removed when the nodejs package is removed.
# No manual yarn uninstall is needed.
rm -rf /usr/local/go
sed -i 's|:/usr/local/go/bin||g' /etc/profile.d/crynux.sh
