"""
MQTT Sensor Monitor - hlavní program
====================================

Raspberry Pi Pico W + MicroPython

Hardware:
    BME280       teplota, vlhkost, tlak   (I2C, adresa 0x76)
    SH1106 OLED  displej 128x64           (I2C, adresa 0x3C)
    MQ-9         CO a hořlavé plyny (LPG, metan) - analogový výstup A0 na GP26
    RGB LED      stav připojení           (GPIO, společná katoda)
    Tlačítko     přepínání obrazovek      (GP15 proti GND, vnitřní pull-up)

Tasky (asyncio):
    sensor_task   měří senzory a ukládá hodnoty do sdíleného stavu
    display_task  vykresluje vybranou obrazovku na OLED
    wifi_task     udržuje připojení k Wi-Fi
    mqtt_task     posílá naměřené hodnoty na MQTT broker
    led_task      ukazuje stav připojení na RGB LED
    button_task   tlačítkem přepíná obrazovky
    time_task     nastaví hodiny Pica přes NTP (pro fázi Měsíce)

Obrazovky (přepínají se tlačítkem):
    senzor   naměřené hodnoty + stav Wi-Fi / MQTT
    Měsíc    aktuální fáze Měsíce (jen obrázek, počítá se v Picu)

RGB LED:
    zelená             Wi-Fi i MQTT připojené
    červená            Wi-Fi nebo MQTT nedostupné
    blikající žlutá    probíhá připojování k Wi-Fi

MQTT topicy:
    de2/pico01/data     {"t": 24.06, "h": 44.1, "p": 983.42, "a": 254, "g": 0.85}
    de2/pico01/status   "online" / "offline"  (retained, offline = last will)
"""

from machine import ADC, I2C, Pin
import asyncio
import json
import math
import network
import ntptime
import rp2
import time

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

# Senzor plynu MQ-9 (napájení 5 V, výstup A0 přes dělič na ADC)
GAS_ADC_PIN = 26        # GP26 = ADC0, pin 31
GAS_DIVIDER = 2         # dělič ze dvou stejných rezistorů dělí napětí 2×

# RGB LED (společná katoda: 1 = svítí)
LED_R_PIN = 12
LED_G_PIN = 13
LED_B_PIN = 14

# Barvy LED (R, G, B)
LED_OFF = (0, 0, 0)
LED_RED = (1, 0, 0)
LED_GREEN = (0, 1, 0)
LED_YELLOW = (1, 1, 0)

# Tlačítko (mezi pinem a GND, vnitřní pull-up)
BUTTON_PIN = 15         # GP15, pin 20

# Wi-Fi
WIFI_COUNTRY = "CZ"     # povolí evropské kanály 12 a 13

# MQTT
MQTT_CLIENT_ID = "pico01"
MQTT_TOPIC_DATA = b"de2/pico01/data"
MQTT_TOPIC_STATUS = b"de2/pico01/status"
MQTT_KEEPALIVE_S = 30   # broker pozná výpadek Pica do 1,5 × 30 s
MQTT_TIMEOUT_S = 3      # max. čekání na síť, aby se nezasekly ostatní tasky

# Měsíc
SYNODIC_MONTH_D = 29.530588853                      # délka cyklu fází [dny]
KNOWN_NEW_MOON = (2000, 1, 6, 18, 14, 0, 0, 0)      # známý nov (UTC)
MOON_CX = 64            # střed Měsíce na displeji [px]
MOON_CY = 32
MOON_R = 30             # poloměr [px]

# Intervaly tasků [s]
SENSOR_INTERVAL_S = 2
DISPLAY_INTERVAL_S = 1
WIFI_INTERVAL_S = 5
MQTT_INTERVAL_S = 5
MQTT_WAIT_WIFI_S = 1    # jak často MQTT kontroluje, jestli už je Wi-Fi
LED_INTERVAL_S = 0.5    # zároveň rychlost blikání
BUTTON_INTERVAL_S = 0.03    # jak často se čte tlačítko
NTP_RETRY_S = 5         # jak často zkoušet stáhnout čas


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


def init_button():
    """Tlačítko proti GND s vnitřním pull-upem: 1 = puštěno, 0 = stisknuto."""
    return Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)


def init_gas():
    """Vrátí A/D převodník, na který je připojený výstup A0 senzoru MQ-9."""
    return ADC(GAS_ADC_PIN)


# ==================== Senzory ====================

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


def read_gas(adc):
    """Vrátí napětí na výstupu MQ-9 ve voltech (víc plynu = vyšší napětí)."""
    pin_voltage = adc.read_u16() * 3.3 / 65535     # ADC: 0..65535 = 0..3,3 V
    return pin_voltage * GAS_DIVIDER                # přepočet zpět přes dělič


# ==================== Displej ====================

def draw_display(oled, state):
    """Vykreslí aktuálně vybranou obrazovku."""
    if oled is None:
        return
    if state.screen == "moon":
        draw_moon_screen(oled, state)
    else:
        draw_sensor_screen(oled, state)
    oled.show()


