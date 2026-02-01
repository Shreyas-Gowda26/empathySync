# Multi-Device Sync Setup

Run empathySync on multiple devices (laptop + desktop) with your data synced between them. Only one device can be active at a time.

For the technical details behind this guide, see [persistence.md](persistence.md).

---

## Prerequisites

- empathySync installed on both devices
- SQLite backend recommended (`USE_SQLITE=true`)
- Device lock enabled (`ENABLE_DEVICE_LOCK=true`)

---

## Step 1: Choose a sync tool

| Tool | Setup | Best For |
|------|-------|----------|
| **Syncthing** | Peer-to-peer, no account needed | Privacy-focused (recommended) |
| **Dropbox** | Account required, cloud-hosted | Ease of use |
| **iCloud Drive** | Apple devices only | Apple ecosystem |
| **OneDrive** | Microsoft account | Windows + mobile |

**Not recommended**: Git (binary SQLite diffs poorly), Google Drive (aggressive caching conflicts).

---

## Step 2: Set up the sync folder

Create a shared folder that your sync tool manages:

```bash
# Example: Syncthing
mkdir -p ~/Sync/empathySync/data

# Example: Dropbox
mkdir -p ~/Dropbox/empathySync/data
```

---

## Step 3: Configure empathySync

On **both devices**, point empathySync to the synced data directory. Edit `.env`:

```bash
# Storage
USE_SQLITE=true

# Point to synced folder
DATA_DIR=/home/youruser/Sync/empathySync/data

# Enable lock protection
ENABLE_DEVICE_LOCK=true
LOCK_STALE_TIMEOUT=300
```

Make sure `DATA_DIR` uses the correct path for each device (it may differ between machines).

---

## Step 4: Migrate existing data (if any)

If you already have data in the default `data/` directory:

```bash
# Copy existing data to sync folder
cp data/empathySync.db ~/Sync/empathySync/data/
# Or for JSON backend:
cp data/wellness_data.json data/trusted_network.json ~/Sync/empathySync/data/
```

---

## Daily usage

### The one rule

**Close empathySync on one device before opening it on another.**

The sequence:

```
1. Close app on Device A
2. Wait for sync to complete (green checkmark / no pending changes)
3. Open app on Device B
```

### What happens if you forget

If you open empathySync while it's still running on another device:

- The app detects the lock file from the other device
- It enters **read-only mode** — you can browse but not write
- A warning banner appears: "Read-only mode: empathySync is open on [device name]"
- You can click **"Take Over"** to force ownership (only if the other device is actually closed)

### What the lock file looks like

```
data/
├── empathySync.db
├── .empathySync.lock    ← Lock file (auto-created, auto-deleted)
└── .device_id           ← Persistent device identifier
```

The lock file contains a heartbeat timestamp. If the heartbeat is older than `LOCK_STALE_TIMEOUT` seconds (default: 300), the lock is considered stale and can be safely taken over.

---

## Syncthing setup (recommended)

1. Install Syncthing on both devices: [syncthing.net](https://syncthing.net/)

2. On Device A, add the folder:
   - Folder path: `~/Sync/empathySync/data`
   - Folder ID: `empathysync-data`

3. On Device B, accept the shared folder and set the same local path.

4. **Ignore patterns** — add to `.stignore` in the synced folder:
   ```
   // Ignore WAL files (only exist while app is running)
   *.db-wal
   *.db-shm
   // Ignore temp files from atomic writes
   .wellness_data_*.tmp
   ```

5. Set sync type to **"Send & Receive"** on both devices.

---

## Dropbox / iCloud / OneDrive setup

These work out of the box — just put the data directory inside the synced folder:

```bash
# Dropbox
DATA_DIR=/home/youruser/Dropbox/empathySync/data

# iCloud (macOS)
DATA_DIR=/Users/youruser/Library/Mobile Documents/com~apple~CloudDocs/empathySync/data

# OneDrive
DATA_DIR=/home/youruser/OneDrive/empathySync/data
```

**Watch for conflict copies**: If the sync tool creates files like `empathySync (conflict).db`, it means both devices wrote simultaneously. Delete the conflict copy and rely on the original — the lock file should prevent this, but check that `ENABLE_DEVICE_LOCK=true`.

---

## SQLite vs JSON for sync

| | JSON | SQLite |
|---|---|---|
| **File changes per write** | Entire file rewritten | Only WAL file changes |
| **Conflict risk** | Higher (whole-file replacement) | Lower (WAL consolidates on close) |
| **Sync tool compatibility** | All tools | All tools (after checkpoint) |
| **Recommendation** | Fine for single device | **Recommended for multi-device** |

**Important**: Always close the app cleanly so SQLite runs its checkpoint (`wal_checkpoint(TRUNCATE)`). This consolidates the WAL file into the main database, leaving a single `.db` file for the sync tool to transfer.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Writes blocked" but other device is closed | Delete `data/.empathySync.lock` or click "Take Over" |
| Conflict copies appearing | Ensure `ENABLE_DEVICE_LOCK=true` on both devices |
| Data not syncing | Check sync tool status; ensure WAL is checkpointed (close app cleanly) |
| App shows old data | Wait for sync to complete before opening |
| Lock timeout too aggressive | Increase `LOCK_STALE_TIMEOUT` in `.env` (default: 300 seconds) |

See also: [Troubleshooting guide](troubleshooting.md)
