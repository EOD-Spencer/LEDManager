# led-control WS2812B LED Controller Server
# Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

import argparse
from ledcontrol.app import create_app

def main():
    parser = argparse.ArgumentParser(
        description='LED Controller host for browser-controlled LEDs. The primary consolidated path is USB serial -> Arduino -> SK6812 RGBW.'
    )
    parser.add_argument('--port', type=int, default=80,
                        help='Port to use for web interface. Default: 80')
    parser.add_argument('--host', default='0.0.0.0',
                        help='Address to bind the web interface to. Default: 0.0.0.0 (all interfaces; no built-in authentication)')
    parser.add_argument('--led_count', type=int, default=0,
                        help='Total logical LED count. For a single Arduino strip, match firmware LED_COUNT.')
    parser.add_argument('--config_file',
                        help='Settings JSON path. Inherited default: /etc/ledcontrol.json. A writable explicit path such as ./ledcontrol.json is recommended.')
    parser.add_argument('--pixel_mapping_json', type=argparse.FileType('r'),
                        help='Optional JSON file containing pixel mapping for non-linear/2D/3D layouts')
    parser.add_argument('--fps', type=int, default=60,
                        help='Host animation/render refresh-rate limit in FPS. Default: 60')
    parser.add_argument('--led_pin', type=int, default=18,
                        help='Raspberry Pi direct-output GPIO only. Ignored by Arduino serial rendering. Default: 18')
    parser.add_argument('--led_data_rate', type=int, default=800000,
                        help='Raspberry Pi direct-output LED data rate only. Ignored by Arduino serial rendering. Default: 800000 Hz')
    parser.add_argument('--led_dma_channel', type=int, default=10,
                        help='Raspberry Pi direct-output DMA channel only. Ignored by Arduino serial rendering. Default: 10')
    parser.add_argument('--led_pixel_order', default='GRB',
                        help='Raspberry Pi direct-output color order only. Arduino color order is PIXEL_TYPE in the sketch. Default: GRB')
    parser.add_argument('--led_brightness_limit', type=float, default=1.0,
                        help='LED maximum brightness exposed by the web UI. Float from 0.0-1.0. Default: 1.0')
    parser.add_argument('--save_interval', type=int, default=60,
                        help='Interval for automatically saving settings in seconds. Default: 60')
    parser.add_argument('--sacn', action='store_true',
                        help='Enable inherited sACN / E1.31 support. Default: False')
    parser.add_argument('--hap', action='store_true',
                        help='Enable inherited HomeKit Accessory Protocol support. Default: False')
    parser.add_argument('--no_timer_reset', action='store_true',
                        help='Do not reset the animation timer when patterns are changed. Default: False')
    parser.add_argument('--dev', action='store_true',
                        help='Use the Flask development server instead of bjoern. Needed for normal Windows/macOS operation with current dependencies.')
    args = parser.parse_args()

    app = create_app(args.led_count,
                     args.config_file,
                     args.pixel_mapping_json,
                     args.fps,
                     args.led_pin,
                     args.led_data_rate,
                     args.led_dma_channel,
                     args.led_pixel_order.upper(),
                     args.led_brightness_limit,
                     args.save_interval,
                     args.sacn,
                     args.hap,
                     args.no_timer_reset,
                     args.dev)

    if args.dev:
        app.run(host=args.host, port=args.port)
    else:
        import bjoern
        bjoern.run(app, host=args.host, port=args.port)
