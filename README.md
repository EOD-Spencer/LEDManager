# LED Controller

A single web-controlled RGBW LED system combining the useful parts of the former **LEDManager** and **ArduinoLEDController** projects.

The browser application renders animations, palettes, brightness, saturation, presets, and LED groups. An Arduino connected by USB receives those rendered frames and drives an SK6812 RGBW strip.

## Architecture

```text
Browser
   |
   v
LED Controller web app
   |
   | USB serial @ 115200 baud
   v
Arduino Uno
   |
   v
SK6812 RGBW LEDs
```

There is intentionally only one animation engine. The Arduino firmware does not contain a second set of hard-coded patterns; it renders frames sent by the host application.

## What was consolidated

This repository replaces two previously separate projects:

- `LEDManager` supplied the web UI, animation engine, palettes, presets, grouping, and serial rendering protocol.
- `ArduinoLEDController` supplied the Arduino/SK6812 hardware target.

The old Arduino warning-light program was not copied into the new firmware because it duplicated animation logic and was not compatible with the web application. The included Arduino firmware implements the existing LED Manager serial protocol directly.

## Hardware

Default configuration:

- Arduino Uno or compatible
- SK6812 RGBW LEDs
- 20 LEDs
- Arduino digital pin 10 -> LED data input
- Common ground between Arduino and LED power supply
- Appropriate 5 V LED power supply

Do not power a substantial LED installation through the Arduino board. Size wiring, fusing, and the 5 V supply for the actual LED load.

## 1. Flash the Arduino

The firmware is in:

`firmware/ArduinoLEDController/ArduinoLEDController.ino`

Install **Adafruit NeoPixel** with Arduino Library Manager, verify `LED_COUNT`, `LED_PIN`, and `PIXEL_TYPE`, then compile and upload the sketch.

See `firmware/ArduinoLEDController/README.md` for the hardware-side details.

## 2. Install the host application

Python 3.7 or newer is required by the existing LED Manager application.

```bash
python -m pip install -e .
```

On systems where more than one Python installation is present, use the Python executable you intend to run LED Controller with.

## 3. Start LED Controller

For the default 20-LED strip:

```bash
ledcontrol --led_count 20 --port 8080
```

Then open the web interface on the computer running it:

`http://localhost:8080`

The LED count supplied to the host must match `LED_COUNT` in the Arduino sketch.

## 4. Connect the web app to the Arduino

Open **Setup** in the web interface.

For the main LED group:

- Set **Render Mode** to `Serial (Arduino / USB LED Controller)`.
- Set **Render Target** to the Arduino serial port.

Examples:

- Windows: `COM4`
- Linux: `/dev/ttyACM0`
- macOS: `/dev/cu.usbmodem...`

Return to **Control** and select a pattern. Brightness, saturation, palettes, animation speed, scale, presets, and group controls are rendered by the host and streamed to the Arduino.

## RGBW behavior

The host's existing remote-rendering protocol sends RGB or HSV values. The Arduino firmware converts them to RGBW using the same approach as the former Pico firmware, including use of the dedicated white channel when colors are desaturated.

This preserves compatibility with the existing LED Manager UI and animation engine without requiring an immediate protocol rewrite.

## Repository layout

```text
firmware/ArduinoLEDController/   Arduino Uno + SK6812 RGBW firmware
ledcontrol/                      Python host, web API, animation engine, UI
img/                             Existing animation previews/documentation assets
setup.py                         Python package/CLI installation
```

## Project direction

The supported primary path for this consolidated project is:

**web UI -> USB serial -> Arduino -> RGBW LEDs**

Raspberry Pi direct-output support remains in the inherited host code for compatibility, but the included external-controller firmware is now Arduino-focused. Legacy Pico/Pico W firmware has been removed to avoid maintaining multiple hardware implementations in the same project.

## License and attribution

This project contains MIT-licensed work originally from `jackw01/led-control` and new/modified work by Cody Spencer. See `LICENSE` and `NOTICE.md`.
