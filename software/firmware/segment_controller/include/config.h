#pragma once
// Per-segment configuration. Copy/adjust these values for each PCB
// (base, wrist, ...). All angles are in degrees.

#include <stdint.h>

// ---- I2C bus ----
static const int I2C_SDA = 21;   // ESP32 default
static const int I2C_SCL = 22;
static const uint32_t I2C_HZ = 400000;

// ---- Devices ----
static const uint8_t PCA9685_ADDR = 0x40;
static const uint8_t TCA9548_ADDR = 0x70;
static const uint8_t AS5600_ADDR  = 0x36;  // fixed -> needs the mux
static const int PWM_FREQ_HZ = 50;

// ---- Axes on THIS segment ----
// Each axis pairs one servo (PCA9685 channel) with one encoder
// (TCA9548A channel). Order defines the axis index used on serial.
static const int NUM_AXES = 3;   // e.g. base: joints 1,2,3

struct AxisConfig {
  const char* name;
  uint8_t servo_channel;   // PCA9685 output channel
  uint8_t mux_channel;     // TCA9548A channel the AS5600 is on
  float servo_min_angle;   // servo mechanical extremes...
  float servo_max_angle;
  uint16_t pulse_min_us;   // ...at these pulse widths
  uint16_t pulse_max_us;
  float encoder_offset;    // deg subtracted so home reads ~0
  bool  encoder_invert;    // flip encoder direction if needed
};

// NOTE: placeholder wiring — set these from your PCB layout & calibration.
static const AxisConfig AXES[NUM_AXES] = {
  // name          servo mux  smin  smax   pmin  pmax  offset invert
  { "joint1",        0,   0,   0.f, 180.f,  500,  2500,  0.f,  false },
  { "joint2",        1,   1,   0.f, 180.f,  500,  2500,  0.f,  false },
  { "joint3",        2,   2,   0.f, 270.f,  500,  2500,  0.f,  false },
};
