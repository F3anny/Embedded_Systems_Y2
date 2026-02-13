import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mqtt_client import MQTTClient  # your existing MQTT helper

# ==============================
# CONFIG
# ==============================
MQTT_BROKER = "157.173.101.159"
MQTT_PORT = 1883

# ==============================
# FASTAPI INIT
# ==============================
app = FastAPI()
connected_clients = set()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# REQUEST MODEL
# ==============================
class TopUpRequest(BaseModel):
    uid: str
    amount: int

# ==============================
# WEBSOCKET BROADCAST
# ==============================
async def broadcast(message: dict):
    disconnected = []
    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.append(client)

    for client in disconnected:
        connected_clients.remove(client)

# ==============================
# WEBSOCKET ENDPOINT
# ==============================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    print("WebSocket client connected")
    try:
        while True:
            await websocket.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print("WebSocket client disconnected")

# ==============================
# MQTT CALLBACK
# ==============================
def mqtt_message_handler(topic: str, payload: dict):
    """
    Called from MQTT thread.
    Forwards updates to WebSocket clients.
    """
    asyncio.run_coroutine_threadsafe(
        broadcast({"topic": topic, "data": payload}),
        loop
    )

# ==============================
# STARTUP
# ==============================
@app.on_event("startup")
async def startup_event():
    global mqtt_client, loop
    loop = asyncio.get_event_loop()

    mqtt_client = MQTTClient(
        broker_host=MQTT_BROKER,
        broker_port=MQTT_PORT,
        message_callback=mqtt_message_handler
    )
    mqtt_client.start()
    print("Backend started")

# ==============================
# TOP-UP ENDPOINT
# ==============================
@app.post("/topup")
async def topup(request: TopUpRequest):
    if request.amount <= 0:
        return {"error": "Amount must be positive"}

    # Publish to MQTT
    mqtt_client.publish_topup(request.uid, request.amount)

    # Optimistic WebSocket broadcast
    asyncio.create_task(
        broadcast({"topic": f"rfid/{request.uid}/card/topup",
                   "data": {"uid": request.uid, "new_balance": None}})
    )

    return {"status": "Top-up sent", "uid": request.uid, "amount": request.amount}