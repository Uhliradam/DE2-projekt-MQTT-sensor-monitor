from machine import I2C, Pin
import time

from bme280 import BME280
from sh1106 import SH1106_I2C


# -------------------- Pinout --------------------

LED_R_PIN = 12
LED_G_PIN = 13
LED_B_PIN = 14

I2C_SDA = 4
I2C_SCL = 5
I2C_FREQ = 400_000

BME280_ADDR = 0x76
OLED_ADDR = 0x3C
# -------------------- Initialization --------------------

def init_i2c():
    i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=I2C_FREQ)
    devices = i2c.scan()
    print("I2C zarizeni:", [hex(d) for d in devices])
    return i2c, devices


def init_bme280(i2c):
    try:
        return BME280(i2c=i2c, addr=BME280_ADDR)
    except OSError as e:
        print("BME280 init selhal:", e)
        return None


def init_oled(i2c):
    try:
        return SH1106_I2C(i2c)
    except OSError as e:
        print("OLED init selhal:", e)
        return None


# -------------------- Senzor --------------------

def read_sensor(bme):
    if bme is None:
        return None
    try:
        t, h, p, _ = bme.read_values()
        return t, h, p
    except OSError as e:
        print("Chyba cteni senzoru:", e)
        return None


# -------------------- Displej --------------------

def draw_display(oled, values):
    if oled is None:
        return
    oled.fill(0)
    oled.text("Sensor monitor", 0, 0)
    oled.hline(0, 10, 128, 1)

    if values is None:
        oled.text("Sensor error!", 0, 28)
    else:
        t, h, p = values
        oled.text(f"T: {t:6.1f} C", 0, 16)
        oled.text(f"H: {h:6.1f} %", 0, 28)
        oled.text(f"P: {p:6.1f} hPa", 0, 40)

    oled.show()


# -------------------- Hlavni program --------------------

i2c, devices = init_i2c()

if BME280_ADDR not in devices:
    print("BME280 nenalezen!")
if OLED_ADDR not in devices:
    print("OLED nenalezen!")

bme = init_bme280(i2c)
oled = init_oled(i2c)

while True:
    values = read_sensor(bme)
    if values:
        print("T={:.1f} C  H={:.1f} %  P={:.1f} hPa".format(*values))
    draw_display(oled, values)
    time.sleep(2)
