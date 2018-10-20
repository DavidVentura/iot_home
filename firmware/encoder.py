# -*- coding: utf-8 -*-
# Code based on stuff from
# https://github.com/SpotlightKid/micropython-stm-lib/tree/master/encoder
# Modifications are:
# * add callback on value change
#   * debounced on 50ms 
#   * the calls are only triggered on value change

"""MicroPython rotary encoder library.

Usage:

    from time import sleep_ms
    from encoder import Encoder

    # Connect CLK to D6, DT to D5, GND to GND and + to 3V3
    enc = Encoder(pin_clk=12, pin_dt=14)

    def readloop(e):
        oldval = 0
        while True:
            val = enc.value
            if oldval != val:
                print(val)
                oldval = val
            sleep_ms(50)

    readloop(e)
"""

from machine import Pin
import micropython
import utime


ENC_STATES = (
    0,   # 00 00
    -1,  # 00 01
    1,   # 00 10
    0,   # 00 11
    1,   # 01 00
    0,   # 01 01
    0,   # 01 10
    -1,  # 01 11
    -1,  # 10 00
    0,   # 10 01
    0,   # 10 10
    1,   # 10 11
    0,   # 11 00
    1,   # 11 01
    -1,  # 11 10
    0    # 11 11
)
ACCEL_THRESHOLD = const(5)


class Encoder(object):
    def __init__(self, pin_clk, pin_dt, pin_mode=None, clicks=1,
                 min_val=0, max_val=100, accel=0, reverse=False, callback=None):
        self.pin_clk = (pin_clk if isinstance(pin_clk, Pin) else
                        Pin(pin_clk, Pin.IN, pin_mode))
        self.pin_dt = (pin_dt if isinstance(pin_dt, Pin) else
                       Pin(pin_dt, Pin.IN, pin_mode))

        self.min_val = min_val * clicks
        self.max_val = max_val * clicks
        self.accel = int((max_val - min_val) / 100 * accel)
        self.max_accel = int((max_val - min_val) / 2)
        self.clicks = clicks
        self.reverse = 1 if reverse else -1
        self.callback = callback

        # The following variables are assigned to in the interrupt callback,
        # so we have to allocate them here.
        self._value = 0
        self._readings = 0
        self._state = 0
        self.cur_accel = 0
        self._last_callback = 0
        self._last_value = 0

        if self.callback:
            self.callback(self._value)
        self.set_callbacks(self._callback)

    def _callback(self, line):
        self._readings = (self._readings << 2 | self.pin_clk.value() << 1 |
                          self.pin_dt.value()) & 0x0f

        self._state = ENC_STATES[self._readings] * self.reverse

        if self._state:
            self.cur_accel = min(self.max_accel, self.cur_accel + self.accel)

            self._value = min(self.max_val, max(self.min_val, self._value +
                              (1 + (self.cur_accel >> ACCEL_THRESHOLD)) *
                              self._state))
            now = utime.ticks_ms()
            if self.callback and self._last_value != self._value and \
               utime.ticks_diff(now, self._last_callback) > 50:
                try:
                    micropython.schedule(self.callback, self._value)
                    self._last_value = self._value
                    self._last_callback = now
                except:
                    # calling schedule() too ofter might fail; in that case we 
                    # can call on the next value change
                    pass

    def set_callbacks(self, callback=None):
        mode = Pin.IRQ_RISING | Pin.IRQ_FALLING
        self.irq_clk = self.pin_clk.irq(trigger=mode, handler=callback)
        self.irq_dt = self.pin_dt.irq(trigger=mode, handler=callback)

    def close(self):
        self.set_callbacks(None)
        self.irq_clk = self.irq_dt = None

    @property
    def value(self):
        return self._value // self.clicks

    def reset(self):
        self._value = 0