def draw_sensor_screen(oled, state):
    """Naměřené hodnoty a stav Wi-Fi / MQTT."""
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
        oled.text(f"A:{a:4.0f}m G:{state.gas:.2f}V", 0, 44)

    # Stavový řádek
    if state.wifi_ok:
        wifi_text = "OK"
    elif state.wifi_connecting:
        wifi_text = ".."
    else:
        wifi_text = "--"
    mqtt_text = "OK" if state.mqtt_ok else "--"
    oled.text(f"WiFi:{wifi_text} MQTT:{mqtt_text}", 0, 56)


def draw_moon_screen(oled, state):
    """Fáze Měsíce - jen obrázek, bez textu."""
    oled.fill(0)
    if not state.time_ok:
        # Bez správného času nejde fázi spočítat
        oled.text("Cekam na cas", 16, 24)
        oled.text("(NTP)", 44, 36)
        return
    draw_moon(oled, moon_phase())


# ==================== Měsíc ====================

def moon_phase():
    """Vrátí fázi Měsíce 0..1 (0 = nov, 0.5 = úplněk) podle hodin Pica (UTC)."""
    seconds = time.time() - time.mktime(KNOWN_NEW_MOON)
    return (seconds / 86400 / SYNODIC_MONTH_D) % 1.0


def draw_moon(oled, phase):
    """Nakreslí Měsíc v dané fázi (0 = nov, 0.5 = úplněk).

    Kotouč se kreslí po řádcích. Při dorůstání svítí pravá strana,
    při couvání levá. Hranici světla a stínu určuje cos(fáze).
    """
    k = math.cos(2 * math.pi * phase)       # 1 = nov ... -1 = úplněk
    for dy in range(-MOON_R, MOON_R + 1):
        w = math.sqrt(MOON_R * MOON_R - dy * dy)    # půl šířky kotouče v řádku
        if phase < 0.5:
            x0, x1 = w * k, w               # dorůstá: svítí pravá strana
        else:
            x0, x1 = -w, -w * k             # couvá: svítí levá strana
        oled.hline(round(MOON_CX + x0), MOON_CY + dy, round(x1 - x0), 1)
    oled.ellipse(MOON_CX, MOON_CY, MOON_R, MOON_R, 1)   # obrys kotouče


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


def make_payload(values, gas):
    """Převede (t, h, p, a) a napětí plynu na JSON text pro MQTT."""
    t, h, p, a = values
    return json.dumps({
        "t": round(t, 2),
        "h": round(h, 2),
        "p": round(p, 2),
        "a": round(a),
        "g": round(gas, 2),
    })


# ==================== Sdílený stav ====================

class State:
    """Data sdílená mezi tasky. Tasky do něj zapisují a čtou z něj."""

    def __init__(self):
        self.values = None            # (t, h, p, a), nebo None při chybě senzoru
        self.gas = 0.0                # napětí senzoru plynu MQ-9 [V]
        self.wifi_ok = False          # připojeno k Wi-Fi
        self.wifi_connecting = False  # právě probíhá připojování
        self.mqtt_ok = False          # připojeno k MQTT brokeru
        self.time_ok = False          # hodiny nastavené přes NTP
        self.screen = "sensor"        # "sensor" nebo "moon"


# ==================== Tasky ====================

async def sensor_task(bme, gas_adc, state):
    """Každých SENSOR_INTERVAL_S sekund změří senzory a uloží hodnoty."""
    while True:
        state.gas = read_gas(gas_adc)
        state.values = read_sensor(bme)
        if state.values is not None:
            t, h, p, a = state.values
            print(f"T={t:.1f} C  H={h:.1f} %  P={p:.1f} hPa  A={a:.0f} m  G={state.gas:.2f} V")
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
                client.publish(MQTT_TOPIC_DATA, make_payload(state.values, state.gas))
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


async def button_task(button, state):
    """Při každém stisku tlačítka přepne obrazovku senzor <-> Měsíc."""
    was_pressed = False
    while True:
        pressed = button.value() == 0
        if pressed and not was_pressed:         # právě teď stisknuto
            state.screen = "moon" if state.screen == "sensor" else "sensor"
            print("Obrazovka:", state.screen)
        was_pressed = pressed
        await asyncio.sleep(BUTTON_INTERVAL_S)


async def time_task(state):
    """Po připojení k Wi-Fi jednou nastaví hodiny Pica přes NTP (pro fázi Měsíce)."""
    while not state.time_ok:
        if state.wifi_ok:
            try:
                ntptime.settime()       # nastaví hodiny Pica na UTC
                state.time_ok = True
                print(f"Cas nastaven, faze Mesice: {moon_phase():.2f}")
            except OSError as e:
                print("NTP chyba:", e)
        await asyncio.sleep(NTP_RETRY_S)


# ==================== Hlavní program ====================

async def main():
    led = init_led()
    button = init_button()
    gas = init_gas()
    i2c, devices = init_i2c()
    check_devices(devices)

    bme = init_bme280(i2c)
    oled = init_oled(i2c)
    wifi = init_wifi()
    state = State()

    await asyncio.gather(
        sensor_task(bme, gas, state),
        display_task(oled, state),
        wifi_task(wifi, state),
        mqtt_task(state),
        led_task(led, state),
        button_task(button, state),
        time_task(state),
    )


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program zastaven")
finally:
    set_led(init_led(), LED_OFF)    # po ukončení LED zhasnout
    asyncio.new_event_loop()        # vyčistí asyncio, aby šel program znovu spustit
