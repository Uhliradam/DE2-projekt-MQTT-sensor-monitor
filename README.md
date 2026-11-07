# DE2-projekt-MQTT-sensor-monitor
> MQTT Sensor Monitor using Raspberry Pi Pico W and MicroPython.

An IoT environmental monitoring system that measures temperature, humidity, and atmospheric pressure using a BME280 sensor. The measured data is transmitted via Wi-Fi to an MQTT broker and can be visualized on a web dashboard.

## Poster
*Coming soon*

## Video Demonstration
*Coming soon*

## Table of Contents
- [Poster](#poster)
- [Video Demonstration](#video-demonstration)
- [Overview](#overview)
- [Team](#team)
- [How It Works](#how-it-works)
- [Hardware](#hardware)
  - [Hardware Components](#hardware-components)
  - [Hardware Connections](#hardware-connections)
- [Architecture](#architecture)
  - [Top-Level Block Diagram](#top-level-block-diagram)
  - [Wiring Diagram](#wiring-diagram)
  - [Software Architecture](#software-architecture)
  - [Timing and Concurrency](#timing-and-concurrency)
- [Project Structure](#project-structure)
- [License](#license)

## Overview
The MQTT Sensor Monitor is an IoT project designed to monitor environmental conditions using a Raspberry Pi Pico W and MicroPython.

The system measures temperature, humidity, and atmospheric pressure using a BME280 sensor. The collected data will be transmitted over Wi-Fi to an MQTT broker. As an optional extension, the measurements may also be visualized through a web dashboard.

The project demonstrates:

- Environmental monitoring using a BME280 sensor
- I2C communication between the sensor and Raspberry Pi Pico W
- Wireless communication via Wi-Fi
- MQTT protocol for transmitting sensor data
- Local indication of connection status
- Real-time data visualization using graphs
- Modular programming in MicroPython

## Team

The project is developed by a team of four students.

| Team Member | Responsibilities |
|-------------|------------------|
| Jakub Křiva |  |
| Adam Uhlíř | Repository Management & Documentation |
| Gabriel Novák |  |
| Jakub Oselka |  |

## How It Works

The MQTT Sensor Monitor collects environmental data using a BME280 sensor connected to a Raspberry Pi Pico W. The measured values are transmitted over Wi-Fi to an MQTT broker and can be displayed on a web dashboard.

| Step | Action | Description |
|------|--------|-------------|
| 1 | System Startup | Raspberry Pi Pico W initializes the sensor and other components. |
| 2 | Wi-Fi Connection | The device connects to the configured Wi-Fi network. |
| 3 | MQTT Connection | The device establishes a connection with the MQTT broker. |
| 4 | Sensor Measurement | The BME280 measures temperature, humidity, and atmospheric pressure. |
| 5 | Data Transmission | Sensor readings are published to MQTT topics at regular intervals. |
| 6 | Local Status Indication | LEDs or a display indicate the current connection status. |
| 7 | Data Visualization (Optional) | A web dashboard may display current measurements and graphs. |

As an optional extension, the system may detect connection failures and automatically reconnect when the network or MQTT broker becomes unavailable.

## Hardware

The MQTT Sensor Monitor is based on the Raspberry Pi Pico W microcontroller. It uses a BME280 sensor to measure environmental conditions and Wi-Fi connectivity to transmit data to an MQTT broker.

### Hardware Components

| Component | Description | Interface |
|-----------|-------------|-----------|
| Raspberry Pi Pico W | Main microcontroller running MicroPython | GPIO, I2C, Wi-Fi |
| BME280 Sensor | Measures temperature, humidity, and atmospheric pressure | I2C |
| Display / LEDs | Indicates Wi-Fi and MQTT connection status | SPI / I2C / GPIO |
| Wi-Fi Access Point | Provides wireless network connectivity | Wi-Fi |
| Computer | Hosts the MQTT broker and optional web dashboard | Wi-Fi / Ethernet |

### Hardware Connections

The BME280 sensor will communicate with the Raspberry Pi Pico W using the I2C interface. A display or LEDs will provide local feedback about the system status.

*The exact GPIO pin assignments and wiring diagram will be added after the hardware configuration is finalized.*

## Architecture

The MQTT Sensor Monitor is designed as a modular system consisting of sensor measurement, wireless communication, local status indication, and data visualization.

### Top-Level Block Diagram

*Coming soon – the system block diagram will be added here.*

### Wiring Diagram

*Coming soon – the wiring diagram with GPIO pin assignments will be added here.*

### Software Architecture

The software will be divided into separate modules to simplify development, testing, and maintenance.

| Module | Description |
|--------|-------------|
| BME280 Driver | Handles I2C communication and reads environmental measurements. |
| Wi-Fi Manager | Manages Wi-Fi connectivity and connection status. |
| MQTT Client | Publishes sensor data to the MQTT broker. |
| Display / LED Controller | Provides local indication of the connection status. |
| Main Application | Coordinates sensor measurements, communication, and system operation. |
| Web Dashboard | Displays received measurements and graphs (optional extension). |

### Timing and Concurrency

The system will perform sensor measurements, MQTT communication, and local status updates periodically.

MicroPython's `uasyncio` will be considered to coordinate these operations without unnecessary blocking.

The measurement intervals, publishing frequency, and task scheduling will be specified and verified during implementation.

## Project Structure

The current repository structure is as follows:

```text
DE2-projekt-MQTT-sensor-monitor/
│
├── complete-projects/    # ZIP archives of complete project versions
│   └── .gitkeep
│
├── README.md             # Project documentation
├── LICENSE               # MIT License
└── .gitignore            # Git ignore rules
```
## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.





