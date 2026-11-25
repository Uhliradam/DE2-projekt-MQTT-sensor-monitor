"""
MQTT Sensor Monitor - hlavní program
====================================

Raspberry Pi Pico W + MicroPython

Hardware:
    BME280       teplota, vlhkost, tlak   (I2C, adresa 0x76)
    SH1106 OLED  displej 128x64           (I2C, adresa 0x3C)
    RGB LED      stav připojení           (GPIO, společná katoda)

Tasky (asyncio):
    sensor_task   měří senzor a ukládá hodnoty do sdíleného stavu
    display_task  vykresluje sdílený stav na OLED
    wifi_task     udržuje připojení k Wi-Fi
    mqtt_task     posílá naměřené hodnoty na MQTT broker
    led_task      ukazuje stav připojení na RGB LED

RGB LED:
    zelená             Wi-Fi i MQTT připojené
    červená            Wi-Fi nebo MQTT nedostupné
    blikající žlutá    probíhá připojování k Wi-Fi

MQTT topicy:
    de2/pico01/data     {"t": 24.06, "h": 44.1, "p": 983.42, "a": 254}
    de2/pico01/status   "online" / "offline"  (retained, offline = last will)
"""

from machine import I2C, Pin
import asyncio
import json
import network
import rp2

from umqtt.simple import MQTTClient

from bme280 import BME280
from sh1106 import SH1106_I2C
from wifi_utils import connect_async
from config import SSID, PSWD, MQTT_BROKER


# ==================== Nastavení ====================

# I2C sběrnice (BME280 + OLED)
I2C_SDA = 4
I2C_SCL = 5
I2C_FREQ = 400_000      # 400 kHz (fast mode)

# I2C adresy
BME280_ADDR = 0x76
OLED_ADDR = 0x3C

# RGB LED (společná katoda: 1 = svítí)
LED_R_PIN = 12
LED_G_PIN = 13
LED_B_PIN = 14

# Barvy LED (R, G, B)
LED_OFF = (0, 0, 0)
LED_RED = (1, 0, 0)
LED_GREEN = (0, 1, 0)
LED_YELLOW = (1, 1, 0)

# Wi-Fi
WIFI_COUNTRY = "CZ"     # povolí evropské kanály 12 a 13

# MQTT
MQTT_CLIENT_ID = "pico01"
MQTT_TOPIC_DATA = b"de2/pico01/data"
MQTT_TOPIC_STATUS = b"de2/pico01/status"
MQTT_KEEPALIVE_S = 30   # broker pozná výpadek Pica do 1,5 × 30 s
MQTT_TIMEOUT_S = 3      # max. čekání na síť, aby se nezasekly ostatní tasky

# Intervaly tasků [s]
SENSOR_INTERVAL_S = 2
DISPLAY_INTERVAL_S = 1
WIFI_INTERVAL_S = 5
MQTT_INTERVAL_S = 5
MQTT_WAIT_WIFI_S = 1    # jak často MQTT kontroluje, jestli už je Wi-Fi
LED_INTERVAL_S = 0.5    # zároveň rychlost blikání


# ==================== Inicializace ====================

def init_i2c():
    """Vytvoří I2C sběrnici a vrátí ji spolu se seznamem nalezených adres."""
    i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=I2C_FREQ)
    devices = i2c.scan()
    print("I2C zarizeni:", [hex(d) for d in devices])
    return i2c, devices


def check_devices(devices):
    """Vypíše, které z očekávaných I2C modulů na sběrnici chybí."""
    for name, addr in (("BME280", BME280_ADDR), ("OLED", OLED_ADDR)):
        if addr not in devices:
            print(f"{name} nenalezen na adrese {hex(addr)}!")


def init_bme280(i2c):
    """Vrátí objekt senzoru, nebo None, pokud senzor neodpovídá."""
    try:
        return BME280(i2c=i2c, addr=BME280_ADDR)
    except OSError as e:
        print("BME280 init selhal:", e)
        return None


def init_oled(i2c):
    """Vrátí objekt displeje, nebo None, pokud displej neodpovídá."""
    try:
        return SH1106_I2C(i2c)
    except OSError as e:
        print("OLED init selhal:", e)
        return None


def init_wifi():
    """Zapne Wi-Fi v režimu klienta (připojuje se k routeru)."""
    rp2.country(WIFI_COUNTRY)
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    return wifi


def init_led():
    """Vrátí piny RGB LED (R, G, B), všechny zhasnuté."""
    return (
        Pin(LED_R_PIN, Pin.OUT, value=0),
        Pin(LED_G_PIN, Pin.OUT, value=0),
        Pin(LED_B_PIN, Pin.OUT, value=0),
    )


# ==================== Senzor ====================

def read_sensor(bme):
    """Vrátí (teplota, vlhkost, tlak, výška), nebo None při chybě."""
    if bme is None:
        return None
    try:
        t, h, p, a = bme.read_values()
        return t, h, p, a
    except OSError as e:
        print("Chyba cteni senzoru:", e)
        return None


# ==================== Displej ====================

def draw_display(oled, state):
    """Vykreslí naměřené hodnoty a stav Wi-Fi / MQTT na OLED."""
    if oled is None:
        return

    oled.fill(0)
    oled.text("Sensor monitor", 0, 0)
    oled.hline(0, 10, 128, 1)

    # Naměřené hodnoty
    if state.values is None:
        oled.text("Sensor error!", 0, 28)
    else:
        t, h, p, a = state.values
        oled.text(f"T: {t:6.1f} C", 0, 14)
        oled.text(f"H: {h:6.1f} %", 0, 24)
        oled.text(f"P: {p:6.1f} hPa", 0, 34)
        oled.text(f"A: {a:6.0f} m", 0, 44)

    # Stavový řádek
    if state.wifi_ok:
        wifi_text = "OK"
    elif state.wifi_connecting:
        wifi_text = ".."
    else:
        wifi_text = "--"
    mqtt_text = "OK" if state.mqtt_ok else "--"
    oled.text(f"WiFi:{wifi_text} MQTT:{mqtt_text}", 0, 56)

    oled.show()


