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
        self.config = {
            "delay_range": (1, 3),
            "max_retries": 3,
            "retry_delay": 5,
            "timeout": 30,
            "log_level": "INFO",
            "dashboard_port": 8080,
            "redis_host": "localhost",
            "redis_port": 6379,
            "use_proxies": False,  # Set to False to disable proxies initially
            "proxy_sources": [
                "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
                "https://www.proxy-list.download/api/v1/get?type=http",
                "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
                "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
            ]
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file) as f:
                self.config.update(json.load(f))
        
        # Read emails from file
        self.emails = self._read_emails_from_file("email.txt")
        
        self.active_session = None
        self.proxy_pool = []
        
        # Only fetch proxies if enabled
        if self.config.get("use_proxies", False):
            self.proxy_pool = self._generate_proxies()
        
        self.stats = {
            "created": 0,
            "followed": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }
        
        # Initialize Redis with error handling
        try:
            self.redis_client = redis.Redis(
                host=self.config["redis_host"], 
                port=self.config["redis_port"],
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            logging.info("Redis connection established")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logging.warning(f"Redis unavailable: {e}. Continuing without Redis.")
            self.redis_client = None
        
        self.metrics = []
        self.running = True
        
        # Start dashboard in separate thread
        self.dashboard_thread = threading.Thread(target=self.start_dashboard)
        self.dashboard_thread.daemon = True
        self.dashboard_thread.start()
    
    def _read_emails_from_file(self, filename):
        """Read email addresses from a file."""
        try:
            if not os.path.exists(filename):
                logging.warning(f"Email file '{filename}' not found. Creating empty file.")
                with open(filename, 'w') as f:
                    f.write("example@email.com\n")
                return []
            
            with open(filename, 'r') as file:
                emails = [line.strip() for line in file if line.strip() and '@' in line]
                logging.info(f"Loaded {len(emails)} emails from {filename}")
                return emails
        except Exception as e:
            logging.error(f"Error reading email file: {e}")
            return []
    
    def _generate_proxies(self):
        """Generate proxies from external sources with validation"""
        proxies = []
        
        for source in self.config["proxy_sources"]:
            try:
                logging.info(f"Fetching proxies from {source}...")
                response = requests.get(source, timeout=15)
                
                if response.status_code != 200:
                    logging.warning(f"Failed to fetch from {source}: HTTP {response.status_code}")
                    continue
                
                lines = response.text.strip().splitlines()
                
                for line in lines:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse proxy format (IP:PORT)
                    if ':' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            ip = parts[0].strip()
                            port = parts[1].strip()
                            
                            # Basic validation
                            if self._is_valid_ip(ip) and port.isdigit():
                                proxy_dict = {
                                    "http": f"http://{ip}:{port}",
                                    "https": f"http://{ip}:{port}"
                                }
                                
                                # Optionally validate (slow)
                                # if self.validate_proxy(proxy_dict):
                                proxies.append(proxy_dict)
                
                logging.info(f"Fetched {len(proxies)} proxies from {source}")
                
            except requests.RequestException as e:
                logging.warning(f"Failed to fetch proxies from {source}: {e}")
            except Exception as e:
                logging.error(f"Unexpected error fetching proxies from {source}: {e}")
        
        # Remove duplicates
        unique_proxies = []
        seen = set()
        for proxy in proxies:
            proxy_str = proxy['http']
            if proxy_str not in seen:
                seen.add(proxy_str)
                unique_proxies.append(proxy)
        
        logging.info(f"Total unique proxies: {len(unique_proxies)}")
        return unique_proxies
    
    def _is_valid_ip(self, ip):
        """Basic IP validation"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    def validate_proxy(self, proxy):
        """Test if proxy works properly"""
        try:
            response = requests.get(
                "https://httpbin.org/ip", 
                proxies=proxy,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logging.debug(f"Proxy validation failed: {e}")
            return False
    
    def get_random_proxy(self):
        """Get healthy proxy from pool"""
        if not self.config.get("use_proxies", False):
            return None
        
        if not self.proxy_pool:
            logging.warning("No proxies available, regenerating...")
            self.proxy_pool = self._generate_proxies()
            if not self.proxy_pool:
                logging.error("No available proxies. Disabling proxy usage.")
                self.config["use_proxies"] = False
                return None
        
        return random.choice(self.proxy_pool)
    
    def create_account(self, email):
        """Create account with rotating proxies"""
        for attempt in range(self.config["max_retries"]):
            driver = None
            try:
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                
                # Add proxy if enabled
                if self.config.get("use_proxies", False):
                    proxy = self.get_random_proxy()
                    if proxy:
                        chrome_options.add_argument(f"--proxy-server={proxy['http']}")
                        logging.info(f"Using proxy: {proxy['http']}")
                
                driver = webdriver.Chrome(options=chrome_options)
                driver.set_page_load_timeout(self.config["timeout"])
                
                # Navigate to Facebook
                logging.info(f"Attempting to create account for {email}")
                driver.get("https://www.facebook.com/reg/")
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "firstname"))
                )
                
                # Fill in account details (example)
                driver.find_element(By.NAME, "firstname").send_keys("Test")
                driver.find_element(By.NAME, "lastname").send_keys("User")
                driver.find_element(By.NAME, "reg_email__").send_keys(email)
                
                # Add delay
                time.sleep(random.uniform(*self.config["delay_range"]))
                
                logging.info(f"Account creation initiated for {email}")
                self.stats["created"] += 1
                
                driver.quit()
                return True
                
            except Exception as e:
                logging.error(f"Attempt {attempt + 1}/{self.config['max_retries']} failed for {email}: {e}")
                self.stats["errors"] += 1
                
                if driver:
                    driver.quit()
                
                if attempt < self.config["max_retries"] - 1:
                    time.sleep(self.config["retry_delay"])
                else:
                    logging.error(f"Failed to create account for {email} after all retries")
                    return False
        
        return False
    
    def start_dashboard(self):
        """Simple dashboard placeholder"""
        logging.info(f"Dashboard started on port {self.config['dashboard_port']}")
        # Implement actual dashboard using Flask/FastAPI if needed
        while self.running:
            time.sleep(10)
    
    def run(self):
        """Main execution loop"""
        if not self.emails:
            logging.error("No emails to process. Add emails to email.txt")
            return
        
        logging.info(f"Starting automation for {len(self.emails)} emails")
        
        for email in self.emails:
            if not self.running:
                break
            
            self.create_account(email)
            time.sleep(random.uniform(*self.config["delay_range"]))
        
        logging.info(f"Automation completed: {self.stats}")
    
    def stop(self):
        """Graceful shutdown"""
        self.running = False
        logging.info("Stopping automation...")

if __name__ == "__main__":
    automation = FacebookAutomation()
    try:
        automation.run()
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
        automation.stop()