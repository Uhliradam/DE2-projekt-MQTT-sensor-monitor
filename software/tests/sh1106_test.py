"""
Test OLED displeje SH1106
Postupně zobrazí 4 testovací obrazce a vypíše, co má být vidět.
"""
from machine import I2C, Pin
import time
from sh1106 import SH1106_I2C

I2C_SDA = 4
I2C_SCL = 5
I2C_FREQ = 400_000
OLED_ADDR = 0x3C

STEP_S = 10      # jak dlouho je vidět každý obrazec


def main():
    print("=== Test SH1106 ===")
    i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=I2C_FREQ)
    devices = i2c.scan()
    print("I2C zarizeni:", [hex(d) for d in devices])

    if OLED_ADDR not in devices:
        print("FAIL: displej nenalezen na adrese", hex(OLED_ADDR))
        return
    print("OK: displej nalezen na", hex(OLED_ADDR))

    oled = SH1106_I2C(i2c)
    try:
        # 1) Všechny pixely
        print("1/4 Cely displej bily - hledej mrtve pixely")
        oled.fill(1)
        oled.show()
        time.sleep(STEP_S)

        # 2) Rámeček a úhlopříčky
        print("2/4 Ramecek a krizek - ramecek musi byt videt CELY na vsech 4 stranach")
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.line(0, 0, 127, 63, 1)
        oled.line(0, 63, 127, 0, 1)
        oled.show()
        time.sleep(STEP_S)

        # 3) 8 řádků textu
        print("3/4 Osm radku textu 'Radek 0' az 'Radek 7'")
        oled.fill(0)
        for row in range(8):
            oled.text(f"Radek {row}", 0, row * 8)
        oled.show()
        time.sleep(STEP_S)

        # 4) Rozvržení z main.py
        print("4/4 Ukazka obrazovky z main.py")
        oled.fill(0)
        oled.text("Sensor monitor", 0, 0)
        oled.hline(0, 10, 128, 1)
        oled.text("T:   24.0 C", 0, 14)
        oled.text("H:   44.0 %", 0, 24)
        oled.text("P:  983.4 hPa", 0, 34)
        oled.text("A:    255 m", 0, 44)
        oled.text("WiFi:OK", 0, 56)

        start = time.ticks_ms()
        oled.show()
        print("Doba show():", time.ticks_diff(time.ticks_ms(), start), "ms")
        time.sleep(STEP_S)

        print("=== Hotovo - sedely vsechny obrazce? ===")
    finally:
        oled.fill(0)        # displej vždy smazat, i po Stop / Ctrl+C
        oled.show()


main()
