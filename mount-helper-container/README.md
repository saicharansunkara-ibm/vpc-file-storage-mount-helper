# EIT Mount-Helper Container Service 

This is a REST based mount-helper-container service which is used for mounting EIT based fileShare mounts on host-system. This is used by IKS addon `vpc-file-csi-driver`.

## Supported Orchestration Platforms

| IKS/ROKS Version | Image/Distribution | Mount-Helper-Container Supported | 
|------|-------|--------|
| ROKS 4.16+ | [RHEL Versions](https://github.com/IBM/vpc-file-storage-mount-helper/tree/main/mount-helper/packages/rhel) | :heavy_check_mark: |
| IKS 1.30+ | [Ubuntu Versions](https://github.com/IBM/vpc-file-storage-mount-helper/tree/main/mount-helper/packages/ubuntu) | :heavy_check_mark: |

## Changelog + Package Dependencies:

| Mount Helper Container Version | Dependencies | Release | Date | Changes |
|------|-------|--------|--------|--------|
| 0.0.2 | mount.ibmshare-0.0.3 | v0.0.5 | April 05, 2024 | - Initial production release |
| 0.0.3 | mount.ibmshare-0.0.4 | v0.0.6 | May 24, 2024 | - Changed UNIX socket path |
| 0.0.4 | mount.ibmshare-0.0.5 | v0.0.8 | Aug 16, 2024 | - Changed mount.ibmshare dep to 0.0.5 (VSI reboot fix, MH update handling, RHEL 8.10 packages added) |
| 0.0.5 | mount.ibmshare-0.0.6 | v0.0.9 | Aug 26, 2024 | - Changed mount.ibmshare dep to 0.0.6 (RHEL 9 offline package support) |
| 0.0.6 | mount.ibmshare-0.0.7 | v0.1.0 | Oct 1, 2024 | - Changed mount.ibmshare dep to 0.0.6 (Fix bug with --update flag) |
| 0.0.7 | mount.ibmshare-0.0.8 | v0.1.1 | Nov 8, 2024 | - Changed mount.ibmshare dep to 0.0.7 (Add Cert for dev env) |
| 0.0.8 | mount.ibmshare-0.0.9 | v0.1.2 | Feb 17, 2025 | - Changed mount.ibmshare dep to 0.0.8 (Fix bug with --update flag, VPC Region Naming convention, Add cert for dev) |
| 0.0.9 | mount.ibmshare-0.1.0 | v0.1.3 | Feb 26, 2025 | - Changed mount.ibmshare dep to 0.0.9 (Add tls Cert for dev and stage) |
| 0.1.0 | mount.ibmshare-0.1.1 | v0.1.4 | March 9, 2025 | - Changed mount.ibmshare dep to 0.1.0 (Add Cert for Montreal Prod) |
| 0.1.1 | mount.ibmshare-0.1.7 | v0.2.0 | July 30, 2025 | - Changed mount.ibmshare dep to 0.1.0 (Add Support fo RHEL 9.6 + Mh misc changes https://github.com/IBM/vpc-file-storage-mount-helper/compare/0.1.4...0.1.9) |

## Package Building

**For debian based system,**

1. Build debian based package `make deb-build`
2. Copy the package on the host system it is required.
3. Run `apt-get update`
4. Run `apt install -y mount-helper-container-x.y.z.deb`. This will install all required files.

**For rpm based system,**

1. Build rpm based packages use `make rpm-build`
2. Copy the package on the host system it is required.
3. Run `yum install -y mount-helper-container-x.y.z.rpm --nogpgcheck`. This will install all required files.

The packages will be created inside **/mount-helper-container** folder

## Testing changes locally

- Use make target `make test` to see if all unit test cases are passing for your changes.
- Use make target `make build`. This runs go build command on /server/server.go. Binary can be found under /bin folder.

## How to update packages
TBD

## How to contribute

If you have any questions or issues you can create a new issue in the repo.

Pull requests are very welcome! Make sure your patches are well tested. Ideally create a topic branch for every separate change you make. For example:

1. Fork the repo
2. Create your feature branch (git checkout -b my-new-feature)
3. Commit your changes (git commit -am 'Added some feature')
4. Push to the branch (git push origin my-new-feature)
5. Create new Pull Request
6. Add the test results in the PR
