import bluetooth
import time

from ble_simple_central import BLESimpleCentral


MIN_HEIGHT = 652
MAX_HEIGHT = 1270
ERR_MARGIN = 2

class Desk:
    def __init__(self, macaddr):
        ble = bluetooth.BLE()
        self.bt = BLESimpleCentral(ble, self._move_to_target)
        self.bt.connect(1, macaddr)
        self._height_target = None
        while not self.bt.is_connected():
            time.sleep_ms(100)

    def read_height(self, cb):
        _cb = lambda height: cb((height / 10) + 620)
        self.bt.read_height(_cb)

    def move_to(self, target):
        target = min(target, MAX_HEIGHT)
        target = max(target, MIN_HEIGHT)
        self._height_target = target
        self.bt.read_height(self._move_to_target)

    def _move_to_target(self, raw_value):
        if not self.bt.is_connected():
            return
        if not self._height_target:
            return
        current_height = (raw_value / 10) + 620

        if abs(current_height - self._height_target) <= ERR_MARGIN:
            print('Close enough, stopping')
            self.bt.move_stop()
            self._height_target = None
            return

        if current_height > self._height_target:
            self.bt.move_down()

        if current_height < self._height_target:
            self.bt.move_up()
