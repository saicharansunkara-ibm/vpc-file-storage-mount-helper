export LINT_VERSION="1.43.0"
GOPACKAGES=$(shell go list ./... | grep -v /vendor/ | grep -v /tests)

NAME := mount-helper-container
APP_VERSION := 1.0.0
MAINTAINER := "IKS Storage"
DESCRIPTION := "IBM Mount Share helper container service"
LICENSE := "IBM"
DEB_ARCH := all
RPM_ARCH := x86_64
RPM_RELEASE_NUM := 1

BUILD_DIR := $(NAME)-$(APP_VERSION)
BIN_DIR := bin

DEBIAN_CONTROL := $(BUILD_DIR)/DEBIAN/control
REDHAT_SPEC := $(BUILD_DIR)/red-hat.spec

build:
	CGO_ENABLED=0 GOOS=$(go env GOOS) GOARCH=$(go env GOARCH) go build -mod mod -o ${BIN_DIR}/mhelper-container-server ./server/server.go

build-linux:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -mod mod -o ${BIN_DIR}/mhelper-container-server -ldflags "-s -w" -a ./server/server.go

addpackage:
	go mod tidy

clean:
	rm -rf bin

deps:
	echo "Installing dependencies ..."
	go mod download
	go get github.com/pierrre/gotestcover
	go install github.com/pierrre/gotestcover
	@if ! which golangci-lint >/dev/null || [[ "$$(golangci-lint --version)" != *${LINT_VERSION}* ]]; then \
		curl -sfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(shell go env GOPATH)/bin v${LINT_VERSION}; \
	fi


all:
	echo "Add actions here"

test:
	echo "test"

dev:
	echo "dev"

prod:
	echo "prod"
