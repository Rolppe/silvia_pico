# Tuodaan tarvittavat moduulit:
import bluetooth  # Bluetooth-toiminnot MicroPythonissa (sisäänrakennettu Pico W:lle).
from micropython import const  # Määrittelee vakioita muistitehokkuuden vuoksi.
import time  # Aikaviiveet, esim. datan lähetysväli.
import json  # Datan muuntaminen JSON-muotoon lähetystä varten.
import machine  # Laitteiston hallinta, esim. pinnit ja LED.
import random  # Satunnaisluvut lämpötilan simulaatioon (korvaa oikealla anturilla tuotannossa).


# BLE-mainoskonstantit: Nämä ovat standardiarvoja BLE-mainokselle (advertising).
# Ne määrittävät, miten laite ilmoittaa itsestään muille laitteille.
_ADV_TYPE_FLAGS = const(0x01)  # Liput, esim. yleinen löydettävyys.
_ADV_TYPE_NAME = const(0x09)  # Laitteen nimi mainoksessa.
_ADV_TYPE_UUID16_COMPLETE = const(0x3)  # Täydellinen 16-bittinen UUID-lista.
_ADV_TYPE_APPEARANCE = const(0x19)  # Laitteen ulkonäkö (esim. kategoria, kuten anturi).

# GATT-palvelun ja ominaisuuksien UUID:t: Nämä ovat ainutlaatuisia tunnisteita BLE-palveluille ja ominaisuuksille.
# Käytetään standardeja UUID:iä testiin; tuotannossa käytä uniikkeja.
_CENTRAL_UUID = bluetooth.UUID('0000180a-0000-1000-8000-00805f9b34fb')  # Palvelun UUID (esim. Device Information Service).
_DATA_CHAR_UUID = bluetooth.UUID('00002a29-0000-1000-8000-00805f9b34fb')  # Data-ominaisuus (notify ja read).
_COMMAND_CHAR_UUID = bluetooth.UUID('00002a2a-0000-1000-8000-00805f9b34fb')  # Komento-ominaisuus (write).


