#!/bin/bash


# Function to verify checksum for a package
verify_checksum() {
    local package=$1
    local checksum_file="README"
    local expected_checksum=$(grep $(basename $package) "$checksum_file" | awk '{print $2}')

    # Calculate the checksum of the package
    downloaded_checksum=$(sha256sum $package | awk '{print $1}')

    echo ""
    echo "Verifying checksum for: $package"
    echo "Expected checksum: $expected_checksum"
    echo "Downloaded checksum: $downloaded_checksum"

    # Compare the calculated checksum with the expected checksum
    if [ "$downloaded_checksum" == "$expected_checksum" ]; then
        echo "$(basename $package) checksum verified successfully."
    else
        echo "$(basename $package) checksum verification failed!"
    fi
}


# Iterate over each package file in the directory
for package in *.deb *.rpm; do
    # Skip directories
    if [ -f "$package" ]; then
        verify_checksum "$package"
    fi
done