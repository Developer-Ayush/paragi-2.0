# Paragi — Graph Intelligence System

Paragi is a continuously learning graph intelligence system implemented in Python. It uses a unique architecture where semantic meaning resides entirely in edges (vectors), while nodes are pure identifiers.

## Features
- **Pure Node Identifiers**: No vectors or meaning in nodes. Just IDs and labels.
- **Edge-Centric Meaning**: 1024-dim float32 vectors on every edge (700-dim knowledge block + 324-dim control block).
- **Beam-Search Reasoning**: Multi-hop graph traversal for answering queries, not next-token prediction.
- **Continuous Learning**: Lazy decay and recall-based strengthening. The system forgets unused info and reinforces accessed paths.
- **Structural Self-Awareness**: Expansion nodes for identifying and filling knowledge gaps via external APIs (DuckDuckGo/Wikipedia).
- **Credit Economy**: Reward system for knowledge contributions from users.
- **Web UI**: Minimalist chat interface with D3.js force-directed graph visualization.

## Prerequisites
- Python 3.10+
- `rocksdict` (Persistence layer, requires no manual DB setup as it's embedded).

## Installation

1. **Fork and Clone**
   Fork this repository on GitHub and then clone your fork:
   ```bash
   git clone https://github.com/your-username/paragi.git
   cd paragi
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download Language Model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. **Bootstrap Knowledge (ConceptNet)**
   Paragi starts as a "blank slate" unless you bootstrap it with a seed dataset like ConceptNet.
   ```bash
   # Download ConceptNet assertions data (approx 1GB compressed)
   python scripts/download_conceptnet.py

   # Ingest initial edges (capped at 500,000 by default in config)
   python -m bootstrap.seed
   ```

## Running the System

### Development
Start the FastAPI server with auto-reload:
```bash
uvicorn api.main:app --reload --port 8000
```
Access the UI at `http://localhost:8000`.

### Production
For stable use, run without reload and with multiple workers:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## How to Use
1. **Ask Questions**: Type natural language questions like "does fire burn?" or "is steam hot?".
2. **Visualize Paths**: When Paragi finds a path, it shows a "Path Visualization". Click on any node in that path to open the Graph Explorer.
3. **Graph Explorer**: Use the D3.js visualization to see how nodes are connected. Blue nodes are concepts; Red nodes are "Expansion Nodes" (knowledge gaps being investigated).
4. **Knowledge Gaps**: If you ask about something Paragi doesn't know, it creates an expansion node. The background worker will eventually resolve this via internet search.

## Deployment Guide (Make it Live)

### 1. Deploying to a VPS (DigitalOcean/AWS/Linode)
1. **Provision**: Create a Ubuntu 22.04+ instance with at least 4GB RAM.
2. **Setup**:
   ```bash
   sudo apt update && sudo apt install python3-pip git -y
   git clone <your-fork-url>
   cd paragi
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```
3. **Background Ingestion**: Run the bootstrap process in a `screen` or `tmux` session as it takes time.
4. **Service**: Create a systemd service file `/etc/systemd/system/paragi.service`:
   ```ini
   [Unit]
   Description=Paragi AI Service
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/paragi
   Environment="PYTHONPATH=/var/www/paragi"
   ExecStart=/usr/local/bin/uvicorn api.main:app --host 0.0.0.0 --port 80
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
5. **SSL**: Use Nginx as a reverse proxy and `certbot` for HTTPS.

### 2. Docker Deployment
A `Dockerfile` is provided in the repository (if not, you can create one):
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
Build and run:
```bash
docker build -t paragi .
docker run -p 80:8000 -v ./data:/app/data paragi
```

## How to Fork and Customize
Paragi is designed to be highly modular:
- **Change the Brain**: Modify `paragi_io/encoder.py` to use a different embedding model (e.g., OpenAI, Cohere) or change the projection matrix logic.
- **Custom Logic**: Edit `reasoning/scoring.py` to prioritize different types of edges (e.g., make it prioritize `TEMPORAL` over `CAUSES`).
- **New Data Sources**: Add new fetchers to `reasoning/expansion.py` to pull from ArXiv, Twitter, or your own private documents.
- **UI Overhaul**: The frontend is pure HTML/CSS/JS in `api/static/`. It's easy to wrap a React or Vue app around the existing API.

## Testing
Verify your installation:
```bash
export PYTHONPATH=$PYTHONPATH:.
pytest tests/ -v
```

## License
MIT

---
*Built based on Paragi v11 + v12 architecture specifications.*
