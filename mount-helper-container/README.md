# EIT Mount-Helper Container Service 

This is a REST based mount-helper-container service which is used for mounting EIT based fileShare mounts on host-system. This is used by IKS addon `vpc-file-csi-driver`.

## Supported Orchestration Platforms

| IKS/ROKS Version | Image/Distribution | Mount-Helper-Container Supported | 
|------|-------|--------|
| ROKS 4.14 | RHEL 8.9 | |
| ROKS 4.13 | RHEL 8.8 | |
| ROKS 4.12 | RHEL 8.8 | |
| ROKS 4.11 | RHEL 8.8 | |
| IKS 1.28 | Ubuntu 20.04 | |
| IKS 1.27 | Ubuntu 20.04 | |
| IKS 1.26 | Ubuntu 20.04 | |
| IKS 1.25 | Ubuntu 20.04 | |
| IKS 1.24 | Ubuntu 20.04 | |

## Package Dependencies

| Mount Helper Container Version | Dependencies |
|------|-------|
| 1.0.0 | mount-helper-1.0.0 |

## Package Building

**For debian based system,**

1. Build debian based package `make deb-build`
2. Copy the package on the host system it is required.
3. Run `apt-get update`
4. Run `apt install -y mount-helper-container-x.y.z.deb`. This will install all required files.

**For rpm based system,**

1. Build rpm based packages use `make rpm-build`
2. Copy the package on the host system it is required.
3. Run `yum install -y mount-helper-container-x.y.z.rpm`. This will install all required files.

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
