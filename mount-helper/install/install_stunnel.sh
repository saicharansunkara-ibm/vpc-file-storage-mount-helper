#!/bin/bash

# Constants
INSTALL="install"
UNINSTALL="uninstall"

# Create necessary directories
setup_stunnel_directories() {
    sudo mkdir -p /var/run/stunnel4/ /etc/stunnel
    sudo chmod 744 /var/run/stunnel4/ /etc/stunnel
}

# Install stunnel on Ubuntu/Debian-based systems
install_stunnel_ubuntu_debian() {
    echo "Starting installation of stunnel on Ubuntu/Debian-based system..."
    # Update apt and install stunnel
    sudo apt-get update
    sudo apt-get install -y stunnel4
    setup_stunnel_directories

    # Verify installation
    if command -v stunnel > /dev/null; then
        echo "stunnel installed successfully!"
    else
        echo "Failed to install stunnel."
        exit 1
    fi
}

# Install stunnel on Red Hat/CentOS/Rocky-based systems
install_stunnel_rhel_centos_rocky() {
    echo "Starting installation of stunnel on Red Hat/CentOS/Rocky-based system..."
    # Install EPEL repository if not already installed
    sudo yum install -y epel-release

    # Install stunnel
    sudo yum install -y stunnel
    setup_stunnel_directories

    # Verify installation
    if command -v stunnel > /dev/null; then
        echo "stunnel installed successfully!"
    else
        echo "Failed to install stunnel."
        exit 1
    fi
}

# Function to install stunnel on SUSE-based systems
install_stunnel_suse() {
    echo "Starting installation of stunnel on SUSE-based system..."
    # Install stunnel
    sudo zypper install -y stunnel
    setup_stunnel_directories

    # Verify installation
    if command -v stunnel > /dev/null; then
        echo "stunnel installed successfully!"
    else
        echo "Failed to install stunnel."
        exit 1
    fi
}

# Uninstall stunnel on Ubuntu/Debian-based systems
uninstall_stunnel_ubuntu_debian() {
    echo "Uninstalling stunnel on Ubuntu/Debian-based system..."
    sudo apt-get remove --purge -y stunnel4
    sudo rm -rf /var/run/stunnel4/ /etc/stunnel

    if ! command -v stunnel > /dev/null; then
        echo "stunnel uninstalled successfully!"
    else
        echo "Failed to uninstall stunnel."
        exit 1
    fi
}

# Uninstall stunnel on Red Hat/CentOS/Rocky-based systems
uninstall_stunnel_rhel_centos_rocky() {
    echo "Uninstalling stunnel on Red Hat/CentOS/Rocky-based system..."
    sudo yum remove -y stunnel
    sudo rm -rf /var/run/stunnel4/ /etc/stunnel

    if ! command -v stunnel > /dev/null; then
        echo "stunnel uninstalled successfully!"
    else
        echo "Failed to uninstall stunnel."
        exit 1
    fi
}

# Uninstall stunnel on SUSE-based systems
uninstall_stunnel_suse() {
    echo "Uninstalling stunnel on SUSE-based system..."
    sudo zypper remove -y stunnel
    sudo rm -rf /var/run/stunnel4/ /etc/stunnel

    if ! command -v stunnel > /dev/null; then
        echo "stunnel uninstalled successfully!"
    else
        echo "Failed to uninstall stunnel."
        exit 1
    fi
}

# Function to detect the OS and install or uninstall stunnel
detect_and_handle() {
    ACTION=$1

    # Check if the OS release file exists
    if [ ! -f /etc/os-release ]; then
        echo "The file /etc/os-release does not exist. Unable to detect OS."
        exit 1
    fi

    # Source the OS release file
    . /etc/os-release

    case "$ID" in
    ubuntu|debian)
        if [ "$ACTION" == "$INSTALL" ]; then
            install_stunnel_ubuntu_debian
        elif [ "$ACTION" == "$UNINSTALL" ]; then
            uninstall_stunnel_ubuntu_debian
        fi
        ;;
    centos|rhel|rocky)
        if [ "$ACTION" == "$INSTALL" ]; then
            install_stunnel_rhel_centos_rocky
        elif [ "$ACTION" == "$UNINSTALL" ]; then
            uninstall_stunnel_rhel_centos_rocky
        fi
        ;;
    suse|sles)
        if [ "$ACTION" == "$INSTALL" ]; then
            install_stunnel_suse
        elif [ "$ACTION" == "$UNINSTALL" ]; then
            uninstall_stunnel_suse
        fi
            ;;
        *)
            echo "Unsupported OS: $ID"
            exit 1
            ;;
    esac
}

# Default action is install
ACTION=$(echo "${1:-$INSTALL}" | tr '[:upper:]' '[:lower:]')

if [[ "$ACTION" != "$INSTALL" && "$ACTION" != "$UNINSTALL" ]]; then
    echo "Invalid argument. Please specify 'install' or 'uninstall'."
    exit 1
fi

# Start the installation or uninstallation process
detect_and_handle "$ACTION"
