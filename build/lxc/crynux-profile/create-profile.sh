#!/bin/bash

set -e

# Get lxc or incus command from arguments
if [ "$1" == "incus" ]; then
    LXC_CMD="incus"
elif [ "$1" == "lxc" ]; then
    LXC_CMD="lxc"
else
    echo "Usage: $0 [incus|lxc]" >&2
    exit 1
fi
echo "Using command: $LXC_CMD"

# Get the default bridge name from the default profile
LXC_BRIDGE_NAME=$($LXC_CMD profile device get default eth0 network)
if [ -z "$LXC_BRIDGE_NAME" ]; then
    echo "Error: Could not determine the default LXC/Incus bridge network from the 'default' profile." >&2
    exit 1
fi
echo "Detected LXC/Incus bridge: $LXC_BRIDGE_NAME"

# Get the directory of the script
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)


# Template file and output file
TEMPLATE_FILE="$SCRIPT_DIR/profile.yaml.tpl"
OUTPUT_FILE="$SCRIPT_DIR/profile.yaml"

# Replace the placeholder with the absolute path
sed -e "s|__CURRENT_DIR__|$SCRIPT_DIR|g" \
    -e "s|__LXC_BRIDGE_NAME__|$LXC_BRIDGE_NAME|g" \
    "$TEMPLATE_FILE" > "$OUTPUT_FILE"

echo "Generated $OUTPUT_FILE"
echo "You can now apply the profile with: '$LXC_CMD profile edit crynux-node < $OUTPUT_FILE'"
