# Architecture

## Purpose

LED Controller is one system with two runtime components:

1. **Host application** — Python/Flask backend plus Vue-based browser UI.
2. **Arduino firmware** — USB serial renderer for SK6812 RGBW LEDs.

Both components live in this repository and are expected to evolve together.

## Supported primary path

```text
Browser or phone
      |
      | HTTP
      v
Python host / animation engine
      |
      | LED Manager serial protocol @ 115200 baud
      v
Arduino Uno or compatible
      |
      | 800 kHz NeoPixel data
      v
SK6812 RGBW strip
```

## Responsibility boundaries

### Browser/UI

The UI is responsible for user-facing configuration and control, including:

- global and per-group brightness
- saturation
- patterns and animation parameters
- palettes
- presets
- LED group ranges
- render mode and serial-port target

### Host application

The host is the system's control plane and animation engine. It:

- stores settings and presets
- executes animation functions
- calculates each logical pixel frame
- applies group configuration
- encodes RGB or HSV frames into the serial protocol
- opens/reopens the configured Arduino serial port
- sends a render packet followed by a write command

Effects should remain here unless there is a specific architectural reason to move them.

### Arduino firmware

The Arduino is intentionally a device driver, not a second application. It:

- parses the existing LED Manager packet format
- validates packet type and length
- receives RGB or HSV pixel data
- applies correction/brightness/saturation behavior
- derives the RGBW white component
- buffers pixel values in the NeoPixel library
- calls `strip.show()` when commanded

It does not contain a separate library of warning-light or animation patterns.

## Configuration ownership

Some values exist on both sides and must remain synchronized:

| Setting | Host | Arduino | Rule |
| --- | --- | --- | --- |
| Total LED count | `--led_count` | `LED_COUNT` | Must match for a single strip |
| Serial baud | fixed by host transport | `SERIAL_BAUD` | Both are 115200 |
| LED data pin | not used for serial target | `LED_PIN` | Arduino-only |
| RGBW byte order | not used for serial target | `PIXEL_TYPE` | Arduino-only |
| Group ranges | saved UI settings | packet start/end | Host is source of truth |

The end of a group range is **exclusive**. A 20-pixel strip uses `0` to `20`.

## Persistence

The host saves settings to the configured JSON file. Saved data includes controller settings, groups, presets, modified/custom functions, and custom palettes.

The default inherited path is `/etc/ledcontrol.json`, but the consolidated Arduino workflow should normally use an explicit writable path such as `./ledcontrol.json`.

## Serial lifecycle

Opening the USB serial port can reset an Arduino Uno-compatible board. The host therefore waits after opening a serial target before sending the first frame. If a serial write fails, the host closes that connection and retries it on a later frame.

## RGBW model

The serial protocol carries three bytes per logical pixel, either RGB or HSV. The Arduino derives the white channel rather than receiving an independent W byte.

This is a compatibility decision inherited from the LED Manager remote-rendering protocol. Independent four-channel RGBW values would require a protocol extension and matching host/UI changes.

## Legacy code

The repository still contains inherited Raspberry Pi direct-output support and the `rpi_ws281x` submodule. That path is retained for compatibility but is not the primary target of the consolidated system.

The previous Pico/Pico W external-controller firmware was removed. There should not be another independent firmware implementation added casually; doing so would recreate the maintenance split this consolidation was intended to eliminate.

## Change discipline

When changing the system:

- serial packet changes must modify host, Arduino firmware, and `docs/PROTOCOL.md` together;
- hardware-default changes must update the sketch and both hardware-facing READMEs;
- UI labels should describe the supported Arduino/USB target rather than old Pico-specific terminology;
- effects belong in the host animation engine unless explicitly designed otherwise.
