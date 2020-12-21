#!/usr/bin/lua

mqtt = require("mosquitto")

known = {}
known["F4:60:E2:B4:68:C4"] = "David"
known["A4:50:46:5B:FD:E1"] = "Tati"

if arg[2] == "AP-STA-CONNECTED" then
	present = 1
else
	present = 0
end
mac = arg[3]:upper()

client = mqtt.new()
client.ON_CONNECT = function()
	local qos = 1
	local retain = false
	who = known[mac]
	client:publish("PRESENCE/" .. who, tonumber(present), qos, retain)
	print("Publishing..")
end

client.ON_PUBLISH = function()
	print("Sent!")
	os.exit()
end

if known[mac] ~= nil then
	print("Found " .. known[mac] .. " in state " .. tonumber(present))
	client:connect("iot.labs")
	client:loop_forever()
else
	print("Unknown mac " .. mac)
end
