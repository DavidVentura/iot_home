package main

import (
	"fmt"
	"io/ioutil"
	"net"
	"os"
	"strings"
	"time"
)
import MQTT "github.com/eclipse/paho.mqtt.golang"

var tcpData = make(chan string, 1)
var MACToName = map[string]string{
	"F4:60:E2:B4:68:C4": "David",
	"A4:50:46:5B:FD:E1": "Tati",
}

func setupMqtt() MQTT.Client {
	broker := getEnv("MQTT_BROKER", "tcp://iot.labs:1883")
	id := "BRIDGE_TO_MQTT"

	fmt.Printf("Connecting to %s as %s\n", broker, id)
	opts := MQTT.NewClientOptions()
	opts.AddBroker(broker)
	opts.SetClientID(id)
	opts.SetKeepAlive(5 * time.Second)
	client := MQTT.NewClient(opts)

	if token := client.Connect(); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}

	fmt.Println("Connected")
	return client
}

func textToPresent(packet string) []string {
	var ret []string

	for _, line := range strings.Split(packet, "\n") {
		if val, ok := MACToName[line]; ok {
			// fmt.Printf("MAC found %s = %s\n", line, val)
			ret = append(ret, val)
		}
	}

	return ret
}

func dataToMqtt(client MQTT.Client) {
	var prevState []string

	pub_topic := getEnv("MQTT_TOPIC", "PRESENCE")

	for packet := range tcpData {
		present := textToPresent(packet)
		gone := diff(present, prevState)
		_new := diff(prevState, present)

		if len(_new) > 0 {
			fmt.Printf("New: %v\n", _new)
		}
		if len(gone) > 0 {
			fmt.Printf("Gone: %v\n", gone)
		}

		for _, item := range gone {
			topic := fmt.Sprintf("%s/%s", pub_topic, item)
			fmt.Printf("Publishing to %s!\n", topic)
			token := client.Publish(topic, 0, false, "0") // qos retained msg
			token.Wait()
		}
		for _, item := range _new {
			topic := fmt.Sprintf("%s/%s", pub_topic, item)
			fmt.Printf("Publishing to %s!\n", topic)
			token := client.Publish(topic, 0, false, "1") // qos retained msg
			token.Wait()
		}
		prevState = present
	}
}
func handleTCPConn(conn net.Conn) {
	defer conn.Close()
	data, err := ioutil.ReadAll(conn)
	if err != nil {
		fmt.Printf("Error reading: %s\n", err)
		return
	}
	strdata := string(data)
	//fmt.Printf("Read %+v\n", strdata)
	tcpData <- strdata
}
func listenTcp() {
	port := fmt.Sprintf(":%s", getEnv("TCP_PORT", "3334"))
	fmt.Printf("Listening on port %s\n", port)
	socket, err := net.Listen("tcp", port)
	if err != nil {
		panic(err)
	}
	for {
		//fmt.Println("Waiting for conn")
		conn, err := socket.Accept()
		if err != nil {
			panic(err)
		}
		//fmt.Println("Accepted something")
		go handleTCPConn(conn)
	}
}

func main() {
	client := setupMqtt()
	defer client.Disconnect(250)
	go dataToMqtt(client)
	listenTcp()
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

func diff(X, Y []string) []string {

	diff := []string{}
	vals := map[string]struct{}{}

	for _, x := range X {
		vals[x] = struct{}{}
	}

	for _, x := range Y {
		if _, ok := vals[x]; !ok {
			diff = append(diff, x)
		}
	}

	return diff
}
