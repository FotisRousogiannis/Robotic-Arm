// Per-segment ESP32 controller for the robotic arm.
//
// Local stack on one PCB:
//   * PCA9685  -> servo PWM (open-loop angle command)
//   * TCA9548A -> selects one AS5600 magnetic encoder at a time
//   * AS5600   -> true joint angle feedback (0..360 deg)
//
// Comms: a simple line-based SERIAL protocol over USB (115200 baud), so
// you can test the wrist and gearboxes immediately. The higher-level
// host link (micro-ROS / WiFi / serial-to-ROS bridge) can be layered on
// top later without changing the local control below.
//
// Serial commands (newline-terminated):
//   P <axis> <deg>     set target angle for one axis (open-loop servo)
//   H                  home all axes (servo center)
//   E                  print all encoder angles (deg)
//   M <a> <b> <p> <r>  differential mix test: two servo channels a,b
//                      from pitch p and roll r (deg)
//   R <axis>           release one axis servo (stop PWM)
//   ?                  print segment info
//
// Everything here is CALIBRATABLE via include/config.h — the wiring and
// limits are placeholders until measured on the real PCB.

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include "config.h"

Adafruit_PWMServoDriver pca(PCA9685_ADDR);

// ---- TCA9548A: select exactly one downstream channel ----
static void muxSelect(uint8_t channel) {
  Wire.beginTransmission(TCA9548_ADDR);
  Wire.write(1 << channel);
  Wire.endTransmission();
}

// ---- AS5600: read raw angle (0..4095) on the currently selected mux ch ----
static bool as5600ReadRaw(uint16_t& out) {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(0x0C);  // RAW ANGLE high register
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((int)AS5600_ADDR, 2) != 2) return false;
  uint16_t hi = Wire.read();
  uint16_t lo = Wire.read();
  out = ((hi << 8) | lo) & 0x0FFF;
  return true;
}

// Encoder angle for an axis, in degrees, offset/invert applied.
static bool readAxisAngle(int axis, float& deg) {
  const AxisConfig& a = AXES[axis];
  muxSelect(a.mux_channel);
  uint16_t raw;
  if (!as5600ReadRaw(raw)) return false;
  float angle = raw * (360.0f / 4096.0f);
  if (a.encoder_invert) angle = 360.0f - angle;
  angle -= a.encoder_offset;
  deg = angle;
  return true;
}

// ---- PCA9685: command a servo channel to an angle ----
static uint16_t usToTicks(float us) {
  // 12-bit resolution over the PWM period (1e6/freq microseconds).
  float period_us = 1000000.0f / PWM_FREQ_HZ;
  float ticks = (us / period_us) * 4096.0f;
  if (ticks < 0) ticks = 0;
  if (ticks > 4095) ticks = 4095;
  return (uint16_t)ticks;
}

static void setServoAngle(uint8_t channel, float angle,
                          float amin, float amax,
                          uint16_t pmin, uint16_t pmax) {
  if (angle < amin) angle = amin;
  if (angle > amax) angle = amax;
  float frac = (amax > amin) ? (angle - amin) / (amax - amin) : 0.0f;
  float us = pmin + frac * (pmax - pmin);
  pca.setPWM(channel, 0, usToTicks(us));
}

static void setAxis(int axis, float angle) {
  const AxisConfig& a = AXES[axis];
  setServoAngle(a.servo_channel, angle, a.servo_min_angle, a.servo_max_angle,
                a.pulse_min_us, a.pulse_max_us);
}

// ---- Serial command handling ----
static void printInfo() {
  Serial.print(F("segment="));
#ifdef SEGMENT_NAME
  Serial.print(F(SEGMENT_NAME));
#else
  Serial.print(F("unknown"));
#endif
  Serial.print(F(" axes="));
  Serial.println(NUM_AXES);
  for (int i = 0; i < NUM_AXES; i++) {
    Serial.printf("  [%d] %s servo=ch%u enc=mux%u range=%.0f..%.0f\n",
                  i, AXES[i].name, AXES[i].servo_channel, AXES[i].mux_channel,
                  AXES[i].servo_min_angle, AXES[i].servo_max_angle);
  }
}

static void handleLine(char* line) {
  char cmd = line[0];
  switch (cmd) {
    case 'P': {  // P <axis> <deg>
      int axis; float deg;
      if (sscanf(line + 1, "%d %f", &axis, &deg) == 2 &&
          axis >= 0 && axis < NUM_AXES) {
        setAxis(axis, deg);
        Serial.printf("OK P %d %.1f\n", axis, deg);
      } else Serial.println(F("ERR P <axis> <deg>"));
      break;
    }
    case 'H': {  // home all (center of each servo range)
      for (int i = 0; i < NUM_AXES; i++)
        setAxis(i, (AXES[i].servo_min_angle + AXES[i].servo_max_angle) * 0.5f);
      Serial.println(F("OK H"));
      break;
    }
    case 'E': {  // read all encoders
      for (int i = 0; i < NUM_AXES; i++) {
        float d;
        if (readAxisAngle(i, d)) Serial.printf("ENC %d %.2f\n", i, d);
        else Serial.printf("ENC %d ERR\n", i);
      }
      break;
    }
    case 'M': {  // differential mix test: M <a> <b> <pitch> <roll>
      int ca, cb; float pitch, roll;
      if (sscanf(line + 1, "%d %d %f %f", &ca, &cb, &pitch, &roll) == 4) {
        // Uses joint3-like 270deg servos centered at 135 by default.
        float center = 135.0f;
        setServoAngle(ca, center + pitch + roll, 0, 270, 500, 2500);
        setServoAngle(cb, center + pitch - roll, 0, 270, 500, 2500);
        Serial.printf("OK M a=%d b=%d p=%.1f r=%.1f\n", ca, cb, pitch, roll);
      } else Serial.println(F("ERR M <a> <b> <pitch> <roll>"));
      break;
    }
    case 'R': {  // release one axis
      int axis;
      if (sscanf(line + 1, "%d", &axis) == 1 && axis >= 0 && axis < NUM_AXES) {
        pca.setPWM(AXES[axis].servo_channel, 0, 0);
        Serial.printf("OK R %d\n", axis);
      } else Serial.println(F("ERR R <axis>"));
      break;
    }
    case '?': printInfo(); break;
    case '\0': break;
    default: Serial.println(F("ERR unknown cmd (P H E M R ?)"));
  }
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Wire.begin(I2C_SDA, I2C_SCL, I2C_HZ);
  pca.begin();
  pca.setPWMFreq(PWM_FREQ_HZ);
  Serial.println(F("segment_controller ready"));
  printInfo();
}

void loop() {
  static char buf[64];
  static uint8_t n = 0;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      buf[n] = '\0';
      if (n > 0) handleLine(buf);
      n = 0;
    } else if (n < sizeof(buf) - 1) {
      buf[n++] = c;
    }
  }
}
