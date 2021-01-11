import time
import bluetooth
import struct

from ble_advertising import decode_services, decode_name

from micropython import const

_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)

_FLAG_NOTIFY = const(0x0010)
ENABLE_NOTIF = const(0x01)

_ADV_IND = const(0x00)
_ADV_DIRECT_IND = const(0x01)

UUID_COMMAND = bluetooth.UUID('99fa0002-338a-1024-8a49-009c0215f78a')
UUID_HEIGHT = bluetooth.UUID('99fa0021-338a-1024-8a49-009c0215f78a')
UUID_CCCD = bluetooth.UUID(0x2902)

COMMAND_UP = struct.pack("<H", 71)
COMMAND_DOWN = struct.pack("<H", 70)
COMMAND_STOP = struct.pack("<H", 255)


class BLESimpleCentral:
    def __init__(self, ble, notify_callback):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._reset()
        self._notify_callback = notify_callback

    def _reset(self):
        self._read_callback = None
        self._ready = False

        self._conn_handle = None
        self._command_handle = None
        self._height_handle = None
        self._found_chars = []
        self._found_notifiers = []

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            # FIXME should be able to get a name..
            pass
        elif event == _IRQ_SCAN_DONE:
            pass
        elif event == _IRQ_PERIPHERAL_CONNECT:
            print("Connected")
            conn_handle, addr_type, addr = data
            if addr_type == self._addr_type and addr == self._addr:
                self._conn_handle = conn_handle
                self._ble.gattc_discover_services(self._conn_handle)
        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            # Disconnect (either initiated by us or the remote end).
            conn_handle, _, _ = data
            if conn_handle == self._conn_handle:
                # If it was initiated by us, it'll already be reset.
                self._reset()

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            # Connected device returned a service.
            conn_handle, start_handle, end_handle, uuid = data
            # print("service", data)
            if conn_handle == self._conn_handle:
                self._found_chars.append((start_handle, end_handle))
                # can't have concurrent scans going or this crashes horribly
        elif event == _IRQ_GATTC_SERVICE_DONE:
            if len(self._found_chars):
                start, end = self._found_chars.pop()
                self._start_handle = start
                self._end_handle = end
                self._ble.gattc_discover_characteristics(self._conn_handle, start, end)
        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            # Connected device returned a characteristic.
            conn_handle, def_handle, value_handle, properties, uuid = data
            if uuid not in [UUID_COMMAND, UUID_HEIGHT]:
                return
            # print("char", uuid, def_handle, value_handle, properties)
            if properties & _FLAG_NOTIFY:
                # print("> Can notify!")
                self._found_notifiers.append((self._start_handle, self._end_handle))

            if uuid == UUID_COMMAND:
                self._command_handle = value_handle
                # print("COMMAND!", value_handle)
            elif uuid == UUID_HEIGHT:
                self._height_handle = value_handle
                # print("HEIGHT!", value_handle)
        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            # print('done with chars')
            if len(self._found_chars):
                start, end = self._found_chars.pop()
                self._start_handle = start
                self._end_handle = end
                self._ble.gattc_discover_characteristics(self._conn_handle, start, end)
            elif len(self._found_notifiers):
                start, end = self._found_notifiers.pop()
                self._ble.gattc_discover_descriptors(self._conn_handle, start, end)

        elif event == _IRQ_GATTC_WRITE_DONE:
            conn_handle, value_handle, status = data
            # print("TX complete")

        elif event == _IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            if value_handle != self._height_handle:
                return
            height, _speed = struct.unpack("<Hh", notify_data)
            self._notify_callback(height)

        elif event == _IRQ_GATTC_READ_RESULT:
            conn_handle, value_handle, char_data = data
            # FIXME
            # print('read result', value_handle, char_data)
            if value_handle == self._height_handle:
                if self._read_callback:
                    height, _speed = struct.unpack("<Hh", char_data)
                    self._read_callback(height)
        elif event == _IRQ_GATTC_DESCRIPTOR_RESULT:
            conn_handle, dsc_handle, uuid = data
            if uuid == UUID_CCCD and conn_handle == self._conn_handle:
                # print(">>> desc result", dsc_handle, uuid)
                self._ble.gattc_write(self._conn_handle, dsc_handle, struct.pack('<h', ENABLE_NOTIF))

        elif event == _IRQ_GATTC_DESCRIPTOR_DONE:
            conn_handle, status = data
            # print("desc DONE", conn_handle, status)
            if len(self._found_notifiers):
                start, end = self._found_notifiers.pop()
                self._ble.gattc_discover_descriptors(self._conn_handle, start, end)
            else:
                self._ready = True
        else:
            print("# Something else", event, data)

    def is_connected(self):
        return self._ready

    def connect(self, addr_type, addr):
        self._addr_type = addr_type
        self._addr = addr
        self._ble.gap_connect(self._addr_type, self._addr)

    # Disconnect from current device.
    def disconnect(self):
        if not self._conn_handle:
            return
        self._ble.gap_disconnect(self._conn_handle)
        self._reset()

    def read_height(self, cb):
        if not self.is_connected():
            return
        self._read_callback = cb
        self._ble.gattc_read(self._conn_handle, self._height_handle)

    def move_up(self):
        self._ble.gattc_write(self._conn_handle, self._command_handle, COMMAND_UP)

    def move_down(self):
        self._ble.gattc_write(self._conn_handle, self._command_handle, COMMAND_DOWN)

    def move_stop(self):
        self._ble.gattc_write(self._conn_handle, self._command_handle, COMMAND_STOP)
