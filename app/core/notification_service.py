import queue
import threading
import requests
import os
import app.core.log_service as log_service
from app.core.settings_service import get_setting

# Thread-safe outbox queue
_outbox_queue = queue.Queue()
_worker_started = False
_lock = threading.Lock()

def _send_telegram(token, chat_id, text, image_path=None):
    """Internal helper to send message/photo to Telegram (blocking, called from worker thread)."""
    try:
        if image_path and os.path.exists(image_path):
            # Send photo with text as caption
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            data = {"chat_id": chat_id, "caption": text, "parse_mode": "Markdown"}
            with open(image_path, "rb") as img_file:
                files = {"photo": img_file}
                r = requests.post(url, data=data, files=files, timeout=5.0)
        else:
            # Send plain text
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
            r = requests.post(url, json=payload, timeout=5.0)
            
        r.raise_for_status()
        log_service.info("Notificación de Telegram enviada correctamente.")
        return True
    except Exception as e:
        log_service.error(f"Error al enviar notificación de Telegram: {e}")
        return False

def _send_discord(webhook_url, text, image_path=None):
    """Internal helper to send message/file to Discord (blocking, called from worker thread)."""
    try:
        if image_path and os.path.exists(image_path):
            # Discord webhook with file attachment
            payload = {"content": text}
            with open(image_path, "rb") as img_file:
                files = {
                    "file": (os.path.basename(image_path), img_file, "image/jpeg")
                }
                r = requests.post(webhook_url, data=payload, files=files, timeout=5.0)
        else:
            # Plain text
            payload = {"content": text}
            r = requests.post(webhook_url, json=payload, timeout=5.0)
            
        r.raise_for_status()
        log_service.info("Notificación de Discord enviada correctamente.")
        return True
    except Exception as e:
        log_service.error(f"Error al enviar notificación de Discord: {e}")
        return False

def _outbox_worker():
    """Background worker loop that processes notifications sequentially."""
    log_service.info("Iniciado hilo outbox de notificaciones.")
    while True:
        try:
            job = _outbox_queue.get()
            if job is None:
                break
                
            token = job.get("token")
            chat_id = job.get("chat_id")
            webhook_url = job.get("webhook_url")
            text = job.get("text")
            image_path = job.get("image_path")
            
            if job.get("type") == "telegram" and token and chat_id:
                _send_telegram(token, chat_id, text, image_path)
            elif job.get("type") == "discord" and webhook_url:
                _send_discord(webhook_url, text, image_path)
                
            _outbox_queue.task_done()
        except Exception as e:
            log_service.error(f"Error en el bucle del trabajador de outbox: {e}")

def _ensure_worker_started():
    """Starts the outbox daemon thread if not already running."""
    global _worker_started
    with _lock:
        if not _worker_started:
            t = threading.Thread(target=_outbox_worker, daemon=True, name="NotificationOutbox")
            t.start()
            _worker_started = True

def send_notification(text, image_path=None):
    """
    Asynchronously queues a notification to be sent to active channels
    (Telegram and/or Discord) as configured in settings.
    """
    _ensure_worker_started()
    
    # 1. Telegram
    tel_enabled = get_setting("telegram_enabled", "False").lower() == "true"
    tel_token = get_setting("telegram_token", "")
    tel_chat_id = get_setting("telegram_chat_id", "")
    
    if tel_enabled and tel_token and tel_chat_id:
        _outbox_queue.put({
            "type": "telegram",
            "token": tel_token,
            "chat_id": tel_chat_id,
            "text": text,
            "image_path": image_path
        })
        
    # 2. Discord
    disc_enabled = get_setting("discord_enabled", "False").lower() == "true"
    disc_webhook = get_setting("discord_webhook", "")
    
    if disc_enabled and disc_webhook:
        _outbox_queue.put({
            "type": "discord",
            "webhook_url": disc_webhook,
            "text": text,
            "image_path": image_path
        })
