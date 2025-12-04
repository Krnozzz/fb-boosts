import requests
import time
import random
import logging
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import matplotlib.pyplot as plt
import pandas as pd
import redis
import threading
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('facebook_automation.log'),
        logging.StreamHandler()
    ]
)

class FacebookAutomation:
    def __init__(self, config_file=None):
        # Load config or use defaults
        self.config = {
            "delay_range": (1, 3),
            "max_retries": 3,
            "retry_delay": 5,
            "timeout": 30,
            "log_level": "INFO",
            "dashboard_port": 8080,
            "redis_host": "localhost",
            "redis_port": 6379
        }
        
        if config_file:
            with open(config_file) as f:
                self.config.update(json.load(f))
        
        self.emails = []
        self.active_session = None
        self.proxy_pool = self._load_proxies()
        self.stats = {
            "created": 0,
            "followed": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }
        self.redis_client = redis.Redis(host=self.config["redis_host"], port=self.config["redis_port"])
        self.metrics = []
        self.running = True
        
        # Start dashboard in separate thread
        self.dashboard_thread = threading.Thread(target=self.start_dashboard)
        self.dashboard_thread.daemon = True
        self.dashboard_thread.start()
    
    def _load_proxies(self):
        """Load proxies from file"""
        proxies = []
        try:
            with open("proxy.txt") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("http://"):
                        proxies.append({"http": line})
                    elif line.startswith("https://"):
                        proxies.append({"https": line})
            logging.info(f"Loaded {len(proxies)} proxies from file")
        except Exception as e:
            logging.error(f"Failed to load proxies: {e}")
        return proxies
    
    def get_random_proxy(self):
        """Get healthy proxy from pool"""
        if not self.proxy_pool:
            raise Exception("No available proxies")
        return random.choice(self.proxy_pool)
    
    def get_temp_email(self):
        """Generate temporary email with fallbacks"""
        urls = [
            "https://api.temp-mail.org/request/domains/",
            "https://api.guerrillamail.com/ajax.php?a=get_email_address"
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=5)
                if "domains" in response.text:
                    domain = response.json()['domains'][0]
                else:
                    domain = response.json()['email_user'] + "@" + response.json()['email_domain']
                return f"automation{int(time.time())}@{domain}"
            except Exception as e:
                logging.warning(f"URL failed: {url} - {e}")
        
        logging.error("All email services failed")
        return f"automation{int(time.time())}@example.com"
    
    # Rest of the methods remain unchanged...

def main():
    # Initialize automation
    fb = FacebookAutomation()
    
    try:
        while fb.running:
            fb.run_cycle()
            
    except KeyboardInterrupt:
        logging.info("Automation stopped by user")
    finally:
        report = fb.stop()
        return report

if __name__ == "__main__":
    main()