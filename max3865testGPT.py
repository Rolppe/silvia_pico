# MicroPython (Raspberry Pi Pico W)
from machine import Pin, SPI
import time

# --- SPI & pin config (muokkaa tarpeen mukaan) ---
SPI_ID = 1
SCK = 10
MOSI = 11
MISO = 12
CS_PIN = 13

THREE_WIRE = True   # aseta False jos 2- tai 4-johtoinen PT100
FILTER_50HZ = True  # True=50 Hz, False=60 Hz

# MAX31865 rekisterit
REG_CONFIG   = 0x00
REG_RTD_MSB  = 0x01
REG_RTD_LSB  = 0x02
REG_HFT_MSB  = 0x03
REG_HFT_LSB  = 0x04
REG_LFT_MSB  = 0x05
REG_LFT_LSB  = 0x06
REG_FAULT    = 0x07

# Config-bittien apu
CFG_VBIAS    = 0x80
CFG_MODEAUTO = 0x40
CFG_1SHOT    = 0x20
CFG_3WIRE    = 0x10
# Fault-detektion ohjausbitit D3..D2 jätetään 00 (ei suoriteta sykliä nyt)
CFG_FAULTCLR = 0x02
CFG_FILTER50 = 0x01  # 1=50 Hz, 0=60 Hz

# Fault bit masks
FLT_HIGHTH   = 0x80
FLT_LOWTH    = 0x40
FLT_REFINH   = 0x20
FLT_REFINL   = 0x10
FLT_RTDINL   = 0x08
FLT_OV_UV    = 0x04

cs = Pin(CS_PIN, Pin.OUT, value=1)  # Pidä CS ylhäällä jo alussa
spi = SPI(SPI_ID, baudrate=1_000_000, polarity=0, phase=1, sck=Pin(SCK), mosi=Pin(MOSI), miso=Pin(MISO))

def write_reg(addr, val):
    # Write: MSB=0, auto-increment kun kirjoitetaan useampi, mutta tässä yksittäinen
    cs.value(0)
    spi.write(bytes([addr & 0x7F, val & 0xFF]))
    cs.value(1)

def read_regs(addr, nbytes=1):
    # Read: aseta MSB=1
    cs.value(0)
    spi.write(bytes([0x80 | (addr & 0x7F)]))
    data = spi.read(nbytes)
    cs.value(1)
    return data

def config_set(vbias=True, auto=True, three_wire=THREE_WIRE, filter50=FILTER_50HZ, fault_clear=False):
    cfg = 0
    if vbias:     cfg |= CFG_VBIAS
    if auto:      cfg |= CFG_MODEAUTO
    if three_wire:cfg |= CFG_3WIRE
    if filter50:  cfg |= CFG_FILTER50
    if fault_clear: cfg |= CFG_FAULTCLR
    write_reg(REG_CONFIG, cfg)
    return cfg

def fault_clear_once():
    # Kirjoita sama konfigi + FAULTCLR bitti hetkeksi
    current = read_regs(REG_CONFIG, 1)[0]
    write_reg(REG_CONFIG, current | CFG_FAULTCLR)
    # datasheetin mukaan riittää yksi kirjoitus; luetaan takaisin varmistukseksi
    time.sleep_ms(2)
    return read_regs(REG_FAULT, 1)[0]

def read_all():
    regs = {}
    regs['config'] = read_regs(REG_CONFIG, 1)[0]
    rtd_msb = read_regs(REG_RTD_MSB, 1)[0]
    rtd_lsb = read_regs(REG_RTD_LSB, 1)[0]
    regs['rtd_raw'] = ((rtd_msb << 8) | rtd_lsb) >> 1  # D15..D1 validit, D0 fault-bitin peili
    regs['fault']  = read_regs(REG_FAULT, 1)[0]
    regs['hft']    = (read_regs(REG_HFT_MSB,1)[0] << 8) | read_regs(REG_HFT_LSB,1)[0]
    regs['lft']    = (read_regs(REG_LFT_MSB,1)[0] << 8) | read_regs(REG_LFT_LSB,1)[0]
    return regs

def decode_fault(f):
    msgs = []
    if f & FLT_HIGHTH: msgs.append("RTD yli High-rajan (mahd. avoin johdin tai liian suuri R)")
    if f & FLT_LOWTH:  msgs.append("RTD alle Low-rajan (mahd. oikosulku/maahan)")
    if f & FLT_REFINH: msgs.append("REFIN- epänormaali (korkea) → Rref/REFIN johdotus?")
    if f & FLT_REFINL: msgs.append("REFIN- epänormaali (matala) → Rref/REFIN johdotus?")
    if f & FLT_RTDINL: msgs.append("RTDIN- epänormaali (matala) → RTD-linja/3-wire kytkentä?")
    if f & FLT_OV_UV:  msgs.append("Yli-/alijännite fault (syöttö/EMI/VDD?)")
    if not msgs:
        msgs = ["Ei faultteja."]
    return msgs

# --- Testisekvenssi: käynnistysdiag ---
print("Alustetaan: VBIAS päälle, autoconvert, {}-wire, {} Hz suodatin"
      .format(3 if THREE_WIRE else 2, 50 if FILTER_50HZ else 60))

cfg = config_set(vbias=True, auto=True, three_wire=THREE_WIRE, filter50=FILTER_50HZ, fault_clear=False)
time.sleep_ms(50)  # anna biasin asettua

f_before = read_regs(REG_FAULT, 1)[0]
print("Fault ennen clear: 0x{:02X} -> {}".format(f_before, "; ".join(decode_fault(f_before))))

f_after = fault_clear_once()
print("Fault clearin jälkeen: 0x{:02X} -> {}".format(f_after, "; ".join(decode_fault(f_after))))

regs = read_all()
print("CONFIG=0x{:02X}, RTD_raw=0x{:04X} ({})".format(regs['config'], regs['rtd_raw'], regs['rtd_raw']))
print("FAULT=0x{:02X} -> {}".format(regs['fault'], "; ".join(decode_fault(regs['fault']))))
