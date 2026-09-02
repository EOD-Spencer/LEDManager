/*
 * Arduino RGBW LED renderer for LED Controller.
 *
 * Receives the LED Manager serial rendering protocol at 115200 baud and
 * drives an SK6812 RGBW strip with Adafruit_NeoPixel.
 *
 * Copyright (c) 2025-2026 Cody Spencer
 * Released under the MIT License. See LICENSE in the repository root.
 */

#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

// Keep LED_COUNT in sync with the host --led_count value.
static const uint16_t LED_COUNT = 20;
static const uint8_t LED_PIN = 10;
static const uint32_t SERIAL_BAUD = 115200;
static const neoPixelType PIXEL_TYPE = NEO_GRBW + NEO_KHZ800;

static const uint8_t PACKET_START_BYTE = 0x00;

enum CommandType : uint8_t {
  CMD_CALIBRATION = 0,
  CMD_RENDER_RGB = 1,
  CMD_RENDER_HSV = 2,
  CMD_WRITE_LEDS = 3,
  CMD_TYPE_MAX
};

// A render packet contains 3 bytes per logical pixel plus a small header.
static const uint16_t PACKET_BUFFER_SIZE = LED_COUNT * 3 + 64;

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, PIXEL_TYPE);
uint8_t packetBuffer[PACKET_BUFFER_SIZE];
uint16_t packetIndex = 0;
uint16_t packetLength = 0;

static uint8_t scale8(uint8_t a, uint8_t b) {
  return ((uint16_t)a * (uint16_t)b) >> 8;
}

static uint32_t makeColor(uint8_t r, uint8_t g, uint8_t b, uint8_t w) {
  return strip.Color(r, g, b, w);
}

static uint32_t renderRgb(uint8_t r, uint8_t g, uint8_t b,
                          uint8_t corrR, uint8_t corrG, uint8_t corrB,
                          uint8_t saturation, uint8_t brightness) {
  uint8_t w = 0;

  // Match the RGB -> RGBW behavior used by the original LED Manager firmware.
  uint8_t maxValue = max(r, max(g, b));
  uint8_t minValue = 0;

  if (saturation == 0) {
    r = 0;
    g = 0;
    b = 0;
    minValue = maxValue;
  } else {
    int16_t rr = (int16_t)r - ((uint16_t)maxValue * saturation / 255) + maxValue;
    int16_t gg = (int16_t)g - ((uint16_t)maxValue * saturation / 255) + maxValue;
    int16_t bb = (int16_t)b - ((uint16_t)maxValue * saturation / 255) + maxValue;

    r = constrain(rr, 0, 255);
    g = constrain(gg, 0, 255);
    b = constrain(bb, 0, 255);

    minValue = min(r, min(g, b));
    r -= minValue;
    g -= minValue;
    b -= minValue;
  }

  w = scale8(minValue, minValue);

  r = ((uint32_t)r * brightness * corrR) >> 16;
  g = ((uint32_t)g * brightness * corrG) >> 16;
  b = ((uint32_t)b * brightness * corrB) >> 16;
  w = scale8(w, brightness);

  return makeColor(r, g, b, w);
}

static uint32_t renderHsv(uint8_t h, uint8_t s, uint8_t v,
                          uint8_t corrR, uint8_t corrG, uint8_t corrB,
                          uint8_t saturation, uint8_t brightness) {
  uint8_t hue = h;
  uint8_t sat = scale8(s, saturation);
  uint8_t val = scale8(v, v);
  if (val > 0 && val < 255) {
    val++;
  }
  val = scale8(val, brightness);

  uint8_t r = 0;
  uint8_t g = 0;
  uint8_t b = 0;
  uint8_t w = 0;

  uint8_t offset = hue & 0x1F;
  uint8_t offset8 = offset << 3;
  uint8_t third = offset8 / 3;

  if (!(hue & 0x80)) {
    if (!(hue & 0x40)) {
      if (!(hue & 0x20)) {
        r = 255 - third;
        g = third;
      } else {
        r = 171;
        g = 85 + third;
      }
    } else {
      if (!(hue & 0x20)) {
        r = 171 - third * 2;
        g = 170 + third;
      } else {
        g = 255 - third;
        b = third;
      }
    }
  } else {
    if (!(hue & 0x40)) {
      if (!(hue & 0x20)) {
        uint8_t twoThirds = third * 2;
        g = 171 - twoThirds;
        b = 85 + twoThirds;
      } else {
        r = third;
        b = 255 - third;
      }
    } else {
      if (!(hue & 0x20)) {
        r = 85 + third;
        b = 171 - third;
      } else {
        r = 170 + third;
        b = 85 - third;
      }
    }
  }

  if (sat != 255) {
    if (sat == 0) {
      r = 0;
      g = 0;
      b = 0;
      w = 255;
    } else {
      uint8_t desat = 255 - sat;
      desat = scale8(desat, desat);
      r = scale8(r, sat);
      g = scale8(g, sat);
      b = scale8(b, sat);
      w = desat;
    }
  }

  if (val != 255) {
    if (val == 0) {
      r = g = b = w = 0;
    } else {
      r = scale8(r, val);
      g = scale8(g, val);
      b = scale8(b, val);
      w = scale8(w, val);
    }
  }

  r = scale8(r, corrR);
  g = scale8(g, corrG);
  b = scale8(b, corrB);

  return makeColor(r, g, b, w);
}

