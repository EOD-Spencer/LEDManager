# LED Controller

`EOD-Spencer/LEDManager` is the single source of truth for the LED Controller system. It contains both the browser-based LED Manager host application and the Arduino firmware that drives the physical RGBW LEDs.

The supported primary architecture is:

```text
Browser / phone
      |
      v
LED Controller host application
      |
      | USB serial @ 115200 baud
      v
Arduino Uno or compatible
      |
      v
SK6812 RGBW LEDs
```

The host owns animations, palettes, brightness, saturation, presets, groups, and timing. The Arduino is intentionally a small renderer: it receives frames from the host and writes them to the LED strip. There is only one animation engine.

> **Current validation status:** the host/firmware protocol has been reconciled in code. A physical Arduino + SK6812 hardware test is still required before the current defaults should be treated as hardware-validated.

## Documentation

- [Arduino firmware and wiring](firmware/ArduinoLEDController/README.md)
- [Architecture and ownership boundaries](docs/ARCHITECTURE.md)
- [Host configuration and command-line options](docs/CONFIGURATION.md)
- [USB serial protocol](docs/PROTOCOL.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Built-in animation previews](animations.md)
- [License and attribution](NOTICE.md)

## Default hardware configuration

The included Arduino sketch currently assumes:

- Arduino Uno or compatible AVR board
- SK6812 RGBW LEDs
- 20 LEDs
- LED data on Arduino digital pin 10
- `NEO_GRBW + NEO_KHZ800`
- USB serial at 115200 baud
- common ground between Arduino and LED power supply
- an external 5 V supply sized appropriately for the LED installation

Do not power a substantial LED installation through the Arduino board. Size the 5 V supply, wiring, connectors, and circuit protection for the actual LED load.

## Quick start

### 1. Flash the Arduino

The firmware is:

`firmware/ArduinoLEDController/ArduinoLEDController.ino`

Install **Adafruit NeoPixel** through Arduino Library Manager. Before uploading, verify these constants near the top of the sketch:

```cpp
static const uint16_t LED_COUNT = 20;
static const uint8_t LED_PIN = 10;
static const neoPixelType PIXEL_TYPE = NEO_GRBW + NEO_KHZ800;
```

`LED_COUNT` must match the host's `--led_count` value. See the [firmware README](firmware/ArduinoLEDController/README.md) for wiring and flashing details.

### 2. Install the host application

Python 3.7 or newer is required by the inherited LED Manager application.

From the repository root:

```bash
python -m pip install -e .
```

The package keeps the historical `ledcontrol` command name.

### 3. Start the host

Use an explicit writable settings file. This avoids depending on the inherited `/etc/ledcontrol.json` default, which is mainly appropriate to Linux appliance-style installs.

```bash
ledcontrol --led_count 20 --config_file ./ledcontrol.json --port 8080
```

On Windows or macOS, add `--dev` because the production `bjoern` server is only installed on Linux:

```bash
ledcontrol --led_count 20 --config_file ./ledcontrol.json --port 8080 --dev
```

Open:

`http://localhost:8080`

By default the host binds to `0.0.0.0`, which makes the UI reachable from other devices on the same network. There is currently **no built-in authentication**, so only expose it on a trusted network. Use `--host 127.0.0.1` if the UI should only be reachable from the host computer.

### 4. Connect the UI to the Arduino

Open **Setup** in the web interface. For the LED group you want to drive:

- **Render Mode:** `Serial (Arduino / USB LED Controller)`
- **Serial Port:** the Arduino's USB serial device
- **Range:** the LEDs assigned to that group; the end value is exclusive

Typical serial-port examples:

- Windows: `COM4`
- Linux: `/dev/ttyACM0`
- macOS: `/dev/cu.usbmodem...`

For a single 20-LED strip, use a range of `0` to `20`.

Return to **Control** and choose a pattern. The host renders frames and streams them to the Arduino.

## Settings and persistence

The host automatically saves controller settings, groups, presets, custom animation changes, and custom palettes. The default save interval is 60 seconds and can be changed with `--save_interval`.

For the consolidated Arduino workflow, an explicit local config path is recommended:

```bash
--config_file ./ledcontrol.json
```

If an existing settings file is invalid, the application preserves a copy with an `.error` suffix before starting with defaults. Older settings may be backed up with a `.bak` suffix during migration.

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for the complete command-line reference and which arguments apply only to inherited Raspberry Pi direct-output support.

## RGBW behavior

The existing remote-rendering protocol sends three bytes per logical pixel as RGB or HSV. It does not transmit an independent fourth white byte. The Arduino firmware derives the SK6812 white channel using behavior compatible with the former remote-renderer implementation.

That keeps the existing UI and animation engine compatible with RGBW strips without duplicating effects in the firmware. If fully independent R/G/B/W control is needed later, the serial protocol must be extended.

## Repository layout

```text
firmware/ArduinoLEDController/   Arduino + SK6812 RGBW firmware
ledcontrol/                      Python host, web API, animation engine, UI
docs/                            Architecture, configuration, protocol, troubleshooting
img/                             Animation preview assets
animations.md                    Built-in animation preview index
setup.py                         Python package and CLI metadata
LICENSE / NOTICE.md              Licensing and upstream attribution
```

## Legacy Raspberry Pi support

Direct Raspberry Pi LED output remains in the inherited host code and `rpi_ws281x` submodule for compatibility. It is not the primary hardware path for this consolidated project and was not part of the Arduino consolidation validation pass.

The Pico/Pico W external-controller firmware was intentionally removed. New external-controller work should target the Arduino serial implementation unless the project explicitly decides to add another supported hardware target.

## Project rules

To prevent the two halves from drifting apart again:

1. Host UI/backend and Arduino firmware stay in this repository.
2. The host remains the source of truth for animations and effects.
3. Wire-protocol changes must update both host and firmware in the same change.
4. Any protocol change must also update `docs/PROTOCOL.md`.
5. Hardware defaults must stay synchronized between the root README, firmware README, and Arduino sketch.

## License and attribution

This repository contains MIT-licensed work derived from `jackw01/led-control` plus Arduino firmware and consolidation work by Cody Spencer / EOD-Spencer. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
