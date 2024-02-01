/**
 *
 * Copyright 2024- IBM Inc. All rights reserved
 * SPDX-License-Identifier: Apache2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package main

import (
	"flag"
	"net"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"syscall"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

func init() {
	_ = flag.Set("logtostderr", "true") // #nosec G104: Attempt to set flags for logging to stderr only on best-effort basis.Error cannot be usefully handled.
	logger = setUpLogger()
	defer logger.Sync()
}

var (
	logger     *zap.Logger
	socketDir  = "/tmp/"
	socketPath = socketDir + "mysocket.sock"
)

// SystemOperation is an interface for system operations like mount and unmount.
type SystemOperation interface {
	Execute(command string, args ...string) (string, error)
}

// RealSystemOperation is an implementation of SystemOperation that performs actual system operations.
type RealSystemOperation struct{}

func (rs *RealSystemOperation) Execute(command string, args ...string) (string, error) {
	cmd := exec.Command(command, args...)

	output, err := cmd.CombinedOutput()
	return string(output), err
}

func setUpLogger() *zap.Logger {
	// Prepare a new logger
	atom := zap.NewAtomicLevel()
	encoderCfg := zap.NewProductionEncoderConfig()
	encoderCfg.TimeKey = "timestamp"
	encoderCfg.EncodeTime = zapcore.ISO8601TimeEncoder

	logger := zap.New(zapcore.NewCore(
		zapcore.NewJSONEncoder(encoderCfg),
		zapcore.Lock(os.Stdout),
		atom,
	), zap.AddCaller()).With(zap.String("ServiceName", "mount-helper-conatiner-service"))
	atom.SetLevel(zap.InfoLevel)
	return logger
}

func main() {
	// Always create fresh socket file
	os.Remove(socketPath)

	// Create a listener
	logger.Info("Creating unix socket listener...")
	listener, err := net.Listen("unix", socketPath)
	if err != nil {
		logger.Fatal("Failed to create unix socket listener:", zap.Error(err))
	}
	// Close the listener at the end
	defer listener.Close()

	// Handle SIGINT and SIGTERM signals to gracefully shut down the server
	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-signals
		os.Remove(socketPath)
		os.Exit(0)
	}()

	logger.Info("Starting mount-helper-container service...")

	// Create gin router
	router := gin.Default()

	sysOp := &RealSystemOperation{}

	// Add REST APIs to router
	router.POST("/api/mount", handleMounting(sysOp))
	router.POST("/api/umount", handleUnMount(sysOp))

	// Serve HTTP requests over Unix socket
	err = http.Serve(listener, router)
	if err != nil {
		logger.Fatal("Error while serving HTTP requests:", zap.Error(err))
	}
}


// handleMounting mounts ibmshare based file system stagingTargetPath to targetPath
func handleMounting(sysOp SystemOperation) gin.HandlerFunc {
	return func(c *gin.Context) {
		var request struct {
			StagingTargetPath string `json:"stagingTargetPath"`
			TargetPath        string `json:"targetPath"`
			FsType            string `json:"fsType"`
			RequestID         string `json:"requestID"`
		}

		if err := c.BindJSON(&request); err != nil {
			logger.Error("Invalid request: ", zap.Error(err))
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
			return
		}

		logger.Info("New mount request with values: ", zap.String("RequestID:", request.RequestID), zap.String("Staging Target Path:", request.StagingTargetPath), zap.String("Target Path:", request.TargetPath))

		// execute mount command
		options := "mount -t " + request.FsType + " -o secure=true " + request.StagingTargetPath + " " + request.TargetPath + " -v"

		logger.Info("Command to execute is: ", zap.String("Command:", options))

		output, err := sysOp.Execute("mount", "-t", request.FsType, "-o", "secure=true", request.StagingTargetPath, request.TargetPath, "-v")
		if err != nil {
			logger.Error("Mounting failed with error: ", zap.Error(err))
			logger.Error("Command output: ", zap.String("output", output))
			response := gin.H{
				"Error:": err.Error(),
			}
			c.JSON(http.StatusInternalServerError, response)
			return
		}

		logger.Info("Command output: ", zap.String("", output))
		c.JSON(http.StatusOK, gin.H{"message": "Request processed successfully"})
	}
}

// handleUnMount does umount on a targetPath provided
func handleUnMount(sysOp SystemOperation) gin.HandlerFunc {
	return func(c *gin.Context) {
		var request struct {
			TargetPath string `json:"targetPath"`
		}

		if err := c.BindJSON(&request); err != nil {
			logger.Error("Invalid request: ", zap.Error(err))
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
			return
		}

		logger.Info("New umount request with values: ", zap.String("Target Path:", request.TargetPath))

		output, err := sysOp.Execute("umount", request.TargetPath)

		if err != nil {
			logger.Error("Umount failed with error: ", zap.Error(err))
			logger.Error("Command output: ", zap.String("output", output))
			response := gin.H{
				"Error:": err.Error(),
			}
			c.JSON(http.StatusInternalServerError, response)
			return
		}

		c.JSON(http.StatusOK, gin.H{"Message": "Request processed successfully"})
	}
}