# ==================== RGB LED ====================

def set_led(led, color):
    """Rozsvítí LED danou barvou, např. set_led(led, LED_GREEN)."""
    for pin, value in zip(led, color):
        pin.value(value)


def led_color(state, blink_on):
    """Vybere barvu LED podle stavu připojení."""
    if state.wifi_connecting:
        return LED_YELLOW if blink_on else LED_OFF     # bliká = připojuje se
    if state.wifi_ok and state.mqtt_ok:
        return LED_GREEN                               # vše připojeno
    return LED_RED                                     # Wi-Fi nebo MQTT nejede


# ==================== MQTT ====================

def mqtt_connect():
    """Připojí se k brokeru a ohlásí stav 'online'."""
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, keepalive=MQTT_KEEPALIVE_S)
    client.set_last_will(MQTT_TOPIC_STATUS, b"offline", retain=True)
    client.connect(timeout=MQTT_TIMEOUT_S)
    client.publish(MQTT_TOPIC_STATUS, b"online", retain=True)
    return client


def mqtt_close(client):
    """Zavře spojení bez odhlášení - broker pak sám rozešle 'offline'."""
    try:
        client.sock.close()
    except Exception:
        pass


def make_payload(values):
    """Převede (t, h, p, a) na JSON text pro MQTT."""
    t, h, p, a = values
    return json.dumps({
        "t": round(t, 2),
        "h": round(h, 2),
        "p": round(p, 2),
        "a": round(a),
    })


# ==================== Sdílený stav ====================

class State:
    """Data sdílená mezi tasky. Tasky do něj zapisují a čtou z něj."""

    def __init__(self):
        self.values = None            # (t, h, p, a), nebo None při chybě senzoru
        self.wifi_ok = False          # připojeno k Wi-Fi
        self.wifi_connecting = False  # právě probíhá připojování
        self.mqtt_ok = False          # připojeno k MQTT brokeru


# ==================== Tasky ====================

async def sensor_task(bme, state):
    """Každých SENSOR_INTERVAL_S sekund změří senzor a uloží hodnoty."""
    while True:
        state.values = read_sensor(bme)
        if state.values is not None:
            t, h, p, a = state.values
            print(f"T={t:.1f} C  H={h:.1f} %  P={p:.1f} hPa  A={a:.0f} m")
        await asyncio.sleep(SENSOR_INTERVAL_S)


async def display_task(oled, state):
    """Každých DISPLAY_INTERVAL_S sekund překreslí displej."""
    while True:
        try:
            draw_display(oled, state)
        except OSError as e:
            print("Chyba displeje:", e)
        await asyncio.sleep(DISPLAY_INTERVAL_S)


async def wifi_task(wifi, state):
    """Každých WIFI_INTERVAL_S sekund zkontroluje Wi-Fi a případně se připojí."""
    while True:
        if wifi.isconnected():
            state.wifi_ok = True
        else:
            state.wifi_ok = False
            state.wifi_connecting = True
            if await connect_async(wifi, SSID, PSWD):
                state.wifi_ok = True
                print("IP adresa:", wifi.ifconfig()[0])
            state.wifi_connecting = False
        await asyncio.sleep(WIFI_INTERVAL_S)


async def mqtt_task(state):
    """Každých MQTT_INTERVAL_S sekund odešle naměřené hodnoty na broker."""
    client = None
    while True:
        if not state.wifi_ok:
            # Bez Wi-Fi nemá smysl se připojovat
            if client is not None:
                mqtt_close(client)
                client = None
            state.mqtt_ok = False
            await asyncio.sleep(MQTT_WAIT_WIFI_S)   # brzy zkusit znovu
            continue

        try:
            if client is None:
                client = mqtt_connect()
                state.mqtt_ok = True
                print("MQTT: pripojeno k", MQTT_BROKER)

            if state.values is not None:
                client.publish(MQTT_TOPIC_DATA, make_payload(state.values))
            else:
                client.ping()       # nic k odeslání, jen udržet spojení
        except OSError as e:
            print("MQTT chyba:", e)
            if client is not None:
                mqtt_close(client)
            client = None           # příště se připojí znovu
            state.mqtt_ok = False
        await asyncio.sleep(MQTT_INTERVAL_S)


async def led_task(led, state):
    """Každých LED_INTERVAL_S sekund nastaví barvu LED podle stavu připojení."""
    blink_on = False
    while True:
        blink_on = not blink_on     # střídá zapnuto/vypnuto = blikání
        set_led(led, led_color(state, blink_on))
        await asyncio.sleep(LED_INTERVAL_S)


# ==================== Hlavní program ====================

async def main():
    led = init_led()
    i2c, devices = init_i2c()
    check_devices(devices)

    bme = init_bme280(i2c)
    oled = init_oled(i2c)
    wifi = init_wifi()
    state = State()

    await asyncio.gather(
        sensor_task(bme, state),
        display_task(oled, state),
        wifi_task(wifi, state),
        mqtt_task(state),
        led_task(led, state),
    )


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program zastaven")
finally:
    set_led(init_led(), LED_OFF)    # po ukončení LED zhasnout
    asyncio.new_event_loop()        # vyčistí asyncio, aby šel program znovu spustit
