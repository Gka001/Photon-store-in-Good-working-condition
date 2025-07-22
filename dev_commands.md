
# 🚀 Photon Cure Developer Command Cheat Sheet

This file contains essential commands and explanations for managing your Django development environment using Redis, Celery, and Django.

---

## 🔧 Start the Development Environment

```bash
./start_dev.sh
```

Runs:
- Redis server
- Celery worker (to process background tasks like sending emails)
- Django development server

---

## 🛑 Stop the Development Environment

```bash
./stop_dev.sh
```

Stops:
- Celery worker
- Django development server
- Redis (via system service)

📝 If Redis doesn't stop due to permission issues, run manually:
```bash
sudo service redis-server stop
```

---

## 📊 Monitor CPU & Memory Usage

```bash
htop
```

- Shows live view of system processes
- Use `F6` to sort by CPU or Memory
- Press `q` to quit

To install `htop`:
```bash
sudo apt update && sudo apt install htop
```

---

## 📥 Check if Redis is Running

```bash
redis-cli ping
```

✅ Output should be:
```
PONG
```

---

## 💌 Verify Welcome Email Feature

1. Make sure all 3 terminals are running: Redis, Celery, Django server.
2. Register a new user.
3. Celery sends a welcome email in the background.

---

## 🧪 Check Duplicate Email Validation

Try registering with the same email again.

Expected error:
```
Email: User with this Email already exists.
```

---

## 🐍 Activate Python Virtual Environment

```bash
source venv/bin/activate
```

If you're using WSL:
```bash
source ~/photon_cure/venv/bin/activate
```

---

## 🔚 Manually Check or Kill Processes

### List processes:
```bash
ps aux | grep redis
ps aux | grep celery
ps aux | grep manage.py
```

### Kill Redis manually (if needed):
```bash
sudo pkill -f redis-server
```

---

## 📁 Location
Keep this file in your project root as `dev_commands.md`
