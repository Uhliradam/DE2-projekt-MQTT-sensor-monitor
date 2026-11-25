# Component Tests

This directory contains standalone test programs for verifying the functionality of individual hardware components connected to the Raspberry Pi Pico W.

All tests are written in MicroPython and are designed to verify individual components before running the complete application.

## Available Tests

| Component | Test File | Description |
|---|---|---|
| BME280 Sensor | [bme280_test.py](bme280_test.py) | Verifies I2C communication, chip identification, and temperature, humidity, and pressure measurements. |
| SH1106 OLED Display | [sh1106_test.py](sh1106_test.py) | Tests display pixels, geometric shapes, text rendering, and screen updates. |
| RGB LED | [rgb_test.py](rgb_test.py) | Tests individual LED colors, combined colors, and yellow blinking. |
| Push Button | [button_test.py](button_test.py) | Verifies button press and release detection, internal pull-up resistor, and press counting. |
| MQ-9 Gas Sensor | [mq9_test.py](mq9_test.py) | Verifies analog signal acquisition and ADC voltage calculation. |

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

### Push Button Test

The test verifies the functionality of the push button connected to GPIO 15.

The button is configured as a digital input with an internal pull-up resistor. The released state corresponds to logic 1, while the pressed state corresponds to logic 0.

The program detects changes in the button state and uses a 30 ms debounce delay to reduce unwanted transitions caused by mechanical contact bouncing.

Each detected button press increases the press counter. Press and release events are displayed in the terminal.

Holding the button does not continuously increase the counter.

**Expected result:** Each button press and release is detected correctly, and the counter increases once per press without repeated events.

### MQ-9 Gas Sensor Test

The test verifies analog signal acquisition from the MQ-9 gas sensor using GPIO 26 (ADC0).

The program reads raw ADC values in the range of 0–65535 and converts them into voltage using a reference voltage of 3.3 V.

The raw ADC value and calculated ADC input voltage are displayed in the terminal every 2 seconds.

Before running the test, the sensor should be allowed to warm up according to its requirements. The voltage applied to the ADC input must not exceed 3.3 V.

The test verifies analog signal acquisition only. It does not verify gas concentration measurement accuracy or sensor calibration.

**Expected result:** ADC values and corresponding voltages are displayed every 2 seconds without unexpected program errors.

## Running the Tests

The tests are designed for the Raspberry Pi Pico W running MicroPython.

1. Connect the required hardware components.
2. Open the project in Thonny IDE.
3. Make sure the required driver libraries are available on the Raspberry Pi Pico W.
4. Open the selected test file.
5. Run the test and observe the output in the terminal or on the connected hardware.
6. Stop continuously running tests using Ctrl+C.

The BME280 and SH1106 tests require their corresponding driver libraries, [bme280.py](../bme280.py) and [sh1106.py](../sh1106.py).

The RGB LED, push button, and MQ-9 tests use built-in MicroPython modules and do not require additional driver libraries.

## Test Results

| Component | Status |
|---|---|
| BME280 Sensor | PASS |
| SH1106 OLED Display | PASS |
| RGB LED | PASS |
| Push Button | Pending |
| MQ-9 Gas Sensor | Pending |

The BME280 sensor, SH1106 OLED display, and RGB LED have been successfully verified on the Raspberry Pi Pico W and operate as expected.

The push button and MQ-9 gas sensor tests are prepared and awaiting hardware verification.
