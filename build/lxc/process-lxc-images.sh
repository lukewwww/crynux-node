#!/bin/bash

# LXC Image Processing Script for Simplestreams
# This script processes uploaded LXC images and converts them to simplestreams format
#
# IMPORTANT: This script runs with ubuntu user permissions (no sudo required)
# Relies on directory setgid bit to ensure proper file group ownership

UPLOAD_DIR="/var/www/lxc/uploads"
SIMPLESTREAMS_DIR="/var/www/lxc/simplestreams"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [process-lxc-images.sh] $1"
}

process_image() {
    local version="$1"

    log "Processing image with version: $version"

    # Check if required files exist in upload directory (build-incus format)
    local incus_file="$UPLOAD_DIR/incus-${version}.tar.xz"
    local rootfs_file="$UPLOAD_DIR/rootfs-${version}.squashfs"

    if [[ ! -f "$incus_file" ]] || [[ ! -f "$rootfs_file" ]]; then
        log "ERROR: Missing required files (incus-${version}.tar.xz or rootfs-${version}.squashfs) in $UPLOAD_DIR"
        return 1
    fi

    # Process from simplestreams directory
    cd "$SIMPLESTREAMS_DIR"
    log "Working from directory: $(pwd)"

    # Add image to simplestreams repository
    # incus-simplestreams processes build-incus format: incus.tar.xz and rootfs.squashfs
    log "Adding Incus image to simplestreams repository..."

    local -a cmd=(incus-simplestreams add
        "$incus_file" "$rootfs_file"
        --alias "crynux-node:$version"
        --no-default-alias
    )

    if [[ "$LATEST" == "true" ]]; then
        log "Adding latest alias for blockchain: $BLOCKCHAIN"
        cmd+=(--alias "crynux-node:latest-$BLOCKCHAIN")
    fi

    "${cmd[@]}"

    if [[ $? -eq 0 ]]; then
        log "Successfully added image crynux-node:$version"
        log "Successfully processed and published crynux-node:$version"

        # Clean up processed files
        rm -f "$incus_file" "$rootfs_file"

        return 0
    else
        log "ERROR: Failed to add image to simplestreams"
        return 1
    fi
}

# Main execution
# Support both command line arguments and environment variables, with arguments taking precedence.

# 1. VERSION (Required)
if [[ -n "$1" ]]; then
    VERSION="$1"
fi
if [[ -z "$VERSION" ]]; then
    echo "Error: Version is not specified."
    echo "Usage: $0 <version> [blockchain] [latest]"
    echo "Alternatively, set the VERSION environment variable."
    exit 1
fi

# 2. BLOCKCHAIN (Required)
if [[ -n "$2" ]]; then
    BLOCKCHAIN="$2"
fi
if [[ -z "$BLOCKCHAIN" ]]; then
    echo "Error: Blockchain is not specified."
    echo "Usage: $0 <version> <blockchain> [latest]"
    echo "Alternatively, set the BLOCKCHAIN environment variable."
    exit 1
fi

# 3. LATEST (Optional, defaults to false)
if [[ -n "$3" ]]; then
    LATEST="$3"
fi
if [[ -z "$LATEST" ]]; then
    LATEST="false"
fi

process_image "$VERSION"
