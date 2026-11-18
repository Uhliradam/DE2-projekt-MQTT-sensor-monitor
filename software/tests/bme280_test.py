"""
Test BME280
Ověří adresu a chip ID a přečte 10 hodnot, u kterých zkontroluje rozumný rozsah.
"""
from machine import I2C, Pin
import time
from bme280 import BME280

I2C_SDA = 4
I2C_SCL = 5
I2C_FREQ = 400_000

BME280_ADDR = 0x76
CHIP_ID_REG = 0xD0
CHIP_ID_BME280 = 0x60

SAMPLES = 10

# Rozumné rozsahy pro místnost (min, max)
T_RANGE = (5, 40)        # °C
H_RANGE = (10, 90)       # %
P_RANGE = (900, 1100)    # hPa


def in_range(value, limits):
    return limits[0] <= value <= limits[1]


def main():
    print("=== Test BME280 ===")
    i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=I2C_FREQ)
    devices = i2c.scan()
    print("I2C zarizeni:", [hex(d) for d in devices])

    # 1) Adresa
    if BME280_ADDR not in devices:
        print("FAIL: senzor nenalezen na adrese", hex(BME280_ADDR))
        return
    print("OK: senzor nalezen na", hex(BME280_ADDR))

    # 2) Chip ID
    chip_id = i2c.readfrom_mem(BME280_ADDR, CHIP_ID_REG, 1)[0]
    if chip_id != CHIP_ID_BME280:
        print("FAIL: chip ID", hex(chip_id), "(0x58 = BMP280, nema vlhkost)")
        return
    print("OK: chip ID", hex(chip_id), "= BME280")

    # 3) Měření
    bme = BME280(i2c=i2c, addr=BME280_ADDR)
    errors = 0
    for i in range(SAMPLES):
        try:
            t, h, p, _ = bme.read_values()
        except OSError as e:
            print(f"{i + 1:2d}: CHYBA CTENI {e}")
            errors += 1
        else:
            ok = in_range(t, T_RANGE) and in_range(h, H_RANGE) and in_range(p, P_RANGE)
            if not ok:
                errors += 1
            result = "OK" if ok else "MIMO ROZSAH"
            print(f"{i + 1:2d}: T={t:5.1f} C  H={h:5.1f} %  P={p:6.1f} hPa  {result}")
        time.sleep(1)

    if errors == 0:
        print("=== PASS ===")
    else:
        print(f"=== FAIL: {errors} z {SAMPLES} mereni chybnych ===")


main()
