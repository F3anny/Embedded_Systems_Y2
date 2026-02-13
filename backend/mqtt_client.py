import json
import threading
import paho.mqtt.client as mqtt

TEAM_ID = "code888"
BASE_TOPIC = f"rfid/{TEAM_ID}"

STATUS_TOPIC = f"{BASE_TOPIC}/card/status"
BALANCE_TOPIC = f"{BASE_TOPIC}/card/balance"
TOPUP_TOPIC = f"{BASE_TOPIC}/card/topup"

class MQTTClient:
    def __init__(self, broker_host: str, broker_port: int, message_callback):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.message_callback = message_callback

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def start(self):
        self.client.connect(self.broker_host, self.broker_port, 60)
        thread = threading.Thread(target=self.client.loop_forever)
        thread.daemon = True
        thread.start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker")
            client.subscribe(STATUS_TOPIC)
            client.subscribe(BALANCE_TOPIC)
            print("📡 Subscribed to:")
            print("   ", STATUS_TOPIC)
            print("   ", BALANCE_TOPIC)
        else:
            print("MQTT Connection failed with code:", rc)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            print(f"MQTT Message from {msg.topic}: {payload}")
            self.message_callback(msg.topic, payload)
        except Exception as e:
            print("Error processing MQTT message:", e)

    def publish_topup(self, uid: str, amount: int):
        payload = {
            "uid": uid,
            "amount": amount
        }

        self.client.publish(TOPUP_TOPIC, json.dumps(payload))
        print(f"published topup to {TOPUP_TOPIC}: {payload}")