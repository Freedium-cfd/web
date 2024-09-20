package main

import (
	"context"
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/client"
	"golang.org/x/net/proxy"
)

const (
	errorMsg           = "[Cloudflare proxy] Freedium proxy is not working, restarting containers..."
	proxyTestURL       = "http://ipinfo.io"
	telegramAPIBaseURL = "https://api.telegram.org/bot"
)

var (
	userName            = os.Getenv("USER_NAME")
	userPassword        = os.Getenv("USER_PASSWORD")
	proxyHost           = getEnvOrDefault("PROXY_HOST", "localhost")
	proxyPort           = getEnvOrDefault("PROXY_PORT", "9681")
	sleepDurationVar    = getEnvOrDefault("SLEEP_DURATION", "35")
	sleepDuration       int
	authFormatted       = formatAuth(userName, userPassword)
	containersToRestart = strings.Split(os.Getenv("CONTAINERS_TO_RESTART"), ",") // []string{"dante_1", "wgcf1"}
)

func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		log.Printf("Using environment variable for %s: %s", key, value)
		return value
	}
	log.Printf("Using default value for %s: %s", key, defaultValue)
	return defaultValue
}

func formatAuth(username, password string) string {
	if username != "" && password != "" {
		log.Printf("Formatting auth with username: %s", username)
		return fmt.Sprintf("%s:%s@", username, password)
	}
	log.Println("No authentication provided")
	return ""
}

func restartContainers() {
	log.Println("Starting container restart process")
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		log.Printf("Error creating Docker client: %v", err)
		return
	}
	defer cli.Close()

	stopTimeout := 10 // seconds
	stopOptions := container.StopOptions{
		Timeout: &stopTimeout,
	}
	log.Printf("Stop timeout set to %d seconds", stopTimeout)

	for _, containerName := range containersToRestart {
		log.Printf("Attempting to restart container: %s", containerName)
		if err := cli.ContainerRestart(context.Background(), containerName, stopOptions); err != nil {
			log.Printf("Error restarting %s: %v", containerName, err)
		} else {
			log.Printf("%s restarted successfully.", containerName)
		}
	}
	log.Println("Container restart process completed")
}

func sendMsg(text string, maxRetries int) bool {
	log.Printf("Attempting to send message: %s", text)
	tgToken := os.Getenv("TG_TOKEN")
	chatID := os.Getenv("TG_CHAT_ID")

	if tgToken == "" || chatID == "" {
		log.Println("TG_TOKEN or TG_CHAT_ID is not set, skipping message sending")
		return false
	}

	urlReq := fmt.Sprintf("%s%s/sendMessage?chat_id=%s&text=%s", telegramAPIBaseURL, tgToken, chatID, url.QueryEscape(text))

	for attempt := 0; attempt < maxRetries; attempt++ {
		log.Printf("Sending message attempt %d/%d", attempt+1, maxRetries)
		resp, err := http.Get(urlReq)
		if err != nil {
			log.Printf("Error sending message (attempt %d/%d): %v", attempt+1, maxRetries, err)
			if attempt < maxRetries-1 {
				log.Println("Retrying in 5 seconds...")
				time.Sleep(5 * time.Second)
			}
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode == http.StatusOK {
			log.Println("Message sent successfully.")
			return true
		}
		log.Printf("Unexpected status code: %d", resp.StatusCode)
	}

	log.Println("All retry attempts failed. Message not sent.")
	return false
}

func checkProxy(maxRetries int, retryDelay time.Duration) bool {
	proxyURL, err := url.Parse(fmt.Sprintf("socks5://%s%s:%s", authFormatted, proxyHost, proxyPort))
	if err != nil {
		log.Printf("Error parsing proxy URL: %v", err)
		return false
	}
	log.Printf("Checking proxy: %s", proxyURL)

	dialer, err := proxy.FromURL(proxyURL, proxy.Direct)
	if err != nil {
		log.Printf("Error creating proxy dialer: %v", err)
		return false
	}

	httpTransport := &http.Transport{
		Dial: dialer.Dial,
		DialContext: func(ctx context.Context, network, addr string) (net.Conn, error) {
			return dialer.(proxy.ContextDialer).DialContext(ctx, network, addr)
		},
	}
	client := &http.Client{Transport: httpTransport, Timeout: 10 * time.Second}
	log.Printf("HTTP client created with timeout: %v", client.Timeout)

	for attempt := 0; attempt < maxRetries; attempt++ {
		log.Printf("Proxy check attempt %d/%d", attempt+1, maxRetries)
		resp, err := client.Get(proxyTestURL)
		if err != nil {
			log.Printf("Error checking proxy (attempt %d/%d): %v", attempt+1, maxRetries, err)
			if attempt < maxRetries-1 {
				log.Printf("Retrying in %v seconds...", retryDelay.Seconds())
				time.Sleep(retryDelay)
			}
			continue
		}
		defer resp.Body.Close()

		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			log.Printf("Error reading response body: %v", err)
			continue
		}

		log.Printf("Proxy is working: Status Code %d, Body: %s", resp.StatusCode, string(body))
		return true
	}

	log.Println("All retry attempts failed. Proxy is not working.")
	return false
}

func main() {
	log.Println("Starting proxy monitoring service")

	if len(containersToRestart) == 0 {
		log.Fatal("CONTAINERS_TO_RESTART is not set")
	}

	log.Printf("Containers to restart: %v", containersToRestart)
	log.Printf("Proxy host: %s", proxyHost)
	log.Printf("Proxy port: %s", proxyPort)
	log.Printf("Auth formatted: %s", authFormatted)

	if proxyHost == "" || proxyPort == "" {
		log.Fatal("PROXY_HOST and PROXY_PORT must be set")
	}

	log.Printf("Proxy configuration: Host=%s, Port=%s", proxyHost, proxyPort)

	var err error
	sleepDuration, err = strconv.Atoi(sleepDurationVar)
	if err != nil {
		log.Fatalf("Invalid sleep duration: %v", err)
	}

	for {
		log.Printf("Waiting for %d seconds before next proxy check", sleepDuration)
		time.Sleep(time.Duration(sleepDuration) * time.Second)
		log.Println("Initiating proxy check...")
		if !checkProxy(3, 5*time.Second) {
			log.Println(errorMsg)
			log.Println("Sending error message via Telegram")
			sendMsg(errorMsg, 3)
			log.Println("Initiating container restart process")
			restartContainers()
		} else {
			log.Println("Proxy check successful")
		}
	}
}
