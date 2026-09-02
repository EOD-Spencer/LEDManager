# Arduino firmware

This firmware is the hardware half of the consolidated LED Controller project. It replaces the standalone `ArduinoLEDController` pattern program with a small USB serial renderer that is controlled by the LED Controller web application.

## Target hardware

- Arduino Uno or compatible board
- SK6812 RGBW addressable LEDs
- LED data connected to digital pin 10 by default
- 20 LEDs by default
- USB serial connection to the computer running LED Controller

## Required Arduino library

Install **Adafruit NeoPixel** from the Arduino Library Manager.

## Before flashing

Open `ArduinoLEDController.ino` and verify these values near the top of the file:

```cpp
static const uint16_t LED_COUNT = 20;
static const uint8_t LED_PIN = 10;
static const neoPixelType PIXEL_TYPE = NEO_GRBW + NEO_KHZ800;
```

`LED_COUNT` must match the `--led_count` value used when starting the host application.

If your strip uses a different RGBW byte order, change `NEO_GRBW` to the appropriate Adafruit NeoPixel order for the strip.

## Flashing

1. Connect the Arduino by USB.
2. Select the correct board and serial port in Arduino IDE.
3. Open `ArduinoLEDController.ino`.
4. Compile and upload it.
5. Leave the Arduino attached by USB.
6. Start LED Controller on the computer and open its Setup page.
7. Set the group render mode to **Serial (Arduino / USB LED Controller)**.
8. Enter the Arduino serial port, for example `COM4` on Windows or `/dev/ttyACM0` on Linux.

## Protocol

The firmware intentionally implements the existing LED Manager serial packet protocol instead of creating a second API. The computer renders animations and sends RGB/HSV frames at 115200 baud; the Arduino converts those frames to RGBW and updates the SK6812 strip.

The Arduino therefore does not contain separate copies of the web application's animation patterns. That keeps the firmware small and makes the web application the single source of truth for effects and configuration.
