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
            "proxies": [
                {"http": "http://proxy1:port", "https": "https://proxy1:port"},
                {"http": "http://proxy2:port", "https": "https://proxy2:port"}
            ],
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
        self.proxy_pool = self._init_proxy_pool()
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
    
    def _init_proxy_pool(self):
        """Initialize proxy pool with health checks"""
        proxies = []
        for p in self.config["proxies"]:
            try:
                requests.get("https://www.facebook.com", 
                           proxies=p, timeout=5)
                proxies.append(p)
                logging.info(f"Proxy added: {p['http']}")
            except Exception as e:
                logging.warning(f"Proxy failed: {p['http']} - {e}")
        return proxies
    
    def get_random_proxy(self):
        """Get healthy proxy from pool"""
        if not self.proxy_pool:
            raise Exception("No available proxies")
        return random.choice(self.proxy_pool)
    
    def get_temp_email(self):
        """Generate temporary email with fallbacks"""
        try:
            response = requests.get("https://api.temp-mail.org/request/domains/", timeout=5)
            domain = response.json()['domains'][0]
            return f"automation{int(time.time())}@{domain}"
        except Exception as e:
            logging.error(f"Email generation failed: {e}")
            return f"automation{int(time.time())}@example.com"
    
    def create_account(self):
        """Create new Facebook account with full error handling"""
        email = self.get_temp_email()
        self.emails.append(email)
        
        max_retries = self.config["max_retries"]
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                proxy = self.get_random_proxy()
                
                options = Options()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument(f"--proxy-server={proxy['http']}")
                
                self.active_session = webdriver.Chrome(options=options)
                wait = WebDriverWait(self.active_session, self.config["timeout"])
                
                self.active_session.get("https://www.facebook.com/signup")
                wait.until(EC.presence_of_element_located((By.NAME, "firstname")))
                
                self.active_session.find_element(By.NAME, "firstname").send_keys("Automation")
                self.active_session.find_element(By.NAME, "lastname").send_keys("User")
                self.active_session.find_element(By.NAME, "reg_email__").send_keys(email)
                self.active_session.find_element(By.NAME, "reg_passwd__").send_keys("SecurePassword123!")
                self.active_session.find_element(By.NAME, "websubmit").click()
                
                time.sleep(random.randint(*self.config["delay_range"]))
                logging.info(f"Account created: {email}")
                self.stats["created"] += 1
                self._record_metric("created", 1)
                return True
                
            except Exception as e:
                retry_count += 1
                logging.error(f"Retry {retry_count}/{max_retries} for account creation: {e}")
                time.sleep(self.config["retry_delay"])
                
                if self.active_session:
                    self.active_session.quit()
                    self.active_session = None
                    
        logging.error(f"Failed to create account after {max_retries} retries")
        self.stats["errors"] += 1
        self._record_metric("errors", 1)
        return False
    
    def boost_followers(self, target="target_username"):
        """Boost followers with proxy rotation"""
        if not self.active_session:
            raise Exception("No active session")
            
        max_retries = self.config["max_retries"]
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                proxy = self.get_random_proxy()
                self.active_session.get(f"https://www.facebook.com/{target}")
                wait = WebDriverWait(self.active_session, self.config["timeout"])
                
                follow_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Follow')]"))
                )
                follow_button.click()
                
                logging.info(f"Successfully followed {target}")
                self.stats["followed"] += 1
                self._record_metric("followed", 1)
                return True
                
            except Exception as e:
                retry_count += 1
                logging.error(f"Retry {retry_count}/{max_retries} for follow: {e}")
                time.sleep(self.config["retry_delay"])
                
        logging.error(f"Failed to follow {target} after {max_retries} retries")
        self.stats["errors"] += 1
        self._record_metric("errors", 1)
        return False
    
    def _record_metric(self, key, value):
        """Record metric in Redis and local list"""
        timestamp = int(time.time())
        metric = {
            "timestamp": timestamp,
            "key": key,
            "value": value
        }
        self.metrics.append(metric)
        
        # Store in Redis for dashboard
        self.redis_client.zadd(
            f"metrics:{key}",
            {f"{timestamp}:{key}": timestamp}
        )
        self.redis_client.hincrby("metrics:count", key, value)
    
    def start_dashboard(self):
        """Start simple HTTP dashboard"""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class DashboardHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/":
                    html = self._generate_html()
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(html.encode())
                elif self.path == "/metrics":
                    data = self._get_metrics_data()
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(data).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
        
        server = HTTPServer(('0.0.0.0', self.config["dashboard_port"]), DashboardHandler)
        logging.info(f"Dashboard started on port {self.config['dashboard_port']}")
        server.serve_forever()
    
    def _generate_html(self):
        """Generate HTML for dashboard"""
        stats = self._get_metrics_data()
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Facebook Automation Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <h1>Facebook Automation Dashboard</h1>
            <canvas id="metricsChart" width="400" height="200"></canvas>
            <script>
                fetch('/metrics').then(r => r.json()).then(data => {{
                    const ctx = document.getElementById('metricsChart').getContext('2d');
                    new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            labels: data.timestamps,
                            datasets: Object.keys(data.datasets).map(k => ({
                                label: k,
                                data: data.datasets[k],
                                borderColor: '#3e95cd'
                            }))
                        }},
                        options: {{
                            responsive: true,
                            scales: {{
                                x: {{ display: true }},
                                y: {{ display: true }}
                            }}
                        }}
                    }});
                }});
            </script>
        </body>
        </html>
        """
    
    def _get_metrics_data(self):
        """Get metrics data for dashboard"""
        timestamps = []
        datasets = {}
        
        for m in self.metrics[-100:]:  # Last 100 records
            ts = m["timestamp"]
            key = m["key"]
            if ts not in timestamps:
                timestamps.append(ts)
            if key not in datasets:
                datasets[key] = [0] * len(timestamps)
            datasets[key][-1] += m["value"]
        
        return {
            "timestamps": timestamps,
            "datasets": datasets
        }
    
    def run_cycle(self):
        """Complete one cycle: create account + boost followers"""
        success = self.create_account()
        if success:
            time.sleep(random.randint(*self.config["delay_range"]))
            self.boost_followers()
        return success
    
    def generate_report(self):
        """Generate statistics report"""
        duration = datetime.now() - datetime.fromisoformat(self.stats["start_time"])
        return {
            "duration": str(duration),
            "stats": self.stats,
            "proxy_pool_size": len(self.proxy_pool)
        }
    
    def stop(self):
        """Stop automation and generate final report"""
        self.running = False
        report = self.generate_report()
        logging.info(f"Automation completed: {report}")
        return report

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