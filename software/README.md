
# Main Application

## Overview

The [`main.py`](main.py) file is the main application entry point of the MQTT Sensor Monitor.

It coordinates sensor measurements, OLED display updates, Wi-Fi connectivity, and MQTT communication using asynchronous tasks.

This document describes the internal operation of the main program. General project information, hardware connections, software architecture, and timing are available in the [main project README](../README.md).

## Table of Contents

- [Program Initialization](#program-initialization)
- [Main Functions](#main-functions)
- [Asynchronous Tasks](#asynchronous-tasks)
- [Shared Application State](#shared-application-state)
- [MQTT Data Processing](#mqtt-data-processing)
- [Error Handling](#error-handling)
- [Program Execution](#program-execution)

## Program Initialization

The application starts by executing the asynchronous `main()` function.

The initialization process consists of the following steps:

1. Initialize the I2C bus and scan for connected devices.
2. Check whether the expected sensor and display are detected.
3. Initialize the BME280 sensor and SH1106 OLED display.
4. Activate the Wi-Fi interface in station mode.
5. Create a shared application state.
6. Start four asynchronous tasks using `asyncio.gather()`.

The initialization functions report hardware errors to the console. If the sensor or display cannot be initialized, the application can continue with reduced functionality.

## Main Functions

The main program contains several functions responsible for initialization, data processing, and communication.

| Function | Description |
|---|---|
| `init_i2c()` | Initializes the I2C bus and returns the interface and detected device addresses. |
| `check_devices()` | Checks whether the expected I2C devices are detected. |
| `init_bme280()` | Initializes the BME280 sensor and returns its object or `None` on failure. |
| `init_oled()` | Initializes the OLED display and returns its object or `None` on failure. |
| `init_wifi()` | Activates the Wi-Fi interface in station mode. |
| `read_sensor()` | Reads sensor measurements and returns a tuple of values or `None`. |
| `draw_display()` | Displays measurements and connection status on the OLED. |
| `mqtt_connect()` | Connects to the MQTT broker and publishes the online status. |
| `mqtt_close()` | Closes the MQTT client socket. |
| `make_payload()` | Converts sensor measurements into a JSON message. |
| `main()` | Initializes the application and starts all asynchronous tasks. |

## Asynchronous Tasks

The application uses four asynchronous tasks that operate concurrently.

Each task runs in a continuous loop and periodically yields control using `await asyncio.sleep()`.

| Task | Description |
|---|---|
| `sensor_task()` | Reads environmental measurements and stores them in the shared state. |
| `display_task()` | Updates the OLED display using the latest measurements and connection status. |
| `wifi_task()` | Monitors Wi-Fi connectivity and attempts reconnection when necessary. |
| `mqtt_task()` | Manages MQTT communication and publishes sensor measurements. |

### Sensor Task

The `sensor_task()` function periodically calls `read_sensor()` and stores the latest measurements in `state.values`.

Successful measurements are also printed to the MicroPython console.

If a measurement fails, `state.values` is set to `None`.

### Display Task

The `display_task()` function calls `draw_display()` to update the OLED screen.

The display uses the latest measurements stored in the shared state and indicates the current Wi-Fi and MQTT connection status.

If sensor data is unavailable, an error message is displayed.

### Wi-Fi Task

The `wifi_task()` function checks the wireless connection using `wifi.isconnected()`.

If the connection is unavailable, it attempts to reconnect using `connect_async()` from [`wifi_utils.py`](wifi_utils.py).

The task updates the connection flags in the shared state and prints the assigned IP address after successful connection.

### MQTT Task

The `mqtt_task()` function manages communication with the MQTT broker.

When Wi-Fi is available, the task establishes an MQTT connection if necessary and publishes the latest sensor measurements.

If no valid measurements are available, the client sends an MQTT ping instead.

If communication fails, the client is closed and the application attempts to reconnect during a later task cycle.

## Shared Application State

The `State` class stores information shared between asynchronous tasks.

| Attribute | Description |
|---|---|
| `values` | Latest measurements stored as `(temperature, humidity, pressure, altitude)`, or `None`. |
| `wifi_ok` | Indicates whether Wi-Fi is connected. |
| `wifi_connecting` | Indicates whether a Wi-Fi connection attempt is in progress. |
| `mqtt_ok` | Indicates whether the MQTT client has successfully connected. |

This approach allows individual tasks to operate independently while accessing the same measurements and connection information.

## MQTT Data Processing

The `make_payload()` function converts sensor measurements into a JSON message.

Example output:

```json
{
  "t": 24.06,
  "h": 44.1,
  "p": 983.42,
  "a": 254
}
```

The values represent temperature, humidity, atmospheric pressure, and estimated altitude.

Temperature, humidity, and pressure are rounded to two decimal places. Estimated altitude is rounded to the nearest integer.

After establishing an MQTT connection, the application publishes a retained `online` status message.

An `offline` message is configured as the MQTT Last Will, allowing the broker to indicate an unexpected connection loss.

## Error Handling

The application includes basic error handling for hardware and communication failures.

| Error | Application Behavior |
|---|---|
| Sensor initialization failure | Returns `None` and continues running. |
| Sensor reading failure | Stores `None` instead of measurements. |
| OLED initialization failure | Skips display updates. |
| OLED communication failure | Prints an error message and continues. |
| Wi-Fi disconnection | Attempts reconnection asynchronously. |
| MQTT communication failure | Closes the client and attempts reconnection during a later cycle. |

Selected hardware and communication errors are handled using `try` and `except` blocks.

## Program Execution

The application starts with:

```python
asyncio.run(main())
```

The `main()` function initializes the required components and starts four asynchronous tasks:

```python
await asyncio.gather(
    sensor_task(bme, state),
    display_task(oled, state),
    wifi_task(wifi, state),
    mqtt_task(state),
)
```

The tasks run continuously until the application is interrupted or an unhandled exception occurs.

A `KeyboardInterrupt` is handled to allow the program to stop from the MicroPython console.

The `finally` block creates a new asyncio event loop so the application can be started again.
