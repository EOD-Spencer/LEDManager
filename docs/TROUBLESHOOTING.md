# Troubleshooting

Use this guide for the supported path:

```text
web UI -> host application -> USB serial -> Arduino -> SK6812 RGBW LEDs
```

Work from left to right. Do not start by changing animation code when the host cannot open the serial port or the strip is not powered correctly.

## Host does not start

### Permission error involving `/etc/ledcontrol.json`

The inherited default settings path is `/etc/ledcontrol.json`.

Use an explicit writable path instead:

```bash
ledcontrol --led_count 20 --config_file ./ledcontrol.json --port 8080
```

### `bjoern` cannot be imported

`bjoern` is only installed by this project on Linux. On Windows or macOS, use the Flask server:

```bash
ledcontrol --led_count 20 --config_file ./ledcontrol.json --port 8080 --dev
```

### `ledcontrol` command is not found

Install the project from the repository root:

```bash
python -m pip install -e .
```

If multiple Python installations exist, make sure the `pip` invocation and the shell environment use the same Python installation.

## UI does not open

The default HTTP port is 80. The README examples use 8080 to avoid privileged-port problems.

Start with:

```bash
ledcontrol --led_count 20 --config_file ./ledcontrol.json --port 8080 --dev
```

Then open:

```text
http://localhost:8080
```

If opening from another device, use the host computer's LAN IP instead of `localhost` and make sure the process is bound to `0.0.0.0` rather than `127.0.0.1`.

Remember that the application currently has no built-in authentication. Do not expose it directly to an untrusted network or the public internet.

## UI works but LEDs remain dark

Check these in order:

1. Arduino firmware is flashed successfully.
2. The Arduino remains attached by USB to the host.
3. The strip has a suitable 5 V supply.
4. Arduino ground and LED-power ground are common.
5. The LED strip is connected to **data input**, not data output.
6. `LED_PIN` in the sketch matches the physical data connection.
7. `LED_COUNT` in the sketch matches host `--led_count` for the normal single-strip setup.
8. In **Setup**, Render Mode is `Serial (Arduino / USB LED Controller)`.
9. The configured serial port is correct.
10. The group range covers the intended LEDs. For 20 LEDs, use `0` to `20`.
11. Arduino IDE Serial Monitor or another program is not holding the same serial port open.
12. Check the host console for `LED controller serial error` messages.

Opening an Uno-compatible serial connection usually resets the board. The host intentionally pauses after first opening the port, so initial output may not appear instantly.

## Serial controller disconnects or reconnects repeatedly

The host closes a failed serial connection and retries it on a later frame.

Check:

- loose or charge-only USB cables;
- USB hubs or power-saving behavior;
- another application opening the same COM/device port;
- Linux device permissions;
- Arduino resets caused by unstable power.

On Linux, the account running LED Controller must have permission to open the serial device. Depending on the distribution, USB serial devices are often assigned to a group such as `dialout`.

## Only some LEDs work

Check all three count/range values:

```text
Host --led_count
Arduino LED_COUNT
UI group start/end
```

For one 20-pixel strip:

```text
--led_count 20
LED_COUNT = 20
range 0 to 20
```

The range end is exclusive.

Also inspect power injection and voltage drop if failures begin farther down a longer strip.

## Colors are wrong

The most likely cause is LED channel order.

The default sketch uses:

```cpp
NEO_GRBW + NEO_KHZ800
```

If red, green, blue, or white channels are swapped, change `PIXEL_TYPE` to the correct Adafruit NeoPixel order for the actual strip and reflash the Arduino.

Use the application's color-correction/calibration feature only after basic channel order is correct.

## White behavior is unexpected

The protocol does not send an independent W value. The host sends RGB or HSV and the Arduino derives a white component for the RGBW strip.

That is intentional compatibility behavior. True independent white-channel animation would require a protocol extension.

## LEDs flicker, reset, or behave erratically

Treat intermittent behavior as a wiring/power/signal problem before assuming it is an animation bug.

Check:

- stable 5 V power at the strip;
- common ground;
- adequate wire size and connectors;
- correct data direction;
- short/reliable data wiring;
- sufficient power-supply capacity;
- power injection for longer strips.

If the installation has been expanded far beyond the default 20 LEDs, also reduce host frame rate with `--fps` to determine whether serial bandwidth or MCU load is contributing.

## Settings disappear or revert

Always know which settings file the process is using. The recommended consolidated invocation includes:

```bash
--config_file ./ledcontrol.json
```

The application saves automatically, by default every 60 seconds, and again during normal shutdown.

If settings JSON is invalid, the host preserves the bad file with an `.error` suffix and starts from defaults. Older files can also produce `.bak` migration backups.

Check the host console for the exact loaded/saved path.

## A change works in the UI but not on the Arduino

If the change affects packet content or rendering semantics, compare both sides of the protocol:

- `ledcontrol/ledcontroller.py`
- `firmware/ArduinoLEDController/ArduinoLEDController.ino`
- `docs/PROTOCOL.md`

Those three must agree. Protocol changes should never be made to only one side.

## Raspberry Pi direct-output problems

Direct Raspberry Pi LED output is inherited compatibility code, not the primary consolidated hardware path. It uses the `rpi_ws281x` submodule and different command-line hardware settings.

Do not apply Arduino-specific settings such as the UI serial port to diagnose Raspberry Pi direct output, and do not assume that path was validated by the Arduino consolidation work.
