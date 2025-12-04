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
        # Updated proxy sources
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
                "https://www.proxy-list.download/api/v1/get?type=http",
                "https://www.proxy-list.download/api/v1/get?type=https",
                "https://www.proxy-list.download/api/v1/get?type=socks4",
                "https://www.proxy-list.download/api/v1/get?type=socks5",
                "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
                "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt"
            ]
        }
        
        if config_file:
            with open(config_file) as f:
                self.config.update(json.load(f))
        
        # Read emails from file
        self.emails = self._read_emails_from_file("email.txt")
        
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
    
    def _read_emails_from_file(self, filename):
        """Read email addresses from a file."""
        try:
            with open(filename, 'r') as file:
                return [line.strip() for line in file]
        except FileNotFoundError:
            logging.error(f"Email file '{filename}' not found.")
            return []
    
    def _generate_proxies(self):
        """Generate proxies from external sources with validation"""
        proxies = []
        for source in self.config["proxy_sources"]:
            try:
                response = requests.get(source, timeout=10)
                lines = response.text.splitlines()
                
                for line in lines:
                    if ":" in line:
                        ip, port = line.split(":")
                        proxy = {"http": f"http://{ip}:{port}"}
                        if self.validate_proxy(proxy):
                            proxies.append(proxy)
                
                logging.info(f"Fetched {len(proxies)} valid proxies from {source}")
                
            except Exception as e:
                logging.warning(f"Failed to fetch proxies from {source}: {e}")
        
        logging.info(f"Total valid proxies: {len(proxies)}")
        return proxies
    
    def validate_proxy(self, proxy):
        """Test if proxy works properly"""
        try:
            response = requests.get(
                "https://httpbin.org/ip", 
                proxies=proxy,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def get_random_proxy(self):
        """Get healthy proxy from pool"""
        if not self.proxy_pool:
            logging.warning("No proxies available, regenerating...")
            self.proxy_pool = self._generate_proxies()
            if not self.proxy_pool:
                raise Exception("No available proxies")
        return random.choice(self.proxy_pool)
    
    def create_account(self, email):
        """Create account with rotating proxies"""
        for attempt in range(self.config["max_retries"]):
            proxy = self.get_random_proxy()
            try:
                # Use proxy for browser
                chrome_options = Options()
                chrome_options.add_argument(f"--proxy-server={proxy['http']}")
                driver = webdriver.Chrome(options=chrome_options)
                
                # Rest of account creation code
                
                driver.quit()
                break
                
            except Exception as e:
                logging.warning(f"Proxy failed: {proxy}, Error: {e}")
                continue
    
    # Rest of methods unchanged...