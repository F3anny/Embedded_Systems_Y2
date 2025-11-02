import serial,time;
ser=serial.Serial('COM9',9600,timeout=1)
while True:
    ser.write(b'ping\n') #optional heartbeat
    print(ser.readline().strip())
    time.sleep(2)