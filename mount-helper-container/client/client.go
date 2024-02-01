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
	"context"
	"fmt"
	"io"
	"net"
	"net/http"
	"strings"
)

func main() {
	// socket path
	socketPath := "/tmp/mysocket.sock"
	// payload
	payload := fmt.Sprintf(`{"stagingTargetPath":"fs1235","targetPath":"/test","fsType":"ext4","requestID":"1321"}`)
	// url
	url := "http://unix/api/mount"

	// Connect to the Unix domain socket on the host node
	// Create a custom dialer function for Unix socket connection
	dialer := func(ctx context.Context, network, addr string) (net.Conn, error) {
		return net.Dial("unix", socketPath)
	}

	// Create an HTTP client with the Unix socket transport
	client := &http.Client{
		Transport: &http.Transport{
			DialContext: dialer,
		},
	}

	//Create POST request
	req, err := http.NewRequest("POST", url, strings.NewReader(payload))
	if err != nil {
		fmt.Print("Failed to create EIT based umount request. Failed wth error: %w", err)
		return
	}
	req.Header.Set("Content-Type", "application/json")
	response, err := client.Do(req)
	if err != nil {
		//TODO: Add retry logic to continuously send request with 5 sec delay. Is it really required?
		// Can we make a systemctl call from here to the local system?
		fmt.Print("Failed to send EIT based request. Failed with error: %w", err)
		return
	}
	defer response.Body.Close()
	body, err := io.ReadAll(response.Body)
	if err != nil {
		fmt.Println("Error")
		return
	}

	if response.StatusCode != http.StatusOK {
		fmt.Printf("Response from mount-helper-container server: %s ,ResponseCode: %v", string(body), response.StatusCode)
		return
	}
}
