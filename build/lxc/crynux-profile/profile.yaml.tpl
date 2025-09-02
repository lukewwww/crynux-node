name: crynux-node
description: Crynux Node LXC Profile
devices:
  config:
    path: /app/config
    source: __CURRENT_DIR__/config
    type: disk
    shift: true
  huggingface_cache:
    path: /app/tmp/huggingface
    source: __CURRENT_DIR__/tmp/huggingface
    type: disk
    shift: true
  external_cache:
    path: /app/tmp/external
    source: __CURRENT_DIR__/tmp/external
    type: disk
    shift: true
  gpu:
    type: gpu
  web:
    bind: host
    connect: tcp:127.0.0.1:7412
    listen: tcp:0.0.0.0:7412
    type: proxy
  eth0:
    name: eth0
    network: __LXC_BRIDGE_NAME__
    type: nic
config:
  nvidia.runtime: true
