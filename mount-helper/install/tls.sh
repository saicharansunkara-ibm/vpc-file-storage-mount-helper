#!/bin/bash
#
# Copyright (c) IBM Corp. 2024. All Rights Reserved.
# Project name: VPC File Storage Mount Helper
# This project is licensed under the MIT License, see LICENSE file in the root directory.

FILE_PATH="/etc/hosts"
ip_address=$1

# Function to validate IP address format
is_valid_ip() {
    local ip=$1
    local valid_ip_regex="^([0-9]{1,3}\.){3}[0-9]{1,3}$"

    if [[ $ip =~ $valid_ip_regex ]]; then
        IFS='.' read -r -a octets <<< "$ip"
        for octet in "${octets[@]}"; do
            if (( octet < 0 || octet > 255 )); then
                echo "Invalid IP address format."
                return 1  # Invalid octet
            fi
        done
        
        # Check for special IP addresses
        if [[ $ip == "0.0.0.0" ]] || 
           [[ $ip == "255.255.255.255" ]]; then
            echo "Special IPs not allowed."
            return 1  # Special IP addresses are considered invalid for this context
        fi
        
        return 0  # Valid public IP address
    else
        return 1  # Invalid format
    fi
}

# Function to validate hostname extension
is_valid_host_extension() {
    local hostname=$1
    if [[ $hostname == *.ibm.vpc.file.storage ]]; then
        return 0
    else
        echo "The hostname does NOT have the correct extension."
        return 1
    fi
}

# Main logic
if is_valid_ip "$ip_address" || is_valid_host_extension "$ip_address"; then
    if grep -q "$ip_address" "$FILE_PATH"; then
        grep "$ip_address" "$FILE_PATH" | awk '{print $2}'
    else
        echo "$ip_address ibmshare_${ip_address//./_}.ibm.vpc.file.storage" | tee -a "$FILE_PATH"
    fi
else
    exit 1
fi