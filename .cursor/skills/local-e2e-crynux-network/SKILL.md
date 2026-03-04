---
name: local-e2e-crynux-network
description: Orchestrate a full local e2e Crynux Network test across crynux-node, crynux-relay, crynux-relay-wallet, and crynux-bridge. Use when the user asks to build all e2e images, prepare keys/accounts, run a unified docker-compose stack, and validate Bridge task execution with LLM and VLM test tasks.
---

# Local E2E Crynux Network

## Goal

Run a full local end-to-end network test with:

- `crynux-node`
- `crynux-relay`
- `crynux-relay-wallet`
- `crynux-bridge`

The test workflow is:

1. Build e2e Docker images for all four projects.
2. Prepare the Docker-mounted e2e workspace under `tmp/e2e`.
3. Start all components with one unified compose file.
4. Send one LLM task and one VLM task to Bridge, then verify both succeed.

## Directory Layout

Use this skill directory as the control center:

- `SKILL.md`
- `.env.example`
- `docker-compose.e2e-network.yml`
- `scripts/generate-relay-secrets.py`
- `scripts/get-address.py`
- `scripts/send-bridge-tasks.py`

## Workflow

### 0) Read user-provided e2e inputs from env file

When executing this skill, always read values from `.cursor/skills/local-e2e-crynux-network/.env` and use them directly.

### 1) Build e2e Docker images

#### 1.1 crynux-node

Use the existing dedicated skill `build-e2e-node-docker-image` from this repository.

#### 1.2 crynux-relay

Build from the relay repository at `RELAY_REPO_PATH` in `.env`.

PowerShell:

```powershell
# In RELAY_REPO_PATH
docker build -t crynux-relay:e2e -f "build/crynux_relay.Dockerfile" .
docker image inspect crynux-relay:e2e --format "{{.Id}}"
```

#### 1.3 crynux-bridge

Build the bridge e2e Docker image from the bridge project repository with the bridge e2e configuration.
Tag the image as `crynux-bridge:e2e`.

#### 1.4 crynux-relay-wallet

Build from the relay-wallet repository at `RELAY_WALLET_REPO_PATH` in `.env`.

PowerShell:

```powershell
# In RELAY_WALLET_REPO_PATH
docker build -t crynux-relay-wallet:e2e .
docker image inspect crynux-relay-wallet:e2e --format "{{.Id}}"
```

### 2) Prepare Docker-mounted e2e workspace

This step creates a reusable local workspace at `tmp/e2e` for all mounted files (configs, keys, and related runtime files).

#### 2.1 Idempotency rule (must check first)

Before creating anything, check whether `tmp/e2e` already exists.

- If it exists, skip this whole step to avoid re-creating files.
- If it does not exist, create it and continue.

#### 2.2 Copy compose file into `tmp/e2e`

When `tmp/e2e` is newly created, copy the unified compose template `docker-compose.e2e-network.yml` to:

- `tmp/e2e/docker-compose.yml`

#### 2.3 Create per-project subfolders inside `tmp/e2e`

Create one subfolder per project:

- `tmp/e2e/node`
- `tmp/e2e/relay`
- `tmp/e2e/relay-wallet`
- `tmp/e2e/bridge`
- `tmp/e2e/mysql`

#### 2.4 Prepare `node` files and structure

Prepare `tmp/e2e/node` as a host-side data root for node mounts.

Required structure:

```text
tmp/e2e/node/
  config/
    private_key.txt
```

Read `NODE_PRIVATE_KEY` manually from `.cursor/skills/local-e2e-crynux-network/.env`.
Write the value directly into the node private key file.

#### 2.5 Prepare `relay` files and structure

Prepare `tmp/e2e/relay` as the relay mount root.

Required structure:

```text
tmp/e2e/relay/
  config/
    config.yml
    secrets/
      dym_private_key.txt
      near_private_key.txt
      jwt_secret_key.txt
      mac_secret_key.txt
  data/
    logs/
```

Create relay config from relay repo template `config.e2e.yml`:

```powershell
Copy-Item "<RELAY_REPO_PATH_FROM_ENV>/config/config.e2e.yml" "tmp/e2e/relay/config/config.yml" -Force
```

Read these values manually from `.cursor/skills/local-e2e-crynux-network/.env`:

- `RELAY_DYM_PRIVATE_KEY`
- `RELAY_NEAR_PRIVATE_KEY`
- `RELAY_WITHDRAW_WITHDRAWAL_FEE_ADDRESS`
- `RELAY_CREDITS_ADDRESS`
- `RELAY_DAO_ADDRESS`
- `RELAY_BUY_QUOTA_ADDRESS`
- `RELAY_BUY_TASK_FEE_ADDRESS`

Write relay secret files:

```powershell
Set-Content -Path "tmp/e2e/relay/config/secrets/dym_private_key.txt" -Value "<RELAY_DYM_PRIVATE_KEY_FROM_ENV>" -NoNewline
Set-Content -Path "tmp/e2e/relay/config/secrets/near_private_key.txt" -Value "<RELAY_NEAR_PRIVATE_KEY_FROM_ENV>" -NoNewline
```

Generate JWT and MAC secret files when missing or empty:

