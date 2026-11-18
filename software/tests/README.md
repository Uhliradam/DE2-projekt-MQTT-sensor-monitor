
# Component Tests

This directory contains standalone test programs for verifying the functionality of individual hardware components connected to the Raspberry Pi Pico W.

All tests are written in MicroPython and have been verified on the actual hardware.

## Available Tests

| Component | Test File | Description |
|---|---|---|
| BME280 Sensor | [bme280_test.py](bme280_test.py) | Verifies I2C communication, chip identification, and temperature, humidity, and pressure measurements. |
| SH1106 OLED Display | [sh1106_test.py](sh1106_test.py) | Tests display pixels, geometric shapes, text rendering, and screen updates. |
| RGB LED | [rgb_test.py](rgb_test.py) | Tests individual LED colors, combined colors, and yellow blinking. |

## Test Descriptions

### BME280 Sensor Test

The test checks whether the BME280 sensor is detected on the I2C bus at address `0x76` and verifies its chip ID (`0x60`).

It then performs 10 measurements of temperature, humidity, and atmospheric pressure, checking whether the measured values are within predefined ranges.

**Expected result:** All measurements are completed successfully and the terminal displays `PASS`.

### SH1106 OLED Display Test

The test verifies the functionality of the OLED display by showing four test patterns:

1. All pixels illuminated.
2. A rectangular border with diagonal lines.
3. Eight rows of text.
4. A sample monitoring screen.

Each pattern is displayed for 10 seconds. The test also measures the time required to update the display.

**Expected result:** All patterns are displayed correctly without missing pixels or rendering errors.

### RGB LED Test

The test verifies seven LED colors: red, green, blue, yellow, cyan, purple, and white.

Each color is displayed for 3 seconds. The LED then blinks yellow six times to simulate the connection process.

**Expected result:** All colors are displayed correctly, followed by yellow blinking. The LED turns off when the test finishes.

## Running the Tests

The tests are designed for the Raspberry Pi Pico W running MicroPython.

1. Connect the required hardware components.
2. Open the project in Thonny IDE.
3. Make sure the required driver libraries are available on the Raspberry Pi Pico W.
4. Open the selected test file.
5. Run the test and observe the output in the terminal or on the connected hardware.

The BME280 and SH1106 tests require their corresponding driver libraries, [bme280.py](../bme280.py) and [sh1106.py](../sh1106.py).

## Test Results

All three component tests were successfully verified on the Raspberry Pi Pico W.

The BME280 sensor, SH1106 OLED display, and RGB LED operate as expected.
