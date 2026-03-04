---
name: build-e2e-node-docker-image
description: Build the e2e Docker image for Crynux Node using the dedicated e2e config file. Use when the user asks to build an e2e test image, crynux-node:e2e, or an e2e Docker image for node testing.
---

# Build E2E Node Docker Image

## Goal

Build `crynux-node:e2e` from this repository by using the dedicated e2e config template at `config/config.yml.e2e_example`.

## Constraints

- Do not create scripts.
- Execute commands directly in the terminal.
- Keep paths relative to the repository root.

## Workflow

1. Ensure the working directory is the repository root.
2. Copy the e2e config file to the Docker build config path required by `build/docker/Dockerfile`.
3. Build the image with the `crynux-node:e2e` tag.
4. Verify the image exists locally.

## Commands

Use the shell that matches the environment.

### PowerShell

```powershell
Copy-Item "config/config.yml.e2e_example" "build/docker/config.yml.example" -Force
docker build -t crynux-node:e2e -f build/docker/Dockerfile .
docker image inspect crynux-node:e2e --format "{{.Id}}"
```

### Bash

```bash
cp config/config.yml.e2e_example build/docker/config.yml.example
docker build -t crynux-node:e2e -f build/docker/Dockerfile .
docker image inspect crynux-node:e2e --format "{{.Id}}"
```

## Expected Result

- `build/docker/config.yml.example` is generated from the e2e config template.
- Docker image `crynux-node:e2e` is built successfully and can be inspected locally.