```powershell
python ".cursor/skills/local-e2e-crynux-network/scripts/generate-relay-secrets.py"
```

Get addresses from private keys:

```powershell
python ".cursor/skills/local-e2e-crynux-network/scripts/get-address.py" "<RELAY_DYM_PRIVATE_KEY_FROM_ENV>"
python ".cursor/skills/local-e2e-crynux-network/scripts/get-address.py" "<RELAY_NEAR_PRIVATE_KEY_FROM_ENV>"
python ".cursor/skills/local-e2e-crynux-network/scripts/get-address.py" "<RELAY_WALLET_RELAY_API_PRIVATE_KEY_FROM_ENV>"
```

Manually write values into `tmp/e2e/relay/config/config.yml`:

- Set `blockchains.dymension.account.address` to the address derived from `RELAY_DYM_PRIVATE_KEY`.
- Set `blockchains.near.account.address` to the address derived from `RELAY_NEAR_PRIVATE_KEY`.
- Set `withdraw.address` to the address derived from `RELAY_WALLET_RELAY_API_PRIVATE_KEY`.
- Set `withdraw.withdrawal_fee_address` to `RELAY_WITHDRAW_WITHDRAWAL_FEE_ADDRESS`.
- Set `credits.address` to `RELAY_CREDITS_ADDRESS`.
- Set `dao.address` to `RELAY_DAO_ADDRESS`.
- Set `buy_quota.address` to `RELAY_BUY_QUOTA_ADDRESS`.
- Set `buy_task_fee.address` to `RELAY_BUY_TASK_FEE_ADDRESS`.

#### 2.6 Prepare `relay-wallet` files and structure

Prepare `tmp/e2e/relay-wallet` as the relay-wallet mount root.

Use `crynux-relay-wallet` as an isolated offline wallet component for withdrawal signing and risk-control checks.
Do not place the withdrawal signing private key in relay runtime files.

Required structure:

```text
tmp/e2e/relay-wallet/
  config/
    config.yml
    secrets/
      relay_api_private_key.txt
      wallet_private_key.txt
  data/
    db/
    logs/
```

Read these values manually from `.cursor/skills/local-e2e-crynux-network/.env`:

- `RELAY_WALLET_RELAY_API_PRIVATE_KEY`
- `RELAY_WALLET_ACCOUNT_PRIVATE_KEY`

Write secret files:

```powershell
Set-Content -Path "tmp/e2e/relay-wallet/config/secrets/relay_api_private_key.txt" -Value "<RELAY_WALLET_RELAY_API_PRIVATE_KEY_FROM_ENV>" -NoNewline
Set-Content -Path "tmp/e2e/relay-wallet/config/secrets/wallet_private_key.txt" -Value "<RELAY_WALLET_ACCOUNT_PRIVATE_KEY_FROM_ENV>" -NoNewline
```

Create relay-wallet config from relay-wallet repo e2e template:

```powershell
Copy-Item "<RELAY_WALLET_REPO_PATH_FROM_ENV>/config/config.e2e.yml" "tmp/e2e/relay-wallet/config/config.yml" -Force
```

#### 2.7 Prepare `bridge` files and structure

Prepare `tmp/e2e/bridge` as the bridge mount root and place bridge runtime files there:

- Bridge private key and account material from `.env`
- Bridge config files required by the bridge image
- Bridge runtime directories expected by bridge startup

### 3) Start all components with unified compose

Use:

```powershell
docker compose --env-file ".cursor/skills/local-e2e-crynux-network/.env" -f "tmp/e2e/docker-compose.yml" up -d
docker compose --env-file ".cursor/skills/local-e2e-crynux-network/.env" -f "tmp/e2e/docker-compose.yml" ps
```

### 4) Validate Bridge task execution

Run:

```powershell
python ".cursor/skills/local-e2e-crynux-network/scripts/send-bridge-tasks.py"
```

Script goals:

- Submit one LLM task request to Bridge.
- Submit one VLM task request to Bridge.
- Poll task status until completion or timeout.
- Exit non-zero if any task fails or times out.

## Compose File Notes

The unified compose file is provided at:

- `docker-compose.e2e-network.yml`

Runtime compose path after workspace preparation:

- `tmp/e2e/docker-compose.yml`

The compose file defines node, relay, relay-wallet, and bridge services on a shared network.
It also includes a MySQL service used by relay.

## Validation Checklist

- [ ] Four e2e images are available locally.
- [ ] `tmp/e2e` exists (or was already present and reused).
- [ ] `tmp/e2e/docker-compose.yml` exists.
- [ ] `tmp/e2e/node/config/private_key.txt` exists and is valid.
- [ ] `crynux-relay:e2e` image exists locally.
- [ ] `crynux-relay-wallet:e2e` image exists locally.
- [ ] `tmp/e2e/relay/config/config.yml` exists.
- [ ] `tmp/e2e/relay/config/secrets/*.txt` exists and is non-empty.
- [ ] `tmp/e2e/relay-wallet/config/config.yml` exists.
- [ ] `tmp/e2e/relay-wallet/config/secrets/*.txt` exists and is non-empty.
- [ ] `docker compose ... up -d` starts every service.
- [ ] LLM task completes successfully.
- [ ] VLM task completes successfully.
