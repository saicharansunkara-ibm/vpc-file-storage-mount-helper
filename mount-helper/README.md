```
Copyright (c) IBM Corp. 2023. All Rights Reserved.
Project name: VPC File Storage Mount Helper
This project is licensed under the MIT License, see LICENSE file in the root directory.
```

# Mount Helper
Mount helper is an open source automation tool that helps to establish secure IPsec connection between customer virtual server instance (VSI) and storage server. The mount helper ensures that the communication between the customer VSI and the file share is encrypted in transit.

For more information, see the [IBM Cloud File Share Mount Helper utility](https://cloud.ibm.com/docs/vpc?topic=vpc-file-storage-vpc-eit&interface=ui#fs-mount-helper-utility) topic in the IBM Cloud Docs.

## How to build mount helper packages
Mount helper packages can be built from the source code that is available in public GitHub. Follow steps below to build packages for Debian and RedHat instances.
1. Clone mount helper code from github.com
```
git clone git@github.com:IBM/vpc-file-storage-mount-helper.git
```
2. Go to cloned repo directory
```
cd vpc-file-storage-mount-helper
```
3. Run make command to build mount helper .deb/.rpm packages.
```
make iks-prod
```
4. You can find mount-ibmshare-<version>.rpm and mount-ibmshare-<version>.deb packages in current directory

## How to contribute code
Mount helper code is open sourced and anybody can contribute to the code. Follow steps below to contribute mount helper code.
1. Fork mount helper code from https://github.com/IBM/vpc-file-storage-mount-helper
2. Clone your forked repo
```
git clone git@github.com:<user_name>/vpc-file-storage-mount-helper.git
```
3. Create a new branch
```
git checkout -b <BR_NAME>
```
4. Make code changes and update/add tests in test directory.
5. Run unit tests.
```
cd test
./run_test.sh
Make sure all the tests are passed.
```
6. Commit code and push.
```
git add <files>
git commit
git push
```
7. Create a pull request.
8. If you want to create a new version for the package please change version in following files
   - Update APP_VERSION in Makefile.
   - Update .github/workflows/release.yml to create a new release in GitHub.
9. Before creating pull request make sure your workflow ran successfully.
   - Go to Actions in GitHub on your forked repo.
   - Check the latest workflow run.
   -  Fix if there are any issues.
10. Finally create pull request.

## How to install
1. You can follow the procedure to build packages to build .deb/.rpm packages (OR)
2. You can download the packages directly from GitHub releases.
   The latest packages are available at: https://github.com/IBM/vpc-file-storage-mount-helper/releases
```
curl -LO https://github.com/IBM/vpc-file-storage-mount-helper/releases/download/latest/mount-helper.latest.deb
(OR)
curl -LO https://github.com/IBM/vpc-file-storage-mount-helper/releases/download/latest/mount-helper.latest.rpm
```
3. Then run install command
```
apt install mout-ibmshare-<version>.deb (For Ubuntu)
yum install mount-ibmshare-<version>.rpm (For RedHat)
```
4. Few tips to verify installation
    - Check for file /sbin/mount.ibmshare, if the file is not found then installation must have failed. Check the logs and fix/report.
    - Check strongswan status: systemctl status strongswan. This should be in active(running) state.
    - Check for config file: /etc/ibmcloud/share.conf

## Supported Platform:
1. RedHat versions 7, 8, 9
2. Ubuntu versions 20, 22

## How to update packages:
1. Uninstall currently installed package
```
apt remove mount-helper
yum remove mount-helper
```
2. Download the latest packages from GitHub and install.
3. TODO
   - If we are able to host packages on any web server to be able to install directly, then below commands are enough to update the packages. We have to make sure latest packages are uploaded to the repo server.
```
apt update mount-ibmshare
yum update mount-ibmshare
```

## Dependencies of these Packages:
### Ubuntu:
    Python3
    nfs-common
    strongswan-swanctl, charon-systemd
### RedHat:
    python3
    nfs-utils
    epel-release
    strongswan, strongswan-sqlite

## Release/Package versioning process details
   - The packages are versioned as x.x.x
   - Initial version is: 1.0.0
   - The releases are versioned in the same manner: https://github.com/IBM/vpc-file-storage-mount-helper/releases
   - But in the GitHub you can find a release with version tag “latest”, this always points to the latest version.

## Current available packages which anyone can download and install with version
```
https://github.com/IBM/vpc-file-storage-mount-helper/releases
```

## Version metrics for both packages
The currently installed packages and it's details can be verified using below comamnds.
### Ubuntu
```
apt list | grep mount-ibmshare  ---> This shows the currently installed helper package.
apt show mount-ibmshare-<version>   ---> This shows package details.
```
### RedHat
```
yum list | grep mount-ibmshare
yum info mount-ibmshare
```

## Code coverage and unit test cases
   - Unit test cases are located in “test” directory of the mount helper repo.
