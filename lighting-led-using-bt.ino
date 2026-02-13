#include <SoftwareSerial.h>
SoftwareSerial bt(10, 11); // RX, TX
const int buttonPin = 2;
bool ledState = false;     // Stores ON/OFF state
bool lastButtonState = HIGH;
void setup() {
  pinMode(buttonPin, INPUT_PULLUP);
  Serial.begin(9600);   // USB Serial Monitor
  bt.begin(9600);       // HC-05 DATA mode
  Serial.println("MASTER READY - TOGGLE MODE");
}
void loop() {
  bool buttonState = digitalRead(buttonPin);
  // Detect button press (edge detection)
  if (lastButtonState == HIGH && buttonState == LOW) {
    ledState = !ledState;   // TOGGLE state
    if (ledState) {
      bt.write('1');
      Serial.println("Sent: 1 (LED ON)");
    } else {
      bt.write('0');
      Serial.println("Sent: 0 (LED OFF)");
    }
    delay(250);  // Debounce delay
  }
  lastButtonState = buttonState;
}