#!/usr/bin/lua

mqtt = require("mosquitto")

known = {}
known["F4:60:E2:B4:68:C4"] = "david"
known["A4:50:46:5B:FD:E1"] = "tati"

pending_mIDs = {}
pending_items = true

client = mqtt.new()
client.ON_CONNECT = function()
	local qos = 1
	local retain = false
	local found = find_pairs()
	
	state = {}
	for mac, _ in pairs(known) do
		state[mac] = 0
	end

	for idx, mac in pairs(found) do
		state[mac] = 1
	end

	for mac, present in pairs(state) do
		who = known[mac]
		mid = client:publish("phones/" .. who .. "/state", tonumber(present), qos, retain)
		pending_mIDs[mid] = 1
		print("Published.. msg ID: " .. mid)
	end
	pending_items = false
end

client.ON_PUBLISH = function(mid)
	print("Sent! msg ID: " .. mid)
	pending_mIDs[mid] = nil
end

function find_pairs()
	p = {}
	f = io.popen('iwinfo wlan0 assoclist')
	for line in f:lines() do
		mac = string.match(line, '^[A-F0-9:]+')
		if mac ~= nil then
			if known[mac] ~= nil then
				table.insert(p, mac)
			end
		end
	end
	return p
end

function table.empty (self)
	for _, v in pairs(self) do
		if v ~= nil then
			return false
		end
	end
	return true
end

client:connect("iot.labs")
while true do
	client:loop(1000)
	if table.empty(pending_mIDs) and not pending_items then
		os.exit()
	end
end
