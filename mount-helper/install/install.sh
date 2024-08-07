#!/bin/bash
#
# Copyright (c) IBM Corp. 2023. All Rights Reserved.
# Project name: VPC File Storage Mount Helper
# This project is licensed under the MIT License, see LICENSE file in the root directory.

INSTALL_ARG="$1"

APP_NAME="IBM Mount Share Helper"
SCRIPT_NAME="mount.ibmshare"
SBIN_SCRIPT="/sbin/$SCRIPT_NAME"
MIN_PYTHON3_VERSION=3.4
MIN_STRONGSWAN_VERSION=5.4
NA="NOT_SUPPORTED"
APT="apt-get -y install"
YUM="yum install -y"
ZYP="zypper install -y"
LINUX_INSTALL_APP=""
INSTALL_APP="Unknown"
NAME=$(grep -oP '(?<=^NAME=).+' /etc/os-release | tr -d '"')
VERSION=$(grep -oP '(?<=^VERSION_ID=).+' /etc/os-release | tr -d '"')
ARCH="uname -m"
MAJOR_VERSION=${VERSION%.*}
INSTALLED_PACKAGE_LIST="/etc/pre_installed_packages.txt"

#              Name              Min Version    Install
LINUX_UBUNTU=("Ubuntu"           "18"           "$APT")
LINUX_DEBIAN=("Debian GNU/Linux" "10"           "$APT")
LINUX_CENTOS=("CentOS Linux"     "7"            "$YUM")
LINUX_ROCKY=("Rocky Linux"       "8"            "$YUM")
LINUX_FEDORA=("Fedora Linux"     $NA            $NA)
LINUX_SUSE=("SLES"               "12"           "$ZYP")
LINUX_RED_HAT=("Red Hat Enterprise Linux" "7" "$YUM")


log () {
    echo "$1"
}

exit_err () {
    log "Install failed: $1"
    exit -1
}

exit_ok () {
    echo 
    echo "$APP_NAME: $1."
    exit 0
}

check_linux_version () {
    MIN_VER=$1
    if [ "$MIN_VER" == "$NA" ]; then
        exit_err "IbmMountHelper Install not supported $NAME"
        return 0
    fi;

    if version_less_than $VERSION $MIN_VER; then
        exit_err "Can only install on $NAME version $MIN_VER or greater. Current version:$VERSION"
    fi;
    log "Linux($NAME) Version($VERSION) distro"
}

is_linux () {
    eval 'ARRAY=( "${'"$1"'[@]}" )'
    local _NAME=${ARRAY[0]}
    local _MIN_VER=${ARRAY[1]}

    if [[ "$NAME" == "$_NAME"* ]]; then
        check_linux_version $_MIN_VER
        log "Linux version supported - $NAME ($VERSION)"
        set_install_app "${ARRAY[2]}"
        return 0
    fi;
    return 1
}

command_not_exist () {
    type -p $1 &>/dev/null
    if [ 0 -eq $? ]; then
        return 1
    fi;
    return 0
}

command_exist () {
    type -p $1 &>/dev/null ;
}

check_result () {
  code="$?" 
  if [ $code != "0" ]; then
    exit_err "$1 ExitCode($code)"
  fi;
}

version_less_than() { 
    ans="$(printf '%s\n%s\n' "$1" "$2" | sort -t '.' -k 1,1 -k 2,2 -k 3,3 -k 4,4 -g | head -n 1)"
    if [ "$ans" == "$2" ]; then
        return 1
    fi;
    return 0
}

set_install_app() { 
    LINUX_INSTALL_APP="$1"
    array=($LINUX_INSTALL_APP)
    INSTALL_APP=${array[0]}
    if command_not_exist "$INSTALL_APP"; then
        exit_err "Missing install app: $INSTALL_APP"
    fi;
    echo "Using install app: $INSTALL_APP" 
}