static void showCalibrationColor(uint8_t corrR, uint8_t corrG,
                                 uint8_t corrB, uint8_t brightness) {
  uint8_t r = scale8(corrR, brightness);
  uint8_t g = scale8(corrG, brightness);
  uint8_t b = scale8(corrB, brightness);
  uint32_t color = makeColor(r, g, b, 0);

  for (uint16_t i = 0; i < LED_COUNT; i++) {
    strip.setPixelColor(i, color);
  }
  strip.show();
}

static void handlePacket() {
  if (packetLength < 4 || packetBuffer[0] != PACKET_START_BYTE) {
    return;
  }

  uint8_t command = packetBuffer[1];

  if (command == CMD_CALIBRATION) {
    if (packetLength >= 8) {
      showCalibrationColor(packetBuffer[4], packetBuffer[5],
                           packetBuffer[6], packetBuffer[7]);
    }
    return;
  }

  if (command == CMD_WRITE_LEDS) {
    strip.show();
    return;
  }

  if (command != CMD_RENDER_RGB && command != CMD_RENDER_HSV) {
    return;
  }

  if (packetLength < 13) {
    return;
  }

  uint16_t start = ((uint16_t)packetBuffer[9] << 8) | packetBuffer[10];
  uint16_t end = ((uint16_t)packetBuffer[11] << 8) | packetBuffer[12];

  start = min(start, LED_COUNT);
  end = min(end, LED_COUNT);
  if (start >= end) {
    return;
  }

  uint16_t expectedLength = 13 + (end - start) * 3;
  if (packetLength < expectedLength) {
    return;
  }

  const uint8_t corrR = packetBuffer[4];
  const uint8_t corrG = packetBuffer[5];
  const uint8_t corrB = packetBuffer[6];
  const uint8_t saturation = packetBuffer[7];
  const uint8_t brightness = packetBuffer[8];

  for (uint16_t i = start; i < end; i++) {
    uint16_t pos = (i - start) * 3 + 13;
    uint32_t color;

    if (command == CMD_RENDER_RGB) {
      color = renderRgb(packetBuffer[pos], packetBuffer[pos + 1],
                        packetBuffer[pos + 2], corrR, corrG, corrB,
                        saturation, brightness);
    } else {
      color = renderHsv(packetBuffer[pos], packetBuffer[pos + 1],
                        packetBuffer[pos + 2], corrR, corrG, corrB,
                        saturation, brightness);
    }

    strip.setPixelColor(i, color);
  }
}

static void resetPacketParser() {
  packetIndex = 0;
  packetLength = 0;
}

static void consumeSerialByte(uint8_t value) {
  if (packetIndex == 0) {
    if (value == PACKET_START_BYTE) {
      packetBuffer[packetIndex++] = value;
    }
    return;
  }

  if (packetIndex >= PACKET_BUFFER_SIZE) {
    resetPacketParser();
    return;
  }

  packetBuffer[packetIndex++] = value;

  if (packetIndex == 2) {
    if (packetBuffer[1] >= CMD_TYPE_MAX) {
      resetPacketParser();
    }
    return;
  }

  if (packetIndex == 4) {
    packetLength = ((uint16_t)packetBuffer[2] << 8) | packetBuffer[3];
    if (packetLength < 4 || packetLength > PACKET_BUFFER_SIZE) {
      resetPacketParser();
      return;
    }
  }

  if (packetLength > 0 && packetIndex == packetLength) {
    handlePacket();
    resetPacketParser();
  }
}

void setup() {
  strip.begin();
  strip.clear();
  strip.show();

  Serial.begin(SERIAL_BAUD);
}

void loop() {
  while (Serial.available() > 0) {
    consumeSerialByte((uint8_t)Serial.read());
  }
}
