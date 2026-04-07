import bluetooth
from micropython import const
import json
import asyncio

# ============================================================================
# CONSTANTS
# ============================================================================
_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x03)
_ADV_TYPE_APPEARANCE = const(0x19)

_CENTRAL_UUID = bluetooth.UUID('0000180a-0000-1000-8000-00805f9b34fb')
_DATA_CHAR_UUID = bluetooth.UUID('00002a29-0000-1000-8000-00805f9b34fb')
_COMMAND_CHAR_UUID = bluetooth.UUID('00002a2a-0000-1000-8000-00805f9b34fb')


class BLEHandler:
    def __init__(self, ble, brew_data):
        self.brew_data = brew_data
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)

        # GATT-palvelut
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((
            (_CENTRAL_UUID, (
                (_DATA_CHAR_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY),
                (_COMMAND_CHAR_UUID, bluetooth.FLAG_WRITE),
            )),
        ))

        self._connections = set()
        self._payload = BLEHandler._advertising_payload(
            name='EspressoPico',
            services=[_CENTRAL_UUID]
        )

        self._advertise_pending = True
        self._advertise()


    # ====================== ASETUSTEN LÄHETTÄMINEN ======================
    async def send_settings(self):
        """Lähettää vain asetukset (kutsutaan yhteyden muodostuessa ja asetuksen muutoksessa)"""
        if not self._connections:
            return

        data = {
            'pre_infusion_mode': self.brew_data.get_pre_infusion_mode(),
            'pressure_soft_release_mode': self.brew_data.get_pressure_soft_release_mode(),
            'fast_heatup_mode': self.brew_data.get_fast_heatup_mode(),
            'brew_temperature': self.brew_data.get_brew_temperature()
        }

        json_data = json.dumps(data)
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, json_data)


# ====================== REAALIAIKAISTEN TIETOJEN LÄHETTÄMINEN ======================

    async def send_data(self):
        """Lähettää jatkuvasti reaaliaikaiset mittaustiedot"""
        if not self._connections:
            return

        data = {
            'boiler_temperature': self.brew_data.get_boiler_temperature(),
            'pressure': self.brew_data.get_pressure(),
            'mode': self.brew_data.get_mode(),
            'pump_ratio': 0   # voit lisätä myöhemmin jos tarvitset
        }

        json_data = json.dumps(data)
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, json_data)

    # ====================== IRQ (komentojen käsittely) ======================
    def _irq(self, event, data):
        if event == 1:      # Connected
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            print("Connected - sending initial settings")
            asyncio.create_task(self.send_settings())   # asetukset heti yhteydessä

        elif event == 2:    # Disconnected
            conn_handle, _, _ = data
            self._connections.discard(conn_handle)
            self._advertise_pending = True

        elif event == 3:    # Write (komento)
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            command = value.decode('utf-8').strip()

            print(f"Received: '{command}'")

            updated = False

            if command.startswith('pre:'):
                if command == 'pre:on':
                    self.brew_data.set_pre_infusion_mode(True)
                    updated = True
                elif command == 'pre:off':
                    self.brew_data.set_pre_infusion_mode(False)
                    updated = True

            elif command.startswith('spr:'):
                if command == 'spr:on':
                    self.brew_data.set_pressure_soft_release_time(5)
                    self.brew_data.set_pressure_soft_release_mode(True)
                    updated = True
                elif command == 'spr:off':
                    self.brew_data.set_pressure_soft_release_time(0)
                    self.brew_data.set_pressure_soft_release_mode(False)
                    updated = True

            elif command.startswith('fhu:'):
                if command == 'fhu:on':
                    self.brew_data.set_fast_heatup_mode(True)
                    updated = True
                elif command == 'fhu:off':
                    self.brew_data.set_fast_heatup_mode(False)
                    updated = True

            elif command.startswith('bt:'):
                try:
                    temp = float(command.split(':', 1)[1])
                    self.brew_data.set_brew_temperature(temp)
                    updated = True
                except:
                    pass

            if updated:
                asyncio.create_task(self.send_settings())   # asetukset heti muutoksen jälkeen


    def advertise_if_needed(self):
        if self._advertise_pending:
            self._advertise_pending = False
            self._advertise()

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(None)
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    # ====================== DATAN LÄHETTÄMINEN ======================
    async def send_data(self):
        """Lähettää reaaliaikaisen datan kaikille yhteyksissä oleville laitteille"""
        if not self._connections:
            return

        pressure                   = self.brew_data.get_pressure()
        boiler_temperature         = self.brew_data.get_boiler_temperature()
        mode                       = self.brew_data.get_mode()
        brew_temperature           = self.brew_data.get_brew_temperature()
        pre_infusion_mode          = self.brew_data.get_pre_infusion_mode()
        pressure_soft_release_mode = self.brew_data.get_pressure_soft_release_mode()
        fast_heatup_mode           = self.brew_data.get_fast_heatup_mode()
        pump_ratio                 = self.brew_data.get_pump_ratio()
        
        data = {
            'boiler_temperature'         : boiler_temperature,
            'pressure'                   : pressure,
            'mode'                       : mode,
            'brew_temperature'           : brew_temperature,
            'pre_infusion_mode'          : pre_infusion_mode,                  
            'pressure_soft_release_mode' : pressure_soft_release_mode,
            'fast_heatup_mode'           : fast_heatup_mode,
            'pump_ratio'                 : pump_ratio
        }

        json_data = json.dumps(data)
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, json_data)

    def run_transmission(self):
        asyncio.create_task(self.send_data())


    @staticmethod
    def _advertising_payload(limited_disc=False, br_edr=False, name=None, services=None, appearance=0):
        payload = bytearray()
        def _append(adv_type, value):
            nonlocal payload
            payload += bytearray([len(value) + 1, adv_type]) + value

        _append(_ADV_TYPE_FLAGS, bytearray([(0x01 if limited_disc else 0x02) + (0x18 if br_edr else 0x04)]))
        if name:
            _append(_ADV_TYPE_NAME, name.encode())
        if services:
            for uuid in services:
                b = bytes(uuid)
                if len(b) == 2:
                    _append(_ADV_TYPE_UUID16_COMPLETE, b)
        if appearance:
            _append(_ADV_TYPE_APPEARANCE, bytearray([appearance & 0xFF, appearance >> 8]))
        return payload