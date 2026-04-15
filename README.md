# ESG Intelligence Platform

Enterprise-grade, multi-agent ESG analytics platform for operational monitoring, financial risk scoring, compliance audit, final risk summarization, and explainable AI output.

This repository provides a production-friendly backend service built with FastAPI plus a Streamlit dashboard for business users.

## Table of Contents

1. Executive Summary
2. Core Architecture and Innovations
3. System Design
4. Technology Stack
5. Installation and Operation
6. API Endpoints
7. Data and Output Lifecycle
8. Folder Structure
9. Deployment
10. Security and Governance Notes
11. Troubleshooting

## Executive Summary

The ESG Intelligence Platform addresses a common enterprise gap: ESG reporting is often retrospective, manual, and disconnected from real operational signals. This system introduces an automated, pipeline-driven architecture where specialized agents process ESG and financial signals in sequence and generate actionable outputs.

Key outcomes:

- Standardized ESG dataset generation from MongoDB
- Automated compliance evaluation across E, S, and G dimensions
- Deterministic risk scoring and alerting
- Explainability layer using SHAP for model-level transparency
- API-first integration model for dashboards and enterprise systems

## Core Architecture and Innovations

### 1. Multi-Agent Processing Architecture

The platform implements modular agents with clear responsibilities:

- Agent 1: Data extraction and normalization from MongoDB to standardized CSV
- Agent 2: ESG aggregation and financial risk feature enrichment
- Agent 3: Rule-based compliance audit (E, S, G and governance checks)
- Agent 4: Final risk score and alert classification
- Agent 5: Explainability using SHAP on trained model features
- Agent 1 Premium: Background premium data streaming with Socket.IO events

### 2. Company-Scoped Output Routing

Outputs are generated in company-specific paths using environment-driven firm identification, enabling tenant-like separation for enterprise deployments.

### 3. Operational Bootstrap Logic

Agent 2 can automatically trigger Agent 1 if prerequisite data is missing. This reduces operational friction and supports resilient execution flows.

### 4. Explainability-First Risk Layer

Agent 5 does not only score risk; it surfaces top risk drivers through SHAP-based contribution summaries for audit and board-level reporting.

## System Design

### Logical Components

- API Layer: FastAPI routers exposing each agent capability
- Processing Layer: Python agent modules under agents/
- Data Layer: MongoDB source plus generated CSV outputs
- Model Layer: Serialized model artifact under models/
- Visualization Layer: Streamlit dashboard under dashboard/
- Realtime Layer: Socket.IO server for premium stream callbacks

### Processing Flow

1. Agent 1 synchronizes and standardizes source records
2. Agent 2 computes ESG and financial risk metrics
3. Agent 3 evaluates compliance status
4. Agent 4 calculates final risk score and alert level
5. Agent 5 generates top risk factor explanation

### Data Contract Highlights

Core expected fields include:

- Year
- Industry_Type
- E_Score
- S_Score
- G_Score
- ROA
- ROE
- Net Profit Margin
- Board_Independence (optional)

## Technology Stack

### Backend and API

- Python 3.11+
- FastAPI
- Uvicorn
- python-socketio

### Data and ML

- pandas
- scikit-learn
- joblib
- shap
- pymongo

### Dashboard and Docs

- Streamlit
- Plotly
- python-docx

### Environment and Packaging

- python-dotenv
- Docker

## Installation and Operation

### Prerequisites

- Python 3.11 or higher
- pip
- MongoDB access (local or Atlas)

### 1. Clone and Enter Project

```bash
git clone <repository-url>
cd ESG-Intelligence-Platform
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

Linux or macOS:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If you want to run the dashboard, ensure UI dependencies are installed:

```bash
pip install streamlit plotly
```

### 4. Configure Environment

Create config/.env and set:

```env
MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>/?appName=<app-name>
MONGO_DB_NAME=company_database
MONGO_FIRM_ID=TECH001
MONGO_COLLECTION=raw_firm_data
```

### 5. Run API Service

```bash
uvicorn API.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

