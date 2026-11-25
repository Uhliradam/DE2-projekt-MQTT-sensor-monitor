# Node-RED Dashboard

## Overview

The Node-RED dashboard provides a web-based interface for monitoring environmental measurements received from the Raspberry Pi Pico W through the MQTT broker.

The dashboard displays current sensor measurements, historical data, estimated altitude, and device connection status.

The complete Node-RED flow configuration is available in [flows.json](flows.json).

## Software Dependencies

| Software / Package | Description |
|---|---|
| Node.js | Runtime environment required by Node-RED. |
| Node-RED | Flow-based programming environment for processing MQTT messages. |
| @flowfuse/node-red-dashboard | Dashboard 2.0 package for web-based data visualization. |
| Eclipse Mosquitto | MQTT broker responsible for message distribution. |

## Dashboard Features

| Feature | Description |
|---|---|
| Temperature | Current temperature displayed using a gauge. |
| Humidity | Current relative humidity displayed using a gauge. |
| Atmospheric Pressure | Current atmospheric pressure displayed using a gauge. |
| Estimated Altitude | Estimated altitude calculated from atmospheric pressure. |
| Historical Data | Line charts displaying temperature, humidity, and pressure over the last hour. |
| Device Status | Online or offline indication of the Raspberry Pi Pico W. |
| Responsive Layout | Dashboard layout adapts to different screen sizes. |

## Application Architecture

The dashboard receives MQTT messages from the Mosquitto broker and processes them using Node-RED nodes.

The data processing sequence is:

1. The Raspberry Pi Pico W publishes sensor measurements to the MQTT broker.
2. An MQTT input node receives and parses the JSON message.
3. A function node separates the individual sensor measurements.
4. The measurements are forwarded to the corresponding dashboard widgets.
5. Gauges display current measurements.
6. Line charts display historical measurements.
7. A separate MQTT input node receives device connection status messages.

## MQTT Communication

The Node-RED flow uses the following MQTT broker configuration:

| Parameter | Value |
|---|---|
| Broker | localhost |
| Port | 1883 |
| Protocol | MQTT 3.1.1 |
| QoS | 0 |
| Keepalive | 60 s |
| TLS | Disabled |

The default configuration assumes that Node-RED and the Mosquitto broker are running on the same computer.

### MQTT Topics

| Topic | Description |
|---|---|
| `de2/pico01/data` | Receives sensor measurements in JSON format. |
| `de2/pico01/status` | Receives device connection status messages. |

### Data Processing

The function node extracts the following values from incoming JSON messages:

| JSON Key | Measurement | Unit |
|---|---|---|
| `t` | Temperature | °C |
| `h` | Relative humidity | % |
| `p` | Atmospheric pressure | hPa |
| `a` | Estimated altitude | m |

Each measurement is forwarded to its corresponding dashboard widget.

The current dashboard flow processes BME280 measurements. MQ-9 gas sensor visualization is not yet included.

## Dashboard Layout

The dashboard is divided into three groups.

### Device Status (Stav zařízení)

Displays the current connection status of the Raspberry Pi Pico W and estimated altitude.

The device status is represented by:

- 🟢 Online
- 🔴 Offline

### Current Measurements (Aktuální hodnoty)

Displays current environmental measurements using three gauges.

| Measurement | Minimum | Maximum | Unit |
|---|---|---|---|
| Temperature | 0 | 40 | °C |
| Humidity | 0 | 100 | % |
| Atmospheric Pressure | 900 | 1050 | hPa |

### Historical Data (Historie)

Displays three line charts:

- Temperature history
- Relative humidity history
- Atmospheric pressure history

Each chart displays measurements collected over the last hour. Older measurements are automatically removed from the chart.

## Running the Dashboard

### 1. Install Node-RED

Install Node.js and then install Node-RED using npm:

```bash
npm install -g node-red
```

### 2. Start the MQTT Broker

Start the Eclipse Mosquitto broker and make sure it is accessible on port 1883.

### 3. Start Node-RED

Run the following command:

```bash
node-red
```

Open the Node-RED editor in a web browser:

http://localhost:1880

### 4. Install Dashboard 2.0

1. Open the Node-RED menu.
2. Select Manage palette.
3. Open the Install tab.
4. Search for `@flowfuse/node-red-dashboard`.
5. Install the package.

### 5. Import the Flow

1. Open the Node-RED menu.
2. Select Import.
3. Import the [flows.json](flows.json) file.
4. Verify the MQTT broker configuration.
5. Click Deploy.

### 6. Start the Sensor Monitor

Run the [main application](../software/main.py) on the Raspberry Pi Pico W.

Make sure the device is connected to the wireless network and configured to use the correct MQTT broker address.

### 7. Open the Dashboard

Open the following address in a web browser:

http://localhost:1880/dashboard/sensor

To access the dashboard from another device on the local network, replace `localhost` with the IP address of the computer running Node-RED.

## Related Documentation

- [Main Project README](../README.md)
- [Main Application Documentation](../software/README.md)
- [Component Tests Documentation](../software/tests/README.md)
