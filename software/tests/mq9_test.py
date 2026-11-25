from machine import ADC, Pin
from time import sleep

GAS_PIN = 26
ADC_VREF = 3.3
ADC_MAX = 65535

gas = ADC(Pin(GAS_PIN))

print("MQ-9 Gas Sensor Test")
print("Press Ctrl+C to stop the test.")

try:
    while True:
        raw_value = gas.read_u16()
        voltage = raw_value * ADC_VREF / ADC_MAX

        print("ADC:", raw_value,
              "| ADC voltage: {:.3f} V".format(voltage))

        sleep(2)

except KeyboardInterrupt:
    print("Test finished.")
