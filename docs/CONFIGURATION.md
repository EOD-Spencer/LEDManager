# Host configuration

The installed command is `ledcontrol`.

For the consolidated Arduino path, a practical default invocation is:

```bash
ledcontrol --led_count 20 --config_file ./ledcontrol.json --port 8080
```

On Windows or macOS, add `--dev` because the inherited production server dependency (`bjoern`) is only installed on Linux:

```bash
ledcontrol --led_count 20 --config_file ./ledcontrol.json --port 8080 --dev
```

## Command-line options

| Option | Default | Applies to Arduino serial path? | Purpose |
| --- | --- | --- | --- |
| `--port` | `80` | Yes | HTTP port for the web UI |
| `--host` | `0.0.0.0` | Yes | Interface/address the web server binds to |
| `--led_count` | `0` | **Yes** | Total logical LED count. For one strip, match Arduino `LED_COUNT` |
| `--config_file` | `/etc/ledcontrol.json` | **Yes** | JSON settings/preset file. An explicit writable path is recommended |
| `--pixel_mapping_json` | none | Yes | Optional pixel mapping JSON for non-linear/2D/3D layouts |
| `--fps` | `60` | **Yes** | Host animation and serial-render frame-rate limit |
| `--led_pin` | `18` | No | Raspberry Pi direct-output GPIO only |
| `--led_data_rate` | `800000` | No | Raspberry Pi direct-output LED data rate only |
| `--led_dma_channel` | `10` | No | Raspberry Pi direct-output DMA channel only |
| `--led_pixel_order` | `GRB` | No | Raspberry Pi direct-output color order only. Arduino order is `PIXEL_TYPE` in the sketch |
| `--led_brightness_limit` | `1.0` | Yes | Maximum brightness exposed by the UI, from `0.0` to `1.0` |
| `--save_interval` | `60` | Yes | Auto-save interval in seconds |
| `--sacn` | off | Yes/host feature | Enables inherited E1.31/sACN support |
| `--hap` | off | Yes/host feature | Enables inherited HomeKit support |
| `--no_timer_reset` | off | Yes | Prevents animation timer reset when patterns change |
| `--dev` | off | Host only | Uses Flask's development server instead of `bjoern` |

Run `ledcontrol --help` to see the runtime parser's current option list.

## Network exposure

The default host value is `0.0.0.0`, which means the UI listens on all available interfaces. This is useful when controlling the LEDs from a phone or another computer on the LAN.

There is currently no built-in user authentication. Treat the web UI as a trusted-LAN service.

For local-only access:

```bash
ledcontrol --led_count 20 --config_file ./ledcontrol.json --host 127.0.0.1 --port 8080
```

## Settings file

The application creates the configured settings file if it does not exist and automatically saves to it.

Saved state includes:

- global settings
- group definitions and serial targets
- presets
- custom/modified animation functions
- custom palettes

For the consolidated workflow, prefer an explicit path:

```bash
--config_file ./ledcontrol.json
```

This avoids permission and portability problems with the inherited `/etc/ledcontrol.json` default.

### Backups and recovery

When an old settings schema is migrated, the previous data may be copied to a `.bak` file.

If the configured JSON exists but cannot be parsed or applied, the application copies it to an `.error` file and continues with default settings.

If the UI unexpectedly returns to defaults, check the host console and look beside the configured settings file for these backup files.

## Arduino serial target

The Arduino serial port is configured per LED group in **Setup**, not with a command-line `--serial_port` argument.

Examples:

- Windows: `COM4`
- Linux: `/dev/ttyACM0`
- macOS: `/dev/cu.usbmodem...`

A group also owns a start/end LED range. The end is exclusive. For one 20-pixel strip, `0` to `20` covers the full strip.

## LED-count synchronization

For the standard single-Arduino setup, these must agree:

```text
Host:    --led_count 20
Arduino: LED_COUNT = 20
UI:      group range 0 to 20
```

A mismatch can produce missing pixels, truncated frames, or groups that address LEDs the Arduino does not have.

## Frame rate and serial bandwidth

The current wire format sends three payload bytes per logical pixel plus protocol overhead at 115200 baud. The default 20-LED configuration is comfortably within the intended operating range.

If the installation grows substantially, lower `--fps` if necessary before redesigning the protocol or changing hardware. Serial bandwidth and the Arduino's memory become relevant as LED count increases.

## Raspberry Pi direct output

Arguments such as `--led_pin`, `--led_data_rate`, `--led_dma_channel`, and `--led_pixel_order` are inherited for direct Raspberry Pi LED output. They do not configure the Arduino serial renderer.

That legacy path uses the `rpi_ws281x` submodule and is retained for compatibility rather than being the primary supported architecture.