# Pääluokka BLECoffee: Hoitaa kaikki BLE-toiminnot.
class BLECoffee:
    def __init__(self, ble):
        # Tulostetaan debug-tietoa alustuksesta.
        print("Alustetaan BLE...")
        self._ble = ble  # Tallennetaan Bluetooth-objekti.
        self._ble.active(True)  # Aktivoidaan BLE-moduuli; ilman tätä laite ei ole käytettävissä.
        print("BLE aktivoitu")
        self._ble.irq(self._irq)  # Asetetaan IRQ-käsittelijä (interrupt request): Tämä kutsutaan, kun BLE-tapahtuma tapahtuu (esim. yhteys).
        # Rekisteröidään GATT-palvelut: Tämä määrittää, mitä ominaisuuksia laite tarjoaa.
        # _handle_tx ja _handle_rx ovat kahvat notify- ja write-ominaisuuksille.
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((
            (_CENTRAL_UUID,
             (
                 (_DATA_CHAR_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,),  # Read ja notify: Client voi lukea ja tilata päivityksiä.
                 (_COMMAND_CHAR_UUID, bluetooth.FLAG_WRITE,),  # Write: Client voi lähettää komentoja.
             ),
            ),
        ))
        print("Palvelut rekisteröity")
        self._connections = set()  # Seuraa aktiivisia yhteyksiä (conn_handle:t).
        # Luo mainospaketti: Sisältää nimen, palvelut jne., jota käytetään laitteen ilmoittamiseen.
        self._payload = self._advertising_payload(name='EspressoPico', services=[_CENTRAL_UUID])
        self._advertise()  # Aloitetaan mainostus.
        self.temp = 92.0  # Alkuarvo lämpötilalle (päivitetään myöhemmin).

    # IRQ-käsittelijä: Kutsutaan automaattisesti BLE-tapahtumissa. Tämä on BLE:n "event handler".
    def _irq(self, event, data):
        print("IRQ event:", event, "data:", data)  # Debug: Näyttää kaikki tapahtumat.
        if event == 1:  # Yhdistetty: Client (esim. app) on muodostanut yhteyden.
            print("Yhteys muodostettu:", data)
            led.value(1)  # LED päälle osoittamaan yhteyttä.
            conn_handle, _, _ = data  # Puretaan data: conn_handle on yhteyden tunniste.
            self._connections.add(conn_handle)  # Lisätään yhteyteen.
        elif event == 2:  # Katkaistu: Yhteys menetetty.
            print("Yhteys katkaistu:", data)
            led.value(0)  # LED pois.
            conn_handle, _, _ = data
            self._connections.remove(conn_handle)  # Poistetaan yhteys.
            self._advertise()  # Aloitetaan mainostus uudelleen löydettävyyden vuoksi.
        elif event == 3:  # Kirjoitus: Client on kirjoittanut ominaisuuteen (esim. komento).
            print("Kirjoitus vastaanotettu:", data)
            conn_handle, value_handle = data  # Puretaan: value_handle on kirjoitetun ominaisuuden kahva.
            value = self._ble.gatts_read(value_handle)  # Luetaan kirjoitettu arvo.
            command = value.decode('utf-8').strip()  # Muunnetaan tekstiin.
            print("Komento:", command)  # Debug: Näyttää komennon (esim. 'start_brew').
        else:
            print("Tuntematon IRQ-tapahtuma:", event, data)  # Muut tapahtumat (esim. MTU-vaihto).

    # Lähettää dataa clientille: Muuntaa dict JSON:ksi ja ilmoittaa (notify) yhteyksille.
    def send_data(self, data):
        json_data = json.dumps(data)  # Muunnetaan JSON-merkkijonoksi.
        print("Lähetetään data:", json_data)  # Debug.
        for conn_handle in self._connections:  # Lähetetään jokaiselle yhteydelle.
            self._ble.gatts_notify(conn_handle, self._handle_tx, json_data)  # Notify: Lähettää datan ilman pyyntöä.

    # Päivittää lämpötilan: Tässä simulaatio; korvaa anturiluvulla (esim. ADC tai TSIC).
    def update_temp(self):
        self.temp = 92 + random.uniform(-1, 1)  # Simuloi vaihtelua.

    # Aloittaa mainostuksen: Ilmoittaa laitteen saatavuudesta muille laitteille.
    def _advertise(self, interval_us=500000):
        print("Mainostus aloitettu")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)  # GAP-advertise: Lähettää paketin interval_us mikrosekunnein välein.

    # Staattinen metodi mainospaketin luomiseen: Rakentaa bytearrayn standardien mukaan.
    @staticmethod
    def _advertising_payload(limited_disc=False, br_edr=False, name=None, services=None, appearance=0):
        payload = bytearray()  # Aloitetaan tyhjästä.
        def _append(adv_type, value):
            nonlocal payload
            payload += bytearray([len(value) + 1, adv_type]) + value  # Lisätään tyyppi ja data.
        _append(_ADV_TYPE_FLAGS, bytearray([0x06 if limited_disc else 0x02, 0x00]))  # Liput: Löydettävyys.
        if name:
            _append(_ADV_TYPE_NAME, name.encode())  # Lisätään nimi UTF-8:na.
        if services:
            for uuid in services:
                b = bytes(uuid)
                if len(b) == 2:
                    _append(_ADV_TYPE_UUID16_COMPLETE, b)  # Lisätään palvelu-UUID:t.
        if appearance:
            _append(_ADV_TYPE_APPEARANCE, bytearray([appearance & 0xFF, appearance >> 8]))  # Ulkonäkö (esim. anturi).
        return payload

# Käynnistetään BLE ja luokka.
ble = bluetooth.BLE()  # Luo BLE-objekti.
coffee = BLECoffee(ble)  # Luo instanssi.

# Pääsilmukka: Päivittää ja lähettää lämpötilan 1 sekunnin välein (reaaliaikainen data).
while True:
    coffee.update_temp()  # Päivitä arvo.
    data = {'temp': coffee.temp}  # Luo data-dict.
    coffee.send_data(data)  # Lähetä.
    time.sleep(1)  # Odota sekunti