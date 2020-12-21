package main

import (
	"bufio"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)
import MQTT "github.com/eclipse/paho.mqtt.golang"

var commands = make(chan string)
var TV_ID = getEnv("TV_ID", "0000")

func payloadToCommand(payload string) (string, error) {
	switch payload {
	case "MAKE_SOURCE_ACTIVE":
		return "as", nil
	case "POWER_ON":
		return fmt.Sprintf("on %s", TV_ID), nil
	case "POWER_OFF":
		return fmt.Sprintf("standby %s", TV_ID), nil
	default:
		return "", errors.New(fmt.Sprintf("Payload %s is unsupported", payload))
	}
}

func defaultHandler(client MQTT.Client, msg MQTT.Message) {
	fmt.Printf("< [%s]: %s\n", msg.Topic(), string(msg.Payload()))
	command, err := payloadToCommand(string(msg.Payload()))
	if err != nil {
		fmt.Printf("ERROR: %s\n", err)
		return
	}
	commands <- command
}

func setupMqtt() {
	broker := getEnv("MQTT_BROKER", "tcp://iot.labs:1883")
	topic := getEnv("MQTT_TOPIC", "KODI_ON")
	id := "MQTT_to_CEC"

	fmt.Printf("Connecting to %s as %s\n", broker, id)
	opts := MQTT.NewClientOptions()
	opts.AddBroker(broker)
	opts.SetClientID(id)
	opts.SetDefaultPublishHandler(defaultHandler)
	opts.SetKeepAlive(5 * time.Second)
	client := MQTT.NewClient(opts)

	if token := client.Connect(); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}

	fmt.Println("Connected")
	fmt.Printf("Subscribing to %s\n", topic)
	if token := client.Subscribe(topic, 0, nil); token.Wait() && token.Error() != nil {
		fmt.Println(token.Error())
		os.Exit(1)
	}

	fmt.Println("Subscribed")
}

func runCecClient() {
	c := exec.Command("cec-client", "-d", "1")
	stdin, err := c.StdinPipe()
	if err != nil {
		panic(err)
	}
	stdout, err := c.StdoutPipe()
	if err != nil {
		panic(err)
	}
	reader := bufio.NewReader(stdout)
	err = c.Start()
	if err != nil {
		panic(err)
	}

	go func() {
		for command := range commands {
			_, err = stdin.Write([]byte(fmt.Sprintf("%s\n", command)))
			if err != nil {
				panic(err)
			}
			fmt.Printf("Wrote <%s>\n", strings.TrimSpace(command))
		}
	}()

	go func() {
		for true {
			answer, err := reader.ReadString('\n')
			if err != nil {
				panic(err)
			}
			answer = strings.TrimSpace(answer)
			fmt.Printf("Got back: <%s>\n", answer)
		}
	}()

	c.Wait()
}
func main() {
	setupMqtt()
	fmt.Printf("Using TV_ID: %s\n", TV_ID)
	runCecClient()
}
func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}
