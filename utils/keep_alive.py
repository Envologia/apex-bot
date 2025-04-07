import logging
import threading
import time
import os
import requests
from config import WEBHOOK_URL_PATH

logger = logging.getLogger(__name__)

def ping_server():
    """Ping the server to keep the service alive"""
    # For local development, use localhost
    # In production, we'd use the actual deployment URL provided by the platform
    base_url = "http://localhost:5000"
    
    # Get URL from environment if available (for production)
    webhook_url = os.environ.get('WEBHOOK_URL')
    if webhook_url:
        # Extract base URL from webhook URL
        base_url = webhook_url.split('/webhook')[0]
    
    logger.info(f"Keep-alive will ping: {base_url}/health")
    
    while True:
        try:
            # Ping health endpoint
            response = requests.get(f"{base_url}/health")
            if response.status_code == 200:
                logger.debug("Keep-alive ping successful")
            else:
                logger.warning(f"Keep-alive ping returned status code {response.status_code}")
        except Exception as e:
            logger.error(f"Keep-alive ping failed: {e}")
        
        # Sleep for 5 minutes (300 seconds)
        time.sleep(300)

def keep_alive():
    """Start the keep-alive mechanism in a separate thread"""
    thread = threading.Thread(target=ping_server, daemon=True)
    thread.start()
    logger.info("Keep-alive mechanism started")
