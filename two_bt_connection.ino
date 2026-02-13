#include <SoftwareSerial.h>

SoftwareSerial mySerial(10, 11);  // RX, TX

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
  Serial.println("Receiver Ready...");
}

void loop() {

  // Read incoming message from sender Arduino
  if (mySerial.available()) {
    String receivedData = mySerial.readStringUntil('\n');
    receivedData.trim();   // remove noise like \r and spaces

    if (receivedData.length() > 0) {
      Serial.print("Rx Msg: ");
      Serial.println(receivedData);
    }
  }

  // Optional: User can type something to test reverse communication
  if (Serial.available()) {
    String userMessage = Serial.readStringUntil('\n');
    userMessage.trim();

    if (userMessage.length() > 0) {
      mySerial.println(userMessage);
      Serial.print("Echoed: ");
      Serial.println(userMessage);
    }
  }
}
