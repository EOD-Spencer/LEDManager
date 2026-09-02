# led-control WS2812B LED Controller Server
# Copyright 2021-2023 jackw01. Released under the MIT License (see LICENSE for details).
# Arduino serial integration/consolidation Copyright 2025-2026 Cody Spencer.

import atexit
import itertools
import time
import traceback
from enum import Enum

import numpy as np
import serial

import ledcontrol.animationfunctions as animfunctions
import ledcontrol.driver as driver


class TargetMode(str, Enum):
    local = 'local'
    serial = 'serial'


class LEDController:
    def __init__(self,
                 led_count,
                 led_pin,
                 led_data_rate,
                 led_dma_channel,
                 led_pixel_order):
        if driver.is_raspberrypi():
            px_order = driver.WS2811_STRIP_GRB
            if led_pixel_order == 'RGB':
                px_order = driver.WS2811_STRIP_RGB
            elif led_pixel_order == 'RBG':
                px_order = driver.WS2811_STRIP_RBG
            elif led_pixel_order == 'GRB':
                px_order = driver.WS2811_STRIP_GRB
            elif led_pixel_order == 'GBR':
                px_order = driver.WS2811_STRIP_GBR
            elif led_pixel_order == 'BRG':
                px_order = driver.WS2811_STRIP_BRG
            elif led_pixel_order == 'BGR':
                px_order = driver.WS2811_STRIP_BGR
            elif led_pixel_order == 'RGBW':
                px_order = driver.SK6812_STRIP_RGBW
            elif led_pixel_order == 'RBGW':
                px_order = driver.SK6812_STRIP_RBGW
            elif led_pixel_order == 'GRBW':
                px_order = driver.SK6812_STRIP_GRBW
            elif led_pixel_order == 'GBRW':
                px_order = driver.SK6812_STRIP_GBRW
            elif led_pixel_order == 'BRGW':
                px_order = driver.SK6812_STRIP_BRGW
            elif led_pixel_order == 'BGRW':
                px_order = driver.SK6812_STRIP_BGRW

            self._has_white = 1 if 'W' in led_pixel_order else 0
            self._count = led_count

            self._leds = driver.new_ws2811_t()

            for i in range(2):
                chan = driver.ws2811_channel_get(self._leds, i)
                driver.ws2811_channel_t_count_set(chan, 0)
                driver.ws2811_channel_t_gpionum_set(chan, 0)
                driver.ws2811_channel_t_invert_set(chan, 0)
                driver.ws2811_channel_t_brightness_set(chan, 0)

            self._channel = driver.ws2811_channel_get(self._leds, 0)
            driver.ws2811_channel_t_gamma_set(self._channel, list(range(256)))
            driver.ws2811_channel_t_count_set(self._channel, led_count)
            driver.ws2811_channel_t_gpionum_set(self._channel, led_pin)
            driver.ws2811_channel_t_invert_set(self._channel, 0)
            driver.ws2811_channel_t_brightness_set(self._channel, 255)
            driver.ws2811_channel_t_strip_type_set(self._channel, px_order)

            driver.ws2811_t_freq_set(self._leds, led_data_rate)
            driver.ws2811_t_dmanum_set(self._leds, led_dma_channel)

            resp = driver.ws2811_init(self._leds)
            if resp != 0:
                str_resp = driver.ws2811_get_return_t_str(resp)
                raise RuntimeError(
                    'ws2811_init failed with code {0} ({1})'.format(resp, str_resp)
                )
        else:
            self._leds = None
            self._channel = None
            self._has_white = 0
            self._count = led_count

        self._where_hue = np.zeros((led_count * 3,), dtype=bool)
        self._where_hue[0::3] = True

        self._targets_serial = {}
        self._serial_error_targets = set()

        atexit.register(self._cleanup)

    def _cleanup(self):
        for target in list(self._targets_serial.values()):
            try:
                target.close()
            except Exception:
                pass
        self._targets_serial.clear()

        if driver.is_raspberrypi() and self._leds is not None:
            driver.delete_ws2811_t(self._leds)
            self._leds = None
            self._channel = None

    def set_range(self, pixels, start, end,
                  correction, saturation, brightness, color_mode,
                  render_mode, render_target):
        if render_mode == TargetMode.local:
            if driver.is_raspberrypi():
                if color_mode == animfunctions.ColorMode.hsv:
                    driver.ws2811_hsv_render_range_float(
                        self._channel,
                        pixels,
                        start,
                        end,
                        correction,
                        saturation,
                        brightness,
                        1.0,
                        self._has_white
                    )
                else:
                    driver.ws2811_rgb_render_range_float(
                        self._channel,
                        pixels,
                        start,
                        end,
                        correction,
                        saturation,
                        brightness,
                        1.0,
                        self._has_white
                    )
            return

        if render_mode != TargetMode.serial:
            return

        data = np.fromiter(itertools.chain.from_iterable(pixels), np.float32)
        if color_mode == animfunctions.ColorMode.hsv:
            np.fmod(data,
                    1.0,
                    where=self._where_hue[0:(end - start) * 3],
                    out=data)
            data = data * 255.0
        else:
            data = data * 255.0
            data = np.clip(data, 0.0, 255.0)
        data = data.astype(np.uint8)

        packet = (
            b'\x00'
            + (b'\x02' if color_mode == animfunctions.ColorMode.hsv else b'\x01')
            + int((end - start) * 3 + 13).to_bytes(2, 'big')
            + correction.to_bytes(3, 'big')
            + int(saturation * 255).to_bytes(1, 'big')
            + int(brightness * 255).to_bytes(1, 'big')
            + start.to_bytes(2, 'big')
            + end.to_bytes(2, 'big')
            + data.tobytes()
        )
        self._send_serial(packet, render_target)
        self._send_serial(b'\x00\x03\x00\x05\x00', render_target)

    def show_calibration_color(self, count, correction, brightness,
                               render_mode, render_target):
        if render_mode == TargetMode.local:
            if driver.is_raspberrypi():
                driver.ws2811_rgb_render_calibration(
                    self._leds,
                    self._channel,
                    self._count,
                    correction,
                    brightness
                )
            return

        if render_mode == TargetMode.serial:
            packet = (
                b'\x00\x00\x00\x08'
                + correction.to_bytes(3, 'big')
                + int(brightness * 255).to_bytes(1, 'big')
            )
            self._send_serial(packet, render_target)

    def render(self):
        if driver.is_raspberrypi():
            driver.ws2811_render(self._leds)

    def _open_serial_target(self, target):
        port = serial.Serial(
            target,
            115200,
            timeout=0.01,
            write_timeout=0.25
        )

        # Opening the serial port resets many Arduino Uno-compatible boards.
        # Wait for the bootloader/application to become ready so the first
        # frame (including static patterns) is not lost during the reset.
        time.sleep(2.0)
        self._targets_serial[target] = port
        return port

    def _send_serial(self, packet, target):
        if not target:
            return

        try:
            port = self._targets_serial.get(target)
            if port is None or not port.is_open:
                port = self._open_serial_target(target)

            port.write(packet)

            if target in self._serial_error_targets:
                print(f'Reconnected LED controller on {target}')
                self._serial_error_targets.remove(target)

        except Exception as exc:
            old_port = self._targets_serial.pop(target, None)
            if old_port is not None:
                try:
                    old_port.close()
                except Exception:
                    pass

            if target not in self._serial_error_targets:
                msg = ''.join(traceback.format_exception_only(type(exc), exc)).strip()
                print(f'LED controller serial error on {target}: {msg}')
                print('The port will be retried automatically on the next frame.')
                self._serial_error_targets.add(target)
