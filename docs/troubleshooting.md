# Troubleshooting

Common issues and how to fix them.

---

## Ollama not responding

**Symptom**: App shows "Ollama server is not reachable" or responses time out.

**Fixes**:

1. Check if Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```
   If this fails, Ollama isn't running.

2. Start Ollama:
   ```bash
   # macOS / Linux
   ollama serve

   # Or if installed as a service
   systemctl --user start ollama    # Linux
   brew services start ollama       # macOS with Homebrew
   ```

3. If not installed:
   ```bash
   # Install from https://ollama.com/download
   curl -fsSL https://ollama.com/install.sh | sh
   ```

4. Verify the host in `.env` matches where Ollama is running:
   ```bash
   OLLAMA_HOST=http://localhost:11434
   ```

---

## Model not found

**Symptom**: "Model not available" or empty responses.

**Fixes**:

1. List available models:
   ```bash
   ollama list
   ```

2. Pull the model specified in your `.env`:
   ```bash
   # Check what model you configured
   grep OLLAMA_MODEL .env

   # Pull it
   ollama pull llama2
   ```

3. **Recommended models by RAM**:

   | RAM | Model | Pull Command |
   |-----|-------|-------------|
   | 4GB | tinyllama | `ollama pull tinyllama` |
   | 8GB | llama2 (7B) | `ollama pull llama2` |
   | 16GB | llama2:13b | `ollama pull llama2:13b` |
   | 32GB+ | mixtral | `ollama pull mixtral` |

4. If using Docker, pull inside the container:
   ```bash
   docker exec empathysync-ollama ollama pull llama2
   ```

---

## Slow responses

**Symptom**: Responses take 30+ seconds.

**Causes and fixes**:

1. **First request after startup**: The model needs to load into memory. First response is always slower. Subsequent responses should be faster.

2. **Model too large for your RAM**: If the model exceeds available RAM, it swaps to disk and becomes very slow. Use a smaller model (see table above).

3. **No GPU**: Ollama runs on CPU by default. GPU acceleration significantly improves speed.
   ```bash
   # Check if Ollama is using GPU
   ollama ps
   ```

4. **LLM classification enabled**: Each message requires two LLM calls (classification + response). Disable if too slow:
   ```bash
   # .env
   LLM_CLASSIFICATION_ENABLED=false
   ```
   This falls back to keyword matching, which is instant but less accurate.

---

## App won't start

**Symptom**: `streamlit run src/app.py` fails or `empathysync` command not found.

**Fixes**:

1. **Check Python version** (3.9+ required):
   ```bash
   python3 --version
   ```

2. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Check .env file exists**:
   ```bash
   ls .env || cp .env.example .env
   ```

5. **If `empathysync` command not found**:
   ```bash
   pip install -e .
   ```

6. **Port already in use** (Streamlit default 8501):
   ```bash
   streamlit run src/app.py --server.port 8502
   ```

---

## Database locked

**Symptom**: "WriteBlockedError: Writes are currently blocked" or "Writes blocked" in sidebar.

**Causes**:

1. **Another device has the lock**: empathySync is open on another machine. Close it there first, wait for sync, then retry.

2. **Stale lock from a crash**: The app crashed without cleaning up.
   ```bash
   # Check the lock file
   cat data/.empathySync.lock

   # If the heartbeat is old, delete it
   rm data/.empathySync.lock
   ```

3. **Force takeover**: Click "Take Over" in the UI warning banner. This removes the stale lock and claims ownership.

4. **Disable lock checking** (if you only use one device):
   ```bash
   # .env
   ENABLE_DEVICE_LOCK=false
   ```

---

## Data corruption

**Symptom**: App starts with empty data, or error about corrupted JSON.

**What happened**: A write was interrupted (crash, power loss, disk full). The atomic write system should prevent this, but edge cases exist.

**Recovery**:

1. **Check for backup files**:
   ```bash
   ls data/*.corrupted.*
   ```
   Corrupted files are automatically backed up with timestamps. The most recent `.corrupted` file may contain your data.

2. **Restore from backup**:
   ```bash
   # Inspect the backup
   python3 -c "import json; print(json.dumps(json.load(open('data/wellness_data.corrupted.20260201.json')), indent=2))" | head -20

   # If it looks good, restore it
   cp data/wellness_data.corrupted.20260201.json data/wellness_data.json
   ```

3. **SQLite recovery** (if using SQLite backend):
   ```bash
   # Check database integrity
   sqlite3 data/empathySync.db "PRAGMA integrity_check;"

   # If corrupt, try recovery
   sqlite3 data/empathySync.db ".recover" | sqlite3 data/empathySync_recovered.db
   mv data/empathySync.db data/empathySync.db.corrupt
   mv data/empathySync_recovered.db data/empathySync.db
   ```

4. **Start fresh** (last resort):
   ```bash
   mv data/ data_backup/
   mkdir data/
   ```
   The app will create fresh data files on next startup.

---

## Docker issues

**Symptom**: `docker compose up` fails or containers won't start.

**Fixes**:

1. **Ollama container not ready**: The app waits for Ollama's health check. If it times out:
   ```bash
   # Check container status
   docker compose ps

   # Check Ollama logs
   docker compose logs ollama
   ```

2. **Model not pulled**: After containers start, pull the model:
   ```bash
   docker exec empathysync-ollama ollama pull llama2
   ```

3. **Port conflicts**:
   ```bash
   # Check if ports are in use
   lsof -i :8501   # Streamlit
   lsof -i :11434  # Ollama
   ```

4. **Permission errors on data/ volume**:
   ```bash
   chmod 755 data/
   ```

---

## Still stuck?

1. Check the logs:
   ```bash
   ls logs/
   cat logs/empathysync.log | tail -50
   ```

2. Run the health check manually:
   ```bash
   source venv/bin/activate
   python3 -c "from src.utils.health_check import run_health_checks; [print(f'{c.name}: {c.status}') for c in run_health_checks()]"
   ```

3. Open an issue: [github.com/Olawoyin007/empathySync/issues](https://github.com/Olawoyin007/empathySync/issues)
