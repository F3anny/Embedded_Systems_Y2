#include <Wire.h>

// MPU6050 I2C address
#define MPU_ADDR 0x68

// MPU6050 registers
#define REG_PWR_MGMT_1 0x6B
#define REG_ACCEL_XOUT_H 0x3B
#define REG_GYRO_XOUT_H 0x43

// Sensitivities
const float ACCEL_SENS = 16384.0; // LSB/g
const float GYRO_SENS  = 131.0;   // LSB/(°/s)

// Complementary filter factor
const float alpha = 0.98;

// Global angles
float roll = 0, pitch = 0, yaw = 0;

// Gyro bias
float gx_bias = 0, gy_bias = 0, gz_bias = 0;

// Time tracking
unsigned long lastMicros = 0;

// Read a 16-bit value from MPU6050
int16_t read16(int reg) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 2, true);
  return (Wire.read() << 8) | Wire.read();
}

// Read accelerometer and gyro values
void readMPU(float &ax, float &ay, float &az, float &gx, float &gy, float &gz) {
  int16_t rawAX = read16(REG_ACCEL_XOUT_H);
  int16_t rawAY = read16(REG_ACCEL_XOUT_H + 2);
  int16_t rawAZ = read16(REG_ACCEL_XOUT_H + 4);
  int16_t rawGX = read16(REG_GYRO_XOUT_H);
  int16_t rawGY = read16(REG_GYRO_XOUT_H + 2);
  int16_t rawGZ = read16(REG_GYRO_XOUT_H + 4);

  ax = rawAX / ACCEL_SENS;
  ay = rawAY / ACCEL_SENS;
  az = rawAZ / ACCEL_SENS;

  gx = rawGX / GYRO_SENS - gx_bias;
  gy = rawGY / GYRO_SENS - gy_bias;
  gz = rawGZ / GYRO_SENS - gz_bias;
}

// Calibrate gyro
void calibrateGyro(int samples = 500) {
  long sumX = 0, sumY = 0, sumZ = 0;
  for (int i = 0; i < samples; i++) {
    sumX += read16(REG_GYRO_XOUT_H);
    sumY += read16(REG_GYRO_XOUT_H + 2);
    sumZ += read16(REG_GYRO_XOUT_H + 4);
    delay(2);
  }
  gx_bias = sumX / (float)samples / GYRO_SENS;
  gy_bias = sumY / (float)samples / GYRO_SENS;
  gz_bias = sumZ / (float)samples / GYRO_SENS;
}

void setup() {
  Serial.begin(230400);  // Match Python baud rate
  Wire.begin();

  // Wake up MPU6050
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(REG_PWR_MGMT_1);
  Wire.write(0x00);
  Wire.endTransmission(true);
  delay(100);

  calibrateGyro(600);

  float ax, ay, az, gx, gy, gz;
  readMPU(ax, ay, az, gx, gy, gz);

  // Initial angles
  roll  = atan2(ay, az) * 180.0 / PI;
  pitch = atan2(-ax, sqrt(ay * ay + az * az)) * 180.0 / PI;
  yaw   = 0;  // start yaw at 0

  lastMicros = micros();
  Serial.println("START");
}

void loop() {
  float ax, ay, az, gx, gy, gz;
  readMPU(ax, ay, az, gx, gy, gz);

  unsigned long now = micros();
  float dt = (now - lastMicros) / 1e6;
  lastMicros = now;

  // Accelerometer angles
  float acc_roll  = atan2(ay, az) * 180.0 / PI;
  float acc_pitch = atan2(-ax, sqrt(ay * ay + az * az)) * 180.0 / PI;

  // Complementary filter
  roll  = alpha * (roll  + gx * dt) + (1 - alpha) * acc_roll;
  pitch = alpha * (pitch + gy * dt) + (1 - alpha) * acc_pitch;

  // Yaw from gyro integration
  yaw += gz * dt;

  // Normalize yaw
  if (yaw > 180) yaw -= 360;
  if (yaw < -180) yaw += 360;

  // Send CSV: pitch, roll, yaw
  Serial.print(pitch, 2); Serial.print(",");
  Serial.print(roll, 2); Serial.print(",");
  Serial.println(yaw, 2);

  delay(8); // ~100 Hz
}
