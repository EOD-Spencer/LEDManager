# Arduino firmware

This firmware is the hardware half of the consolidated LED Controller project. The web host renders animations; the Arduino receives those frames over USB serial and drives the physical SK6812 RGBW strip.

The firmware is intentionally a renderer, not a second effects engine.

## Target hardware

Current defaults:

- Arduino Uno or compatible board
- SK6812 RGBW addressable LEDs
- 20 LEDs
- LED data on Arduino digital pin 10
- `NEO_GRBW + NEO_KHZ800`
- USB serial connection to the host at 115200 baud

> The protocol implementation has been reconciled with the host in code. Physical Arduino + strip validation is still required for the current hardware defaults.

## Wiring

At minimum:

```text
Arduino pin 10  -> SK6812 DIN
Arduino GND     -> LED power-supply GND
LED supply +5 V -> SK6812 +5 V
LED supply GND  -> SK6812 GND
```

The Arduino and LED power supply must share ground so the data signal has a common reference.

Connect to the strip's **data input** end. Addressable strips are directional.

Do not use the Arduino board as the main power source for a substantial LED installation. Size the external 5 V supply, wiring, connectors, and protection for the actual installation.

## Required Arduino library

Install **Adafruit NeoPixel** through Arduino Library Manager.

The sketch includes:

```cpp
#include <Adafruit_NeoPixel.h>
```

## Configuration before flashing

Open `ArduinoLEDController.ino` and verify:

```cpp
static const uint16_t LED_COUNT = 20;
static const uint8_t LED_PIN = 10;
static const uint32_t SERIAL_BAUD = 115200;
static const neoPixelType PIXEL_TYPE = NEO_GRBW + NEO_KHZ800;
```

### LED count

For the normal one-Arduino setup, `LED_COUNT` must match the host's `--led_count` value.

For 20 LEDs:

```text
Host:    --led_count 20
Arduino: LED_COUNT = 20
UI:      range 0 to 20
```

The UI range end is exclusive.

### Data pin

If the strip data wire is connected to another digital pin, change `LED_PIN` to match.

### Pixel order

SK6812 strips are sold with different channel orders. The default is `NEO_GRBW`.

If colors are swapped, change `PIXEL_TYPE` to the appropriate Adafruit NeoPixel RGBW order and reflash. Do not try to compensate for a wrong hardware byte order with color correction.

## Flashing

1. Connect the Arduino by USB.
2. Open the sketch in Arduino IDE.
3. Select the correct Arduino board.
4. Select the correct serial port.
5. Install Adafruit NeoPixel if it is not already available.
6. Compile and upload the sketch.
7. Leave the Arduino connected to the computer running LED Controller.
8. Close Arduino Serial Monitor if it is open; only one application should own the serial port.
9. Start the LED Controller host.
10. In the web UI, open **Setup**.
11. Set Render Mode to **Serial (Arduino / USB LED Controller)**.
12. Enter the Arduino serial port.
13. Set the group range. For the default 20 LEDs, use `0` to `20`.

Typical serial-port names:

- Windows: `COM4`
- Linux: `/dev/ttyACM0`
- macOS: `/dev/cu.usbmodem...`

## Startup behavior

Opening a serial connection commonly resets an Arduino Uno-compatible board. The host accounts for this by pausing after opening the port before it begins sending frames.

If a serial write fails, the host closes that connection and retries it on a later frame.

## Protocol

The firmware implements the existing LED Manager packet protocol instead of defining another API.

The host sends:

- calibration packets;
- RGB render packets;
- HSV render packets;
- a separate write/display command.

See [`docs/PROTOCOL.md`](../../docs/PROTOCOL.md) for the exact byte layout.

## RGBW behavior

The current protocol transmits three bytes per logical pixel as RGB or HSV. It does not transmit a fourth independent white byte.

The firmware derives the SK6812 white component so the existing LED Manager host can control an RGBW strip without a protocol rewrite.

## Firmware safety checks

The parser rejects unsupported command IDs, impossible packet lengths, and render packets that are too short for their declared LED range. Received ranges are clamped to `LED_COUNT`.

The input buffer is fixed-size to avoid dynamic allocation on the Uno.

## Troubleshooting

If the UI works but the strip does not, see [`docs/TROUBLESHOOTING.md`](../../docs/TROUBLESHOOTING.md).

The most common hardware-side causes are:

- wrong serial port;
- Serial Monitor holding the port open;
- `LED_COUNT` mismatch;
- wrong `LED_PIN`;
- wrong `PIXEL_TYPE`/channel order;
- missing common ground;
- reversed strip direction;
- insufficient or unstable 5 V power.
