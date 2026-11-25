# Main Application

## Overview

The [`main.py`](main.py) file is the main application entry point of the MQTT Sensor Monitor.

It coordinates environmental and gas sensor measurements, OLED display modes, Wi-Fi connectivity, MQTT communication, RGB LED status indication, push button input, time synchronization, and lunar phase visualization using asynchronous tasks.

This document describes the internal operation of the main program. General project information, hardware connections, software architecture, and timing are available in the [main project README](../README.md).

## Table of Contents

- [Program Initialization](#program-initialization)
- [Main Functions](#main-functions)
- [Asynchronous Tasks](#asynchronous-tasks)
- [Shared Application State](#shared-application-state)
- [Gas Sensor Data Processing](#gas-sensor-data-processing)
- [OLED Display Modes](#oled-display-modes)
- [Lunar Phase Calculation](#lunar-phase-calculation)
- [MQTT Data Processing](#mqtt-data-processing)
- [Error Handling](#error-handling)
- [Program Execution](#program-execution)

## Program Initialization

The application starts by executing the asynchronous `main()` function.

The initialization process consists of the following steps:

1. Initialize the RGB LED GPIO pins.
2. Initialize the push button with an internal pull-up resistor.
3. Initialize the ADC interface for the MQ-9 gas sensor.
4. Initialize the I2C bus and scan for connected devices.
5. Check whether the expected BME280 sensor and OLED display are detected.
6. Initialize the BME280 sensor and SH1106 OLED display.
7. Activate the Wi-Fi interface in station mode.
8. Create a shared application state.
9. Start seven asynchronous tasks using `asyncio.gather()`.

The initialization functions report selected hardware errors to the console. If the BME280 sensor or OLED display cannot be initialized, the application can continue with reduced functionality.

## Main Functions

The main program contains functions responsible for hardware initialization, sensor measurements, display rendering, status indication, lunar phase calculation, and communication.

| Function | Description |
|---|---|
| `init_i2c()` | Initializes the I2C bus and returns the interface and detected device addresses. |
| `check_devices(devices)` | Checks whether the expected I2C devices are detected. |
| `init_bme280(i2c)` | Initializes the BME280 sensor and returns its object or `None` on failure. |
| `init_oled(i2c)` | Initializes the OLED display and returns its object or `None` on failure. |
| `init_wifi()` | Activates the Wi-Fi interface in station mode. |
| `init_led()` | Initializes the RGB LED GPIO pins and turns the LED off. |
| `init_button()` | Initializes the push button as a digital input with an internal pull-up resistor. |
| `init_gas()` | Initializes the ADC interface for the MQ-9 gas sensor. |
| `read_sensor(bme)` | Reads environmental measurements and returns a tuple of values or `None`. |
| `read_gas(adc)` | Reads the analog gas sensor signal and converts it into voltage. |
| `draw_display(oled, state)` | Selects and updates the active OLED display mode. |
| `draw_sensor_screen(oled, state)` | Displays sensor measurements and connection status. |
| `draw_moon_screen(oled, state)` | Displays the current lunar phase or an NTP waiting message. |
| `moon_phase()` | Calculates the current position within the lunar cycle. |
| `draw_moon(oled, phase)` | Draws the illuminated part and outline of the Moon. |
| `set_led(led, color)` | Sets the RGB LED color by controlling individual GPIO outputs. |
| `led_color(state, blink_on)` | Determines the RGB LED color based on connection status. |
| `mqtt_connect()` | Connects to the MQTT broker and publishes the online status. |
| `mqtt_close(client)` | Closes the MQTT client socket. |
| `make_payload(values, gas)` | Converts environmental measurements and gas sensor voltage into a JSON message. |
| `main()` | Initializes the application and starts all asynchronous tasks. |

## Asynchronous Tasks

The application starts seven asynchronous tasks using MicroPython `asyncio`.

The tasks periodically yield control using `await asyncio.sleep()`, allowing multiple system functions to operate concurrently.

| Task | Description |
|---|---|
| `sensor_task()` | Reads environmental measurements and gas sensor voltage. |
| `display_task()` | Updates the currently selected OLED display mode. |
| `wifi_task()` | Monitors Wi-Fi connectivity and attempts reconnection when necessary. |
| `mqtt_task()` | Manages MQTT communication and publishes sensor measurements. |
| `led_task()` | Updates RGB LED indication according to connection status. |
| `button_task()` | Detects button presses and switches between display modes. |
| `time_task()` | Synchronizes the internal clock using NTP. |

### Sensor Task

The `sensor_task()` function periodically reads both sensors.

The `read_sensor()` function retrieves temperature, humidity, atmospheric pressure, and estimated altitude from the BME280 sensor. The measurements are stored in `state.values`.

The `read_gas()` function reads the analog output of the MQ-9 sensor. The resulting voltage is stored in `state.gas`.

Successful environmental measurements and gas sensor voltage are printed to the MicroPython console.

If a BME280 measurement fails, `state.values` is set to `None`.

### Display Task

The `display_task()` function periodically calls `draw_display()` to update the OLED screen.

The displayed content depends on the current value of `state.screen`.

The application supports two display modes:

- Environmental measurement screen
- Lunar phase screen

If an OLED communication error occurs, the error is printed to the console and the task continues.

### Wi-Fi Task

The `wifi_task()` function checks the wireless connection using `wifi.isconnected()`.

If the connection is unavailable, it attempts to reconnect using `connect_async()` from [`wifi_utils.py`](wifi_utils.py).

The task updates the connection flags in the shared state and prints the assigned IP address after successful connection.

### MQTT Task

The `mqtt_task()` function manages communication with the MQTT broker.

When Wi-Fi is available, the task establishes an MQTT connection if necessary and publishes the latest sensor measurements.

If no valid BME280 measurements are available, the client sends an MQTT ping instead.

If communication fails, the client socket is closed and the application attempts to reconnect during a later task cycle.

When Wi-Fi becomes unavailable, the MQTT connection is closed and the task waits for wireless connectivity to be restored.

### RGB LED Task

The `led_task()` function periodically updates the RGB LED using the `set_led()` and `led_color()` functions.

The LED color is determined by the connection flags stored in the shared application state.

| LED Color | Meaning |
|---|---|
| Green | Both Wi-Fi and MQTT are connected. |
| Red | Wi-Fi or MQTT is unavailable. |
| Blinking Yellow | A Wi-Fi connection attempt is in progress. |

The `blink_on` variable alternates between `True` and `False` every 0.5 seconds, enabling the blinking indication.

### Button Task

The `button_task()` function periodically checks the state of the push button.

The button uses an internal pull-up resistor and operates with active-low logic:

- Logic 1: Button released
- Logic 0: Button pressed

The task checks the button state every 30 milliseconds.

A new button press is detected by comparing the current state with the previous state stored in `was_pressed`.

Each detected press switches `state.screen` between `sensor` and `moon`.

Holding the button does not continuously switch between display modes.

### Time Synchronization Task

The `time_task()` function synchronizes the internal clock of the Raspberry Pi Pico W using the Network Time Protocol (NTP).

Once Wi-Fi connectivity is available, the function calls `ntptime.settime()` to set the internal clock to UTC.

After successful synchronization, `state.time_ok` is set to `True`.

If synchronization fails, the task retries after five seconds.

The task finishes after successful synchronization. The synchronized clock is subsequently used for lunar phase calculations.

## Shared Application State

The `State` class stores information shared between asynchronous tasks.

| Attribute | Description |
|---|---|
| `values` | Latest measurements stored as `(temperature, humidity, pressure, altitude)`, or `None`. |
| `gas` | Latest MQ-9 gas sensor voltage in volts. |
| `wifi_ok` | Indicates whether Wi-Fi is connected. |
| `wifi_connecting` | Indicates whether a Wi-Fi connection attempt is in progress. |
| `mqtt_ok` | Indicates whether the MQTT client has successfully connected. |
| `time_ok` | Indicates whether the internal clock has been synchronized using NTP. |
| `screen` | Currently selected OLED display mode (`sensor` or `moon`). |

The shared state allows individual tasks to access the latest measurements, connection information, and display settings.

The default display mode after startup is `sensor`.

## Gas Sensor Data Processing

The MQ-9 sensor provides an analog output signal related to the presence of carbon monoxide and combustible gases.

The analog signal is read using the MicroPython `ADC` interface.

The `read_u16()` method returns a value between 0 and 65535.

The ADC input voltage is calculated using:

```python
pin_voltage = adc.read_u16() * 3.3 / 65535
```

The application then applies the configured voltage divider compensation:

```python
return pin_voltage * GAS_DIVIDER
```

The current implementation uses `GAS_DIVIDER = 2`, assuming a voltage divider consisting of two equal resistors.

The resulting value is stored in the shared application state and displayed on the OLED and transmitted through MQTT.

The gas sensor output is represented in volts. The application does not convert the measured voltage into gas concentration in ppm.

## OLED Display Modes

The OLED display supports two modes selected using the push button.

### Environmental Measurement Screen

The environmental measurement screen displays:

| Symbol | Measurement | Unit |
|---|---|---|
| T | Temperature | °C |
| H | Relative humidity | % |
| P | Atmospheric pressure | hPa |
| A | Estimated altitude | m |
| G | Gas sensor voltage | V |

The bottom line displays the current Wi-Fi and MQTT connection status.

If BME280 measurements are unavailable, a sensor error message is displayed.

### Lunar Phase Screen

The lunar phase screen displays a graphical representation of the current lunar phase.

The displayed image is calculated directly by the Raspberry Pi Pico W.

If the internal clock has not been synchronized, the display shows a waiting message instead of the lunar phase.

The push button allows the user to return to the environmental measurement screen.

## Lunar Phase Calculation

The `moon_phase()` function calculates the current lunar phase using the internal clock synchronized through NTP.

The calculation uses a known new moon reference date:

- Reference date: January 6, 2000, at 18:14 UTC
- Average synodic month: 29.530588853 days

The elapsed time since the reference date is divided by the average duration of the lunar cycle.

The result is normalized to a value between 0 and 1.

| Phase Value | Lunar Phase |
|---|---|
| 0.00 | New Moon |
| 0.25 | First Quarter |
| 0.50 | Full Moon |
| 0.75 | Last Quarter |
| 1.00 | Beginning of the next lunar cycle |

Intermediate values represent waxing and waning phases.

The `draw_moon()` function uses mathematical operations to calculate the illuminated portion of the Moon.

The lunar disc is rendered line by line using horizontal lines. The boundary between the illuminated and dark regions is calculated using the cosine of the lunar phase angle.

During waxing phases, the right side of the Moon is illuminated. During waning phases, the left side is illuminated.

An elliptical outline is drawn around the lunar disc.

This method provides an approximate graphical representation of the current lunar phase without requiring an external astronomical API.

## MQTT Data Processing

The `make_payload()` function converts environmental measurements and gas sensor voltage into a JSON message.

Example output:

```json
{
  "t": 24.06,
  "h": 44.1,
  "p": 983.42,
  "a": 254,
  "g": 0.85
}
```

| JSON Key | Description | Unit |
|---|---|---|
| `t` | Temperature | °C |
| `h` | Relative humidity | % |
| `p` | Atmospheric pressure | hPa |
| `a` | Estimated altitude | m |
| `g` | Gas sensor voltage | V |

Temperature, humidity, pressure, and gas sensor voltage are rounded to two decimal places.

Estimated altitude is rounded to the nearest integer.

### MQTT Topics

| Topic | Description |
|---|---|
| `de2/pico01/data` | Contains sensor measurements in JSON format. |
| `de2/pico01/status` | Contains the device connection status (`online` or `offline`). |

After establishing an MQTT connection, the application publishes a retained `online` status message.

An `offline` message is configured as the MQTT Last Will, allowing the broker to indicate an unexpected connection loss.

The MQTT client uses a keepalive interval of 30 seconds and a connection timeout of three seconds.

## Error Handling

The application includes basic error handling for selected hardware and communication failures.

| Error | Application Behavior |
|---|---|
| Missing I2C device | Prints a warning to the console. |
| BME280 initialization failure | Returns `None` and continues running. |
| BME280 reading failure | Stores `None` instead of environmental measurements. |
| OLED initialization failure | Skips display updates. |
| OLED communication failure | Prints an error message and continues. |
| Wi-Fi disconnection | Attempts reconnection asynchronously. |
| MQTT communication failure | Closes the client and attempts reconnection during a later cycle. |
| Missing BME280 measurements | Sends an MQTT ping instead of sensor data. |
| NTP synchronization failure | Retries time synchronization. |
| Time not synchronized | Displays a waiting message on the lunar phase screen. |

Selected hardware and communication errors are handled using `try` and `except` blocks.

## Program Execution

The application starts with:

```python
asyncio.run(main())
```

The `main()` function initializes the required components and starts seven asynchronous tasks:

```python
await asyncio.gather(
    sensor_task(bme, gas, state),
    display_task(oled, state),
    wifi_task(wifi, state),
    mqtt_task(state),
    led_task(led, state),
    button_task(button, state),
    time_task(state),
)
```

The main tasks run continuously until the application is interrupted or an unhandled exception occurs. The time synchronization task finishes after successfully setting the internal clock.

A `KeyboardInterrupt` is handled to allow the program to stop from the MicroPython console.

The `finally` block turns off the RGB LED and creates a new asyncio event loop so the application can be started again.
