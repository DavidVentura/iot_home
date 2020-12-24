The code in this repo runs inside a [ath79](https://openwrt.org/docs/techref/targets/ath79) based wireless router,
running OpenWrt.

The only behavior here is mapping presence in wifi to MQTT, and it runs inside the router.

The zeroth approach was a PoC in bash which amounted to `while true; do iwinfo wlan0 assoclist | nc <target>; sleep
5; done`. This worked well but required a remote server doing TCP->MQTT.

The first approach was to write this in Go, as it can trivially cross-compile for the mips-el target, but it did not
feel right to have >30% of the entirety of the flash memory used by a single binary.

The second approach was to write this in Rust, which could also target mips-el easily. This worked fine for a
hello-world, but the mqtt library pulled in a lot of dependencies, and some of those would not build for mips.

The third approach was to give up and write it in C, which also worked fine and cross compiled fine, but it was not ABI
compatible, so it crashed on startup. The solution for this was to use the cross-compiler from the SDK:

* [get the sdk](https://downloads.openwrt.org/releases/19.07.5/targets/ath79/generic/openwrt-imagebuilder-19.07.5-ath79-generic.Linux-x86_64.tar.xz)
* [Cross compiling](https://openwrt.org/docs/guide-developer/crosscompile)

build:

```bash
mips-openwrt-linux-gcc -I../include *.c
```

after asking in the `#openwrt-dev` IRC channel they asked me why didn't I write it in lua, as it is supported in
OpenWrt. Duh.

So the fourth and last version is what you see here, written in lua.

```
opkg install hostapd-utils
```

In /etc/rc.local
```
hostapd_cli -a /root/hook.lua  -i wlan0 -B 
```

In /etc/crontabs/root
```
*/2 * * * * /usr/bin/lua /root/timer.lua
```
