#include <SoftwareSerial.h>
SoftwareSerial bt(10, 11); // RX, TX
void setup(){
 Serial.begin(38400); // Hardware Serial
 bt.begin(38400); //Software Serial
}
void loop(){
 if(Serial.available()){
   bt.write(Serial.read()); //send user input to BT
 }

 if(bt.available()){
  Serial.print(bt.readString()); //print response from BT
 }
}