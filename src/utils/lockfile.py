"""
Lock File Manager for empathySync

Prevents data conflicts when syncing between multiple devices.
Uses heartbeat-based staleness detection (not PID) because PIDs
can be reused after reboot.

Usage:
    from utils.lockfile import acquire_lock, release_lock, check_lock_status

    # On app startup
    status = check_lock_status()
    if status["locked_by_other"]:
        # Show warning to user
        print(f"Open on {status['hostname']} since {status['started_at']}")

    # Acquire (will fail if another device has active lock)
    if acquire_lock():
        # Good to go
        ...
    else:
        # User must close on other device or force takeover

    # On app close
    release_lock()
"""

import json
import os
import socket
import threading
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import atexit

from config.settings import settings

logger = logging.getLogger(__name__)

# How often to update heartbeat (seconds)
HEARTBEAT_INTERVAL = 60


def get_stale_timeout() -> int:
    """Get lock stale timeout from settings (with fallback)."""
    return getattr(settings, "LOCK_STALE_TIMEOUT", 300)


# Unique device identifier (persists across app restarts on same device)
_device_id: Optional[str] = None

# Heartbeat thread
_heartbeat_thread: Optional[threading.Thread] = None
_heartbeat_stop = threading.Event()


def get_lock_path() -> Path:
    """Get the lock file path."""
    return settings.DATA_DIR / ".empathySync.lock"


def get_device_id() -> str:
    """
    Get a unique device identifier.

    Uses hostname + a UUID that persists in a local file.
    This is more reliable than PID for detecting "same device".
    """
    global _device_id

    if _device_id is not None:
        return _device_id

    device_id_file = settings.DATA_DIR / ".device_id"

    if device_id_file.exists():
        try:
            _device_id = device_id_file.read_text().strip()
            return _device_id
        except Exception:
            pass

    # Generate new device ID
    _device_id = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"

    # Save for future runs
    try:
        device_id_file.parent.mkdir(parents=True, exist_ok=True)
        device_id_file.write_text(_device_id)
    except Exception as e:
        logger.warning(f"Could not save device ID: {e}")

    return _device_id


def _read_lock() -> Optional[Dict]:
    """Read and parse the lock file."""
    lock_path = get_lock_path()

    if not lock_path.exists():
        return None

    try:
        with open(lock_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read lock file: {e}")
        return None


def _write_lock(lock_data: Dict):
    """Write the lock file atomically."""
    lock_path = get_lock_path()
    temp_path = lock_path.with_suffix(".tmp")

    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        with open(temp_path, "w") as f:
            json.dump(lock_data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, lock_path)

    except Exception as e:
        logger.error(f"Could not write lock file: {e}")
        try:
            temp_path.unlink()
        except OSError:
            pass
        raise


def _delete_lock():
    """Delete the lock file."""
    lock_path = get_lock_path()
    try:
        if lock_path.exists():
            lock_path.unlink()
            logger.info("Lock file released")
    except OSError as e:
        logger.warning(f"Could not delete lock file: {e}")


def _is_lock_stale(lock_data: Dict) -> bool:
    """Check if a lock's heartbeat is too old."""
    if not lock_data:
        return True

    heartbeat_str = lock_data.get("heartbeat")
    if not heartbeat_str:
        return True

    try:
        heartbeat = datetime.fromisoformat(heartbeat_str)
        age = datetime.now() - heartbeat
        return age.total_seconds() > get_stale_timeout()
    except (ValueError, TypeError):
        return True


def _is_our_lock(lock_data: Dict) -> bool:
    """Check if this is our own lock (same device)."""
    if not lock_data:
        return False
    return lock_data.get("device_id") == get_device_id()


def check_lock_status() -> Dict:
    """
    Check the current lock status.

    Returns:
        {
            "locked": bool,           # Is there a valid lock?
            "locked_by_us": bool,     # Is it our lock?
            "locked_by_other": bool,  # Is another device holding it?
            "stale": bool,            # Is the lock stale (can be taken over)?
            "device_id": str,         # Device holding the lock
            "hostname": str,          # Hostname of lock holder
            "started_at": str,        # When lock was acquired
            "heartbeat": str,         # Last heartbeat time
            "age_seconds": float,     # Seconds since last heartbeat
        }
    """
    lock_data = _read_lock()

    if not lock_data:
        return {
            "locked": False,
            "locked_by_us": False,
            "locked_by_other": False,
            "stale": False,
            "device_id": None,
            "hostname": None,
            "started_at": None,
            "heartbeat": None,
            "age_seconds": None,
        }

    is_stale = _is_lock_stale(lock_data)
    is_ours = _is_our_lock(lock_data)

    # Calculate age
    age_seconds = None
    if lock_data.get("heartbeat"):
        try:
            heartbeat = datetime.fromisoformat(lock_data["heartbeat"])
            age_seconds = (datetime.now() - heartbeat).total_seconds()
        except (ValueError, TypeError):
            pass

    return {
        "locked": not is_stale,
        "locked_by_us": is_ours and not is_stale,
        "locked_by_other": not is_ours and not is_stale,
        "stale": is_stale,
        "device_id": lock_data.get("device_id"),
        "hostname": lock_data.get("hostname"),
        "started_at": lock_data.get("started_at"),
        "heartbeat": lock_data.get("heartbeat"),
        "age_seconds": age_seconds,
    }


def acquire_lock(force: bool = False) -> bool:
    """
    Attempt to acquire the lock atomically.

    Uses O_CREAT | O_EXCL for atomic create-or-fail on the lock file,
    eliminating the read-then-write race condition where two processes
    could both see "unlocked" and both write their lock.

    Args:
        force: If True, take over even if another device has an active lock.
               Use with caution - may cause data conflicts.

    Returns:
        True if lock acquired, False if blocked by another device.
    """
    global _heartbeat_thread, _heartbeat_stop

    lock_path = get_lock_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # Build lock data
    now = datetime.now().isoformat()
    lock_data = {
        "device_id": get_device_id(),
        "hostname": socket.gethostname(),
        "pid": os.getpid(),  # For debugging only, not used for staleness
        "started_at": now,
        "heartbeat": now,
    }

    try:
        if not force:
            # Atomic create: O_CREAT | O_EXCL fails if file already exists
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                try:
                    content = json.dumps(lock_data, indent=2).encode()
                    os.write(fd, content)
                    os.fsync(fd)
                finally:
                    os.close(fd)
            except FileExistsError:
                # Lock file exists — check if it's stale or ours
                existing = _read_lock()
                if existing and _is_our_lock(existing):
                    # Re-entry from same device (e.g., crash recovery)
                    _write_lock(lock_data)
                elif existing and _is_lock_stale(existing):
                    # Stale lock — safe to take over
                    _write_lock(lock_data)
                else:
                    # Active lock held by another device
                    status = check_lock_status()
                    age = status.get("age_seconds", 0) or 0
                    logger.warning(
                        f"Lock held by another device: {status.get('hostname')} "
                        f"(last heartbeat: {age:.0f}s ago)"
                    )
                    return False
        else:
            # Force takeover — overwrite regardless
            _write_lock(lock_data)

        logger.info(f"Lock acquired by {lock_data['hostname']}")

        # Start heartbeat thread
        _heartbeat_stop.clear()
        _heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
        _heartbeat_thread.start()

        # Register cleanup on exit
        atexit.register(release_lock)

        return True

    except Exception as e:
        logger.error(f"Failed to acquire lock: {e}")
        return False


def release_lock():
    """
    Release the lock.

    Should be called on clean app shutdown.
    """
    global _heartbeat_thread, _heartbeat_stop

    # Stop heartbeat thread
    _heartbeat_stop.set()
    if _heartbeat_thread is not None:
        _heartbeat_thread.join(timeout=2.0)
        _heartbeat_thread = None

    # Only delete if it's our lock (or already gone)
    lock_path = get_lock_path()
    if not lock_path.exists():
        return  # Already released

    status = check_lock_status()
    if status["locked_by_us"] or status["stale"]:
        _delete_lock()
    elif status["locked"]:
        logger.warning("Not releasing lock - held by another device")


def update_heartbeat():
    """Update the heartbeat timestamp in the lock file."""
    lock_data = _read_lock()

    if not lock_data or not _is_our_lock(lock_data):
        logger.warning("Cannot update heartbeat - lock not owned by us")
        return

    lock_data["heartbeat"] = datetime.now().isoformat()

    try:
        _write_lock(lock_data)
    except Exception as e:
        logger.error(f"Failed to update heartbeat: {e}")


def _heartbeat_loop():
    """Background thread that updates heartbeat periodically."""
    while not _heartbeat_stop.wait(HEARTBEAT_INTERVAL):
        update_heartbeat()


def format_lock_warning(status: Dict) -> str:
    """
    Format a user-friendly warning message for a locked state.

    Returns empty string if no warning needed.
    """
    if not status["locked_by_other"]:
        return ""

    hostname = status.get("hostname", "another device")
    started = status.get("started_at", "unknown time")

    # Parse started time for friendly display
    try:
        started_dt = datetime.fromisoformat(started)
        started = started_dt.strftime("%I:%M %p on %b %d")
    except (ValueError, TypeError):
        pass

    age = status.get("age_seconds")
    if age is not None:
        if age < 120:
            age_str = f"{int(age)} seconds ago"
        else:
            age_str = f"{int(age / 60)} minutes ago"
    else:
        age_str = "unknown"

    return (
        f"empathySync appears to be open on {hostname} "
        f"(started {started}, last active {age_str}).\n\n"
        f"Close it there first to sync safely, or click 'Take Over' "
        f"if that device is unavailable."
    )
