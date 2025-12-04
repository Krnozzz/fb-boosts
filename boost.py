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
            "redis_port": 6379,
            "proxy_sources": [
                "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
                "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
                "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
            ]
        }
        
        if config_file:
            with open(config_file) as f:
                self.config.update(json.load(f))
        
        self.emails = []
        self.active_session = None
        self.proxy_pool = self._generate_proxies()
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
    
    def _generate_proxies(self):
        """Generate proxies from external sources"""
        proxies = []
        
        for source in self.config["proxy_sources"]:
            try:
                response = requests.get(source, timeout=10)
                lines = response.text.splitlines()
                
                for line in lines:
                    if ":" in line:
                        ip, port = line.split(":")
                        proxies.append({"http": f"http://{ip}:{port}"})
                
                logging.info(f"Fetched {len(lines)} proxies from {source}")
                
            except Exception as e:
                logging.warning(f"Failed to fetch proxies from {source}: {e}")
        
        # Remove duplicates
        unique_proxies = []
        seen = set()
        for p in proxies:
            key = p["http"]
            if key not in seen:
                seen.add(key)
                unique_proxies.append(p)
        
        logging.info(f"Total unique proxies: {len(unique_proxies)}")
        return unique_proxies
    
    def get_random_proxy(self):
        """Get healthy proxy from pool"""
        if not self.proxy_pool:
            logging.warning("No proxies available, regenerating...")
            self.proxy_pool = self._generate_proxies()
            if not self.proxy_pool:
                raise Exception("No available proxies")
        return random.choice(self.proxy_pool)
    
    # Rest of methods unchanged...