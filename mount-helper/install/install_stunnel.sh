#!/bin/bash

# Create necessary directories
setup_stunnel_directories() {
    sudo mkdir -p /var/run/stunnel4/ /etc/stunnel
    sudo chmod 744 /var/run/stunnel4/ /etc/stunnel
}

# Install stunnel on Ubuntu/Debian-based systems
install_stunnel_ubuntu_debian() {
    echo "Installing stunnel on Ubuntu/Debian-based system..."

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
    echo "Installing stunnel on Red Hat/CentOS/Rocky-based system..."

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
    echo "Installing stunnel on SUSE-based system..."

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

# Function to detect the OS and install stunnel
detect_and_install() {
    # Check the OS distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case "$ID" in
            ubuntu|debian)
                install_stunnel_ubuntu_debian
                ;;
            centos|rhel|rocky)
                install_stunnel_rhel_centos_rocky
                ;;
            suse|sles)
                install_stunnel_suse
                ;;
            *)
                echo "Unsupported OS: $ID"
                exit 1
                ;;
        esac
    else
        echo "Could not detect the operating system."
        exit 1
    fi
}

# Start the installation process
detect_and_install