_remove_apps() { 
    apps=($@)
    $SBIN_SCRIPT -TEARDOWN_APP
    for ((i=${#apps[@]}-1; i>=0; i--)); do
        app="${apps[$i]}"
        log "Removing package $app"

        # Condition to check if app name consists of mount.ibmshare
        if [[ "$app" == *"mount.ibmshare"* ]]; then
            app="mount.ibmshare"
        fi

        if is_linux LINUX_UBUNTU; then
            # Skip uninstallation in case /etc/pre_installed_packages.txt is missing in system
            if [ ! -f "$INSTALLED_PACKAGE_LIST" ]; then
                log "Skipping uninstallation of packages as file '$INSTALLED_PACKAGE_LIST' is missing..."
                exit -1
            fi
            # Read preInstalled packages from system
            if grep -q "^$app" $INSTALLED_PACKAGE_LIST ; then
                log "Skipping package $app for uninstallation as it was pre-installed on the system"
                continue 2
            fi
            apt-get purge -y --no-auto-remove "$app"
        elif is_linux LINUX_RED_HAT; then
            if [[ $VERSION == 8.8 || $VERSION == 8.9 || $VERSION == 8.10 ]]; then
                # Skip uninstallation in case /etc/pre_installed_packages.txt is missing in system
                if [ ! -f "$INSTALLED_PACKAGE_LIST" ]; then
                    log "Skipping uninstallation of packages as file '$INSTALLED_PACKAGE_LIST' is missing..."
                    exit -1
                fi
                # Read preInstalled packages from system
                if grep -q "^$app" $INSTALLED_PACKAGE_LIST ; then
                    log "Skipping package $app for uninstallation as it was pre-installed on the system"
                    continue 3
                fi
                rpm -e --allmatches --nodeps "$app"
            else
                rpm -e --allmatches --nodeps "$app"
            fi
        else
            if [ "$INSTALL_APP" == "apt-get" ]; then
                apt-get purge -y --auto-remove "$app"
            elif [ "$INSTALL_APP" == "zypper" ]; then
                zypper remove -y --clean-deps "$app"
            else
                eval "$INSTALL_APP remove -y $app"
            fi
        fi
    done
}

extract_version() {
    ver=$1
    python3 -c "import re; m=re.findall('[0-9]+\.[0-9]+\.?[0-9]*', '$ver'); print(m[0] if len(m)>0 else '' )"

}

check_available_version() {
    app=$1
    min_ver=$2
    if [ "$INSTALL_APP" == "apt-get" ]; then
        cmd="apt show  "$app"  2>/dev/null  | grep -i \"Version:\""
    elif [ "$INSTALL_APP" == "zypper" ]; then
        cmd="zypper info "$app" | grep \"Version\""
    else
        cmd="yum info "$app" | grep -i version"
    fi

    app_ver=$(eval "$cmd")
    app_ver=$(extract_version "$app_ver")

    if [[ "$app_ver" == "" ]]; then
        exit_err "Package not available: $app"
    fi
    if version_less_than $app_ver $min_ver; then
        exit_err "Package($app) - Available Version($app_ver) - Min Version($min_ver)"
    fi
    echo "Package($app) - Available Version($app_ver) - Min Version($min_ver)"
}

_install_app() { 
    PACKAGE_NAME=$1
    log "Installing package $PACKAGE_NAME"
    eval "$LINUX_INSTALL_APP $PACKAGE_NAME"
    check_result "Problem installing package: $PACKAGE_NAME"
    log "Updating package $PACKAGE_NAME"
    # Update the package 
    if [ "$LINUX_INSTALL_APP" == "$YUM" ]; then
        eval "yum update -y $PACKAGE_NAME"
    elif [ "$LINUX_INSTALL_APP" == "$APT" ]; then
        eval "apt-get install --only-upgrade -y $PACKAGE_NAME"
    elif [ "$LINUX_INSTALL_APP" == "$ZYP" ]; then
        eval "zypper update -y $PACKAGE_NAME"
    fi
}

_install_apps() { 
    apps=($@)

    if is_linux LINUX_UBUNTU && [[ "$INSTALL_ARG" != "--update" && "$INSTALL_ARG" != "--update-stage" ]]; then
        # Storing all the packages which come by default on the system. This will be used in uninstalltion case.
        dpkg -l | grep '^ii' | awk '{print $2}' > $INSTALLED_PACKAGE_LIST
    elif is_linux LINUX_RED_HAT && [[ "$INSTALL_ARG" != "--update" && "$INSTALL_ARG" != "--update-stage" ]]; then
        rpm -qa --queryformat '%{NAME}\n' > $INSTALLED_PACKAGE_LIST
    fi

    for app in "${apps[@]}"; do 
        if [[ (( "$INSTALL_ARG" == "--update" || "$INSTALL_ARG" == "--update-stage" )) && $app != "mount.ibmshare"* ]]; then
            continue
        fi
        if grep -q -i "strongswan" <<< "$app" && ! is_linux LINUX_UBUNTU && ! is_linux LINUX_RED_HAT; then
            check_available_version "$app" $MIN_STRONGSWAN_VERSION
        fi

        if is_linux LINUX_UBUNTU && ([[ ! "$ARCH" = *"s390x"* ]]); then
            # Read preInstalled packages from system
            if [[ $app != *"python"* && $(grep -q "^$app" $INSTALLED_PACKAGE_LIST; echo $?) -eq 0 ]] ; then
                log "Skipping package $app for installation as it is pre-installed on the system"
                continue 
            fi
            log "Installing package $app"
            if [[ $app == "mount.ibmshare"* || $app == *"python"* ]]; then
                dpkg --force-all -i "$app"
                continue
            fi
            PACKAGE_DIR="packages/ubuntu/$VERSION"
            dpkg --force-all -i "$PACKAGE_DIR/$app"*
        elif  is_linux LINUX_RED_HAT && ([[ $VERSION == 8.8 || $VERSION == 8.9 || $VERSION == 8.10 ]]); then
            # Read preInstalled packages from system
            if [[ $app != *"python"* && $(grep -q "^$app" $INSTALLED_PACKAGE_LIST; echo $?) -eq 0 ]] ; then
                log "Skipping package $app for installation as it is pre-installed on the system"
                continue 
            fi
            log "Installing package $app"
            if [[ $app == "mount.ibmshare"* ]]; then
                rpm -i "$app" --force --nodeps --nodigest --nosignature
                continue
            fi
            if [[ $app == *"python"* ]]; then
                rpm -i "$app" --force --nodeps
                continue
            fi
            PACKAGE_DIR="packages/rhel/$VERSION"
            rpm -i "$PACKAGE_DIR/$app"* --force --nodeps
        else
            _install_app "$app" 
        fi
    done
}

install_apps() { 
    if [ "$INSTALL_ARG" == "--uninstall" ]; then
        _remove_apps "$@" 
        exit_ok "UnInstall completed ok"
    fi
    _install_apps "$@" 
}

get_current_python_version () {
  echo "$(python3 --version 2>&1 | awk '{print $2}')"
}

wait_till_true () {
    action="$1" 
    secs=$2
    echo "Wait: $1"
    for i in `seq 1 10`; do
        eval "$action" &>/dev/null
        if [ "$?" == "0" ]; then
            return
        fi
        sleep $secs
    done 
}

check_python3_installed () {
    if command_exist cloud-init; then
        log "Wait for cloud-init to complete."
        cloud-init status --wait --long
    fi

    if is_linux LINUX_RED_HAT; then
        PYTHON3_PACKAGE=packages/rhel/$VERSION/python*.rpm
    elif is_linux LINUX_UBUNTU; then
        PYTHON3_PACKAGE=packages/ubuntu/$VERSION/python*.deb
    else
        PYTHON3_PACKAGE=$1
    fi
    if command_not_exist python3; then
        if [ "$PYTHON3_PACKAGE" == "" ]; then
            exit_err "Python3 not installed"
        fi;
        _install_apps "$PYTHON3_PACKAGE"
    fi;
    PYTHON3_VERSION="$(get_current_python_version)"
    if version_less_than $PYTHON3_VERSION $MIN_PYTHON3_VERSION; then
        exit_err  "Can only install with Python3 version $MIN_PYTHON3_VERSION or greater. Current version:$PYTHON3_VERSION"
    fi;
    log "Python $PYTHON3_VERSION installed"
}

disable_metadata () {
    log "Disabling metadata service"
    sed -i 's/USE_METADATA_SERVICE = True/USE_METADATA_SERVICE = False/' $SBIN_SCRIPT
}

init_mount_helper () {
    if [[ "$INSTALL_ARG" == "region="* ]]; then
        log "Updating config file: ./share.conf"
        sed -i "s/region=.*/$INSTALL_ARG/" ./share.conf
        INSTALL_ARG=""
    fi
    if [[ "$INSTALL_ARG" == "stage" || "$INSTALL_ARG" == "--update-stage" ]]; then
        CERT_PATH="./dev_certs/metadata"
        log "Installing certs for stage environment..."
        $SBIN_SCRIPT -INSTALL_ROOT_CERT $CERT_PATH
        check_result "Problem installing ssl certs"
        exit_ok "Install completed ok"
    fi
    if [[ "$INSTALL_ARG" == "" || "$INSTALL_ARG" == "--update" ]]; then
        INSTALL_ARG="metadata"
    fi
    log "Installing certs for: $INSTALL_ARG"
    CERT_PATH="./certs/$INSTALL_ARG"
    if [ ! -d $CERT_PATH ]; then
        exit_err "$CERT_PATH cert folder does not exist" 
    fi
    if [ "$INSTALL_ARG" != "metadata" ]; then
        disable_metadata
    fi
    $SBIN_SCRIPT -INSTALL_ROOT_CERT $CERT_PATH
    check_result "Problem installing ssl certs"
    exit_ok "Install completed ok"
}

if is_linux LINUX_UBUNTU; then
    export DEBIAN_FRONTEND=noninteractive
    check_python3_installed 
    apt-get -y remove needrestart

    # Define the path to the package list file based on the Ubuntu version
    PACKAGE_LIST_PATH="packages/ubuntu/$VERSION/package_list"

    # Check if the package list file exists
    if [ ! -f "$PACKAGE_LIST_PATH" ]; then
        exit_err "Package list file '$PACKAGE_LIST_PATH' does not exist"
    fi

    # Read the package list from the file
    packages=()
    while IFS= read -r line; do
        packages+=("$line")
    done < "$PACKAGE_LIST_PATH"

    # Install the packages in the defined order
    install_apps "${packages[@]}" mount.ibmshare*.deb
    init_mount_helper
fi;

if is_linux LINUX_DEBIAN; then
    export DEBIAN_FRONTEND=noninteractive
    check_python3_installed 
    install_apps strongswan-starter strongswan-swanctl nfs-common mount.ibmshare*.deb
    init_mount_helper
fi;


if is_linux LINUX_RED_HAT; then
    check_python3_installed python3
    if [[ $VERSION == 8.8 || $VERSION == 8.9 || $VERSION == 8.10 ]]; then
        # Define the path to the package list file based on the Ubuntu version
        PACKAGE_LIST_PATH="packages/rhel/$VERSION/package_list"

        # Check if the package list file exists
        if [ ! -f "$PACKAGE_LIST_PATH" ]; then
            exit_err "Package list file '$PACKAGE_LIST_PATH' does not exist"
        fi

        # Read the package list from the file
        packages=()
        while IFS= read -r line; do
            packages+=("$line")
        done < "$PACKAGE_LIST_PATH"

        # Install the packages in the defined order
        install_apps "${packages[@]}" mount.ibmshare*.rpm
        init_mount_helper 
    else
        if [ "$INSTALL_ARG" != "--uninstall" ]; then
            yum install -y --nogpgcheck "https://dl.fedoraproject.org/pub/epel/epel-release-latest-$MAJOR_VERSION.noarch.rpm"
        fi
        install_apps strongswan  nfs-utils iptables mount.ibmshare*.rpm
        init_mount_helper
    fi
fi;

if is_linux LINUX_CENTOS; then
    check_python3_installed python3
    install_apps epel-release strongswan strongswan-sqlite nfs-utils mount.ibmshare*.rpm
    init_mount_helper
fi;

if is_linux LINUX_ROCKY; then
    check_python3_installed python39
    install_apps epel-release strongswan strongswan-sqlite nfs-utils mount.ibmshare*.rpm
    init_mount_helper
fi;

if is_linux LINUX_SUSE; then
    check_python3_installed 
    # causing install failures - so disable it
    systemctl disable --now packagekit
    install_apps strongswan nfs-client mount.ibmshare*.rpm
    init_mount_helper
fi;

if is_linux LINUX_FEDORA; then
    echo "Locked down distro not supported"
fi;


exit_err "IbmMountHelper Install not supported $NAME $VERSION"
