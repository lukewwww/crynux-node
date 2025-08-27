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

    # Ensure upload directory has correct permissions (no chown needed)
    chmod 755 "$UPLOAD_DIR"

    # Check if required files exist in upload directory
    if [[ ! -f "$UPLOAD_DIR/rootfs.tar.xz" ]] || [[ ! -f "$UPLOAD_DIR/meta.tar.xz" ]]; then
        log "ERROR: Missing required files (rootfs.tar.xz or meta.tar.xz) in $UPLOAD_DIR"
        return 1
    fi

    # Process from simplestreams directory
    cd "$SIMPLESTREAMS_DIR"
    log "Working from directory: $(pwd)"

    # Add image to simplestreams repository
    # incus-simplestreams automatically extracts metadata from meta.tar.xz:
    # - architecture, os, release, variant, creation_date, description
    log "Adding image to simplestreams repository..."
    incus-simplestreams add \
        "$UPLOAD_DIR/meta.tar.xz" "$UPLOAD_DIR/rootfs.tar.xz" \
        --alias "crynux-node:$version"

    if [[ $? -eq 0 ]]; then
        log "Successfully added image crynux-node:$version"
        log "Successfully processed and published crynux-node:$version"

        # Clean up processed files
        rm -f "$UPLOAD_DIR/rootfs.tar.xz" "$UPLOAD_DIR/meta.tar.xz"

        return 0
    else
        log "ERROR: Failed to add image to simplestreams"
        return 1
    fi
}

# Main execution
# Support both command line argument and environment variable
if [[ $# -eq 1 ]]; then
    VERSION="$1"
elif [[ -n "$VERSION" ]]; then
    # Use environment variable if available
    VERSION="$VERSION"
else
    echo "Usage: $0 <version> or set VERSION environment variable"
    exit 1
fi

process_image "$VERSION"
