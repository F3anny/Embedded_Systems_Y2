# RFID Top‑Up Dashboard

⚡ A real‑time web dashboard for topping up RFID card balances with backend API and MQTT integration.

🔗 Live Demo: http://157.173.101.159:9231/  

---

## 📌 Project Overview

This project is a **real‑time RFID Top‑Up System** that allows users to scan RFID cards and immediately update their balances via a dashboard. It uses:

- An ESP8266/IoT device to read RFID cards and publish card status over MQTT
- A backend FastAPI service that receives top‑up requests and communicates with MQTT
- A real‑time WebSocket connection to update the dashboard instantly
- A clean web dashboard UI showing card balances live

This solution is ideal for cashless systems (cafeterias, labs, access control, etc.) that need real‑time updates and low latency.

---

## 🚀 Features

✔ Real‑time balance updates over WebSocket  
✔ HTTP API for sending top‑up requests  
✔ MQTT message broker for device backend communication  
✔ Responsive dashboard UI  
✔ Scalable and modular architecture

---

## 🧠 Architecture

The system connects various components in a structured flow:

