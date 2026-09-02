# USB serial protocol

This document defines the wire protocol between the LED Controller host and the Arduino firmware.

Any change to this protocol must update both:

- `ledcontrol/ledcontroller.py`
- `firmware/ArduinoLEDController/ArduinoLEDController.ino`

The protocol runs at **115200 baud**.

## Packet framing

Every packet begins with a four-byte header:

| Byte | Meaning |
| --- | --- |
| `0` | Start byte: `0x00` |
| `1` | Command type |
| `2` | Total packet length, high byte |
| `3` | Total packet length, low byte |

Packet length is an unsigned 16-bit **big-endian** value and includes the four-byte header.

The parser is length-driven. Zero bytes may therefore appear inside packet payloads without being interpreted as a new packet start.

## Command types

| Value | Name | Purpose |
| --- | --- | --- |
| `0x00` | Calibration | Show the color-correction test color |
| `0x01` | Render RGB | Load RGB pixel values into the strip buffer |
| `0x02` | Render HSV | Load HSV pixel values into the strip buffer |
| `0x03` | Write LEDs | Call `strip.show()` and display the buffered frame |

Unknown command values are rejected by the Arduino parser.

## Calibration packet (`0x00`)

Total length: **8 bytes**.

```text
00 00 00 08 RR GG BB VV
```

| Bytes | Meaning |
| --- | --- |
| `4` | red correction, 0-255 |
| `5` | green correction, 0-255 |
| `6` | blue correction, 0-255 |
| `7` | brightness, 0-255 |

Calibration is applied immediately by the firmware.

## Render RGB packet (`0x01`)

Total length:

```text
13 + (pixel_count * 3)
```

Layout:

| Bytes | Meaning |
| --- | --- |
| `4-6` | RGB color-correction bytes |
| `7` | saturation, 0-255 |
| `8` | brightness, 0-255 |
| `9-10` | start LED index, big-endian |
| `11-12` | end LED index, big-endian and exclusive |
| `13...` | three bytes per pixel: R, G, B |

For a range `0` to `20`, the payload contains 20 logical pixels and 60 pixel-data bytes.

The firmware loads these values into the NeoPixel buffer but does not display them until a Write LEDs command arrives.

## Render HSV packet (`0x02`)

The packet structure is identical to Render RGB, but each three-byte pixel is:

```text
H S V
```

All values are encoded from `0` to `255`. The host maps its floating-point hue cycle into the byte-sized hue field before transmission.

The Arduino converts HSV to RGBW while applying the packet's saturation, brightness, and correction values.

## Write LEDs packet (`0x03`)

The host currently sends:

```text
00 03 00 05 00
```

The command causes the Arduino to call `strip.show()` and commit the previously buffered render data to the LEDs.

The fifth byte is retained for compatibility with the inherited LED Manager protocol; the Arduino renderer does not currently use its value.

## RGBW handling

The wire format is three bytes per logical pixel, not four. There is no independent W byte in the current protocol.

For an SK6812 RGBW strip, the firmware derives a white component from RGB/HSV input using the compatibility behavior implemented in the Arduino renderer.

A future protocol with independent RGBW values should use a new command type rather than silently changing the payload size of `0x01`, so existing firmware cannot misinterpret the frame.

## Range behavior

Start is inclusive and end is exclusive:

```text
start = 0
end   = 20
```

addresses LEDs `0` through `19`.

The Arduino clamps received ranges to `LED_COUNT` and ignores invalid or empty ranges.

## Error handling

The Arduino parser rejects packets when:

- the command value is outside the defined command range;
- the declared packet length is smaller than the header;
- the declared packet length exceeds the firmware input buffer;
- a render packet is shorter than required for its declared LED range.

After rejecting or completing a packet, the parser resets and waits for the next `0x00` start byte.

The host handles serial write failures by closing the failed port and retrying it on a later frame. Opening an Arduino Uno-compatible serial port may reset the board, so the host waits briefly after opening a new connection before streaming frames.