```bash
curl http://localhost:8000/
```

### 6. Run Dashboard (Optional)

```bash
streamlit run dashboard/app.py
```

## API Endpoints

Base URL: http://localhost:8000

### Core Service

- GET / : API health message

### Agent 1 (Data Synchronization)

- POST /agent1/sync : Pull, normalize, and persist operational output
- GET /agent1/companies : List available companies from MongoDB

### Agent 2 (Financial Analysis)

- GET /agent2/process : Create ESG aggregate and financial risk output

### Agent 3 (Compliance Audit)

- GET /agent3/audit : Generate E/S/G compliance verdicts

### Agent 4 (Final Risk Assessment)

- GET /agent4/get-final-summary : Produce final risk score and alert level

### Agent 5 (Explainability)

- GET /agent5/explain : Return SHAP-based risk factor explanation

### Premium Stream

- POST /agent1-premium/start : Start premium listener thread and live emit events

## Data and Output Lifecycle

Primary output pattern:

- outputs/<FIRM_ID>/<FIRM_ID>_agent1_operational_output.csv
- outputs/<FIRM_ID>/<FIRM_ID>_agent2_financial_output.csv
- outputs/<FIRM_ID>/<FIRM_ID>_agent3_compliance_output.csv
- outputs/<FIRM_ID>/<FIRM_ID>_agent4_final_output.csv

Model artifact:

- models/risk_model.pkl

## Folder Structure

```text
ESG-Intelligence-Platform/
|-- API/                     # FastAPI app, routers, database handlers
|-- agents/                  # Core agent implementations and output routing
|-- config/                  # Environment and schema configuration
|-- dashboard/               # Streamlit dashboard
|-- database/                # Mongo init and client helpers
|-- Dataset/                 # Source dataset assets
|-- docs/                    # Reference and report-source docs
|-- ML/                      # Notebooks and ML experiment outputs
|-- models/                  # Model training scripts and model artifacts
|-- outputs/                 # Generated agent outputs (company scoped)
|-- scripts/                 # Report generation scripts
|-- utils/                   # Shared helpers, validators, scheduler
|-- requirements.txt         # Python dependencies
|-- Dockerfile               # Container build file
|-- README.md                # Project documentation
```

## Deployment

### Docker

Build image:

```bash
docker build -t esg-intelligence-platform .
```

Run container:

```bash
docker run -p 8000:8000 --env-file config/.env esg-intelligence-platform
```

### Cloud Runtime Guidance

- Provide all MONGO_* variables through platform secret management
- Persist outputs to object storage if container filesystem is ephemeral
- Add API gateway and authentication for enterprise production
- Add centralized logging and alerting before go-live

## Security and Governance Notes

- Never hardcode credentials in code or notebooks
- Use least-privilege MongoDB users per environment
- Validate incoming payloads and enforce access controls at gateway level
- Keep an auditable trail of agent execution and generated reports

## Troubleshooting

### API starts but agent fails with missing input

Cause: prior agent output does not exist.

Resolution: run upstream endpoints in order, or begin with /agent1/sync.

### SHAP explanation endpoint fails

Cause: missing shap package, model file, or feature mismatch.

Resolution:

- Confirm models/risk_model.pkl exists
- Confirm input file contains all model feature columns
- Reinstall shap and restart API

### MongoDB connection issues

Cause: invalid URI, network restrictions, or wrong DB/collection names.

Resolution:

- Validate MONGO_URI format
- Validate MONGO_DB_NAME and MONGO_COLLECTION
- Check Atlas IP allowlist or VPC rules

## Operational Notes for Corporate Teams

- Recommended execution order in scheduled jobs: Agent1 -> Agent2 -> Agent3 -> Agent4 -> Agent5
- Use isolated environments for dev, qa, and prod
- Track SLA metrics: sync latency, pipeline success rate, and explanation coverage
- Define incident playbooks for data-source failure and model drift events





