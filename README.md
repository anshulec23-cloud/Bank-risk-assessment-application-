# CyberRisk Intelligence Platform
### Cognizant Technoverse Hackathon 2026

> Real-time ICS cyberattack detection + financial blast-radius quantification  
> powered by a 5-agent LangGraph pipeline, Random Forest anomaly detection, and GenAI reporting.

---

## Architecture

```
MQTT Telemetry (ICS Devices / Simulator)
          │
          ▼
  [Agent 1: Detector]        — Random Forest anomaly score
          │ anomaly detected?
          ▼
  [Agent 2: Classifier]      — Rules + LLM → attack type, severity, plain-English explanation
          │
          ▼
  [Agent 3: Isolator]        — Micro-segmentation decision, MQTT isolation command
          │
          ▼
  [Agent 4: Risk Quantifier] — Downtime cost + SLA penalty + regulatory fine + credit flag
          │
          ▼
  [Agent 5: Reporter]        — NIST SP 800-61 report + Bank credit risk brief (LLM)
          │
          ▼
  FastAPI + WebSocket ──────► React Dashboard (live)
          │
          ▼
      SQLite DB
```

## Stack

| Layer       | Technology                              |
|-------------|------------------------------------------|
| Agents      | LangGraph + LangChain                    |
| ML Model    | scikit-learn Random Forest               |
| LLM         | Ollama (Qwen3 4B) via local network      |
| Backend     | FastAPI + SQLAlchemy + WebSockets        |
| Broker      | Eclipse Mosquitto (MQTT)                 |
| Database    | SQLite (swap to PostgreSQL for prod)     |
| Frontend    | React + Recharts + Tailwind CSS          |
| Containers  | Docker + Docker Compose                  |

---

## Quick Start (Local — No Docker)

### Prerequisites
- Python 3.11+
- Node 20+
- Mosquitto MQTT broker running on localhost:1883
- Ollama running on 192.168.1.4:11434 with qwen3:4b pulled

### 1. Backend

```bash
cd backend
pip install -r requirements.txt

# Train the RF model (one-time)
python -m ml.model

# Seed devices into DB
python ../scripts/seed_devices.py

# Start API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### 3. Simulator (in a new terminal)

```bash
cd backend

# Normal telemetry
python -m mqtt.simulator

# Inject DoS attack on device-01
python -m mqtt.simulator --attack DoS --device device-01

# Inject Physical Tamper
python -m mqtt.simulator --attack PhysicalTamper --device device-02
```

---

## Quick Start (Docker)

```bash
cp .env.example .env
# Edit .env — set OLLAMA_BASE_URL to your machine's IP

docker compose up -d                  # broker + backend + frontend
docker compose --profile sim up -d   # also start simulator
```

Dashboard: http://localhost:5173  
API docs:   http://localhost:8000/docs

---

## Project Structure

```
cyberrisk-platform/
├── backend/
│   ├── core/
│   │   ├── config.py          # All settings via pydantic-settings
│   │   └── llm.py             # Async Ollama wrapper
│   ├── db/
│   │   ├── database.py        # SQLAlchemy engine + session
│   │   └── models.py          # Device, TelemetryEvent, Incident tables
│   ├── ml/
│   │   ├── data_gen.py        # Synthetic ICS training data generator
│   │   ├── model.py           # Random Forest train + inference
│   │   └── artifacts/         # Saved model (gitignored)
│   ├── mqtt/
│   │   ├── broker.py          # Async MQTT listener
│   │   └── simulator.py       # 3-device ICS simulator with attack injection
│   ├── agents/
│   │   ├── detector.py        # Agent 1 — RF anomaly detection
│   │   ├── classifier.py      # Agent 2 — attack type + LLM explanation
│   │   ├── isolator.py        # Agent 3 — micro-segmentation
│   │   ├── risk_quantifier.py # Agent 4 — financial blast radius
│   │   └── reporter.py        # Agent 5 — NIST report + credit brief
│   ├── pipeline/
│   │   ├── state.py           # LangGraph TypedDict state schema
│   │   └── graph.py           # Compiled LangGraph DAG
│   ├── api/
│   │   ├── main.py            # FastAPI app, WebSocket, MQTT integration
│   │   └── routes/
│   │       ├── devices.py
│   │       ├── incidents.py
│   │       ├── telemetry.py
│   │       └── reports.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx             # Main app — tabs, data fetching, WS integration
│       ├── hooks/
│       │   └── useWebSocket.js # Auto-reconnecting WebSocket hook
│       ├── api/
│       │   └── client.js       # Axios API client
│       └── components/
│           ├── StatusBar.jsx   # Live connection + event ticker
│           ├── MetricCard.jsx  # KPI card
│           ├── DeviceGrid.jsx  # Device cards with sensors + isolate button
│           ├── IncidentFeed.jsx# Incident list + NIST/credit report viewer
│           ├── TelemetryChart.jsx # Recharts line chart per sensor
│           └── FinancialRisk.jsx  # Exposure breakdown + credit flag
├── scripts/
│   └── seed_devices.py
├── docker-compose.yml
├── mosquitto.conf
└── .env.example
```

---

## API Reference

| Method | Endpoint                          | Description                        |
|--------|-----------------------------------|------------------------------------|
| GET    | /api/devices/                     | List all devices                   |
| POST   | /api/devices/{id}/isolate         | Manually isolate device            |
| POST   | /api/devices/{id}/restore         | Restore device network access      |
| GET    | /api/incidents/                   | List incidents (filterable)        |
| GET    | /api/incidents/summary            | KPI summary                        |
| PATCH  | /api/incidents/{id}/resolve       | Mark incident resolved             |
| GET    | /api/telemetry/latest             | Latest reading per device          |
| GET    | /api/telemetry/stats              | Anomaly rate + avg score           |
| GET    | /api/reports/{id}/nist            | NIST SP 800-61 incident report     |
| GET    | /api/reports/{id}/credit-brief    | Bank credit risk brief             |
| WS     | /ws                               | Live telemetry + incident stream   |

---

## Attack Types Simulated

| Attack          | Signature                                          |
|-----------------|----------------------------------------------------|
| DoS             | Temperature spike + pressure surge + flow drop     |
| Spoofing        | Suspiciously flat/static sensor values             |
| Replay          | Normal values but voltage anomaly                  |
| PhysicalTamper  | Extreme temp + pressure + near-zero flow           |
| MitM            | Mixed anomalous signals                            |

---

## Financial Risk Model

```
Downtime Cost    = hourly_cost[device_type] × downtime_hours[severity]
SLA Penalty      = Downtime Cost × 15%
Regulatory Fine  = Lookup by severity (NERC CIP scale)
Total Exposure   = Sum of above three

Credit Risk Flag:
  < $50K       → NORMAL
  $50K–$500K   → ELEVATED
  $500K–$2M    → HIGH
  > $2M        → CRITICAL
```

---

## Novel Contributions (arXiv-aligned)

1. **Device-side policy engine** — ICS devices reject malicious server commands independently, even if the central server is compromised. Zero-trust extension to resource-constrained hardware.

2. **Cyber-to-financial bridge** — First pipeline to translate OT security telemetry anomalies into real-time structured financial exposure metrics consumable by lending institutions.

