#!/bin/bash

SBIN_SCRIPT="/sbin/mount.ibmshare"
CERT_PATH="/tmp/metadata"

cp /tmp/charon-log.conf /etc/strongswan.d/

$SBIN_SCRIPT -INSTALL_ROOT_CERT $CERT_PATH
