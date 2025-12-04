import requests
import time
import random
import logging
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
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
    def __init__(self, target_account=None, config_file=None):
        self.config = {
            "delay_range": (2, 5),
            "max_retries": 3,
            "retry_delay": 5,
            "timeout": 30,
            "use_proxies": False,
            "headless": False,  # Set to True to hide browser
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file) as f:
                self.config.update(json.load(f))
        
        # Target account to follow
        self.target_account = target_account
        
        # Read emails from file
        self.emails = self._read_emails_from_file("email.txt")
        
        self.stats = {
            "created": 0,
            "followed": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }
        
        self.running = True
        
        # Install ChromeDriver automatically
        self._setup_chromedriver()
    
    def _setup_chromedriver(self):
        """Install ChromeDriver automatically using webdriver-manager"""
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service as ChromeService
            
            logging.info("Installing/Updating ChromeDriver...")
            self.driver_service = ChromeService(ChromeDriverManager().install())
            logging.info("ChromeDriver installed successfully")
        except ImportError:
            logging.error("webdriver-manager not installed. Installing now...")
            os.system("pip install webdriver-manager")
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service as ChromeService
            self.driver_service = ChromeService(ChromeDriverManager().install())
    
    def _read_emails_from_file(self, filename):
        """Read email addresses from a file."""
        try:
            if not os.path.exists(filename):
                logging.warning(f"Email file '{filename}' not found. Creating example file.")
                with open(filename, 'w') as f:
                    f.write("example1@email.com\nexample2@email.com\n")
                return []
            
            with open(filename, 'r') as file:
                emails = [line.strip() for line in file if line.strip() and '@' in line]
                logging.info(f"Loaded {len(emails)} emails from {filename}")
                return emails
        except Exception as e:
            logging.error(f"Error reading email file: {e}")
            return []
    
    def _generate_random_name(self):
        """Generate random first and last names"""
        first_names = ["John", "Jane", "Mike", "Sarah", "David", "Emma", "Chris", "Lisa", 
                      "Tom", "Anna", "James", "Mary", "Robert", "Linda", "Michael", "Patricia"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
                     "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson"]
        
        return random.choice(first_names), random.choice(last_names)
    
    def _generate_random_password(self):
        """Generate a random password"""
        import string
        chars = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(random.choice(chars) for _ in range(12))
    
    def create_driver(self):
        """Create a new Chrome driver instance"""
        chrome_options = Options()
        
        if self.config.get("headless", False):
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(service=self.driver_service, options=chrome_options)
        driver.set_page_load_timeout(self.config["timeout"])
        
        return driver
    
    def create_account(self, email):
        """Create Facebook account"""
        for attempt in range(self.config["max_retries"]):
            driver = None
            try:
                logging.info(f"[Attempt {attempt + 1}/{self.config['max_retries']}] Creating account for {email}")
                
                driver = self.create_driver()
                
                # Generate random account details
                first_name, last_name = self._generate_random_name()
                password = self._generate_random_password()
                
                # Save credentials to file
                with open('accounts.txt', 'a') as f:
                    f.write(f"{email}:{password}:{first_name} {last_name}\n")
                
                # Navigate to Facebook signup
                driver.get("https://www.facebook.com/")
                time.sleep(3)
                
                # Click "Create new account" button
                try:
                    create_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.LINK_TEXT, "Create new account"))
                    )
                    create_btn.click()
                    time.sleep(2)
                except:
                    logging.warning("Couldn't find 'Create new account' button, trying direct signup URL")
                    driver.get("https://www.facebook.com/reg/")
                    time.sleep(3)
                
                # Fill in the signup form
                logging.info(f"Filling signup form for {email}")
                
                # First name
                first_name_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "firstname"))
                )
                first_name_field.send_keys(first_name)
                time.sleep(0.5)
                
                # Last name
                last_name_field = driver.find_element(By.NAME, "lastname")
                last_name_field.send_keys(last_name)
                time.sleep(0.5)
                
                # Email
                email_field = driver.find_element(By.NAME, "reg_email__")
                email_field.send_keys(email)
                time.sleep(0.5)
                
                # Password
                password_field = driver.find_element(By.NAME, "reg_passwd__")
                password_field.send_keys(password)
                time.sleep(0.5)
                
                # Birthday (random date - must be 18+)
                month_select = driver.find_element(By.NAME, "birthday_month")
                month_select.send_keys(str(random.randint(1, 12)))
                time.sleep(0.3)
                
                day_select = driver.find_element(By.NAME, "birthday_day")
                day_select.send_keys(str(random.randint(1, 28)))
                time.sleep(0.3)
                
                year_select = driver.find_element(By.NAME, "birthday_year")
                year_select.send_keys(str(random.randint(1985, 2002)))
                time.sleep(0.3)
                
                # Gender (random)
                gender_value = random.choice(["1", "2"])  # 1=Female, 2=Male
                gender_radio = driver.find_element(By.CSS_SELECTOR, f"input[value='{gender_value}']")
                gender_radio.click()
                time.sleep(0.5)
                
                logging.info(f"Submitting signup form for {email}")
                
                # Click Sign Up button
                signup_btn = driver.find_element(By.NAME, "websubmit")
                signup_btn.click()
                
                # Wait for account creation (this may require captcha or verification)
                time.sleep(5)
                
                logging.info(f"✅ Account creation initiated for {email} ({first_name} {last_name})")
                self.stats["created"] += 1
                
                # Save account info
                account_info = {
                    "email": email,
                    "password": password,
                    "name": f"{first_name} {last_name}",
                    "created_at": datetime.now().isoformat()
                }
                
                driver.quit()
                
                # Wait before following
                time.sleep(random.uniform(*self.config["delay_range"]))
                
                # Follow target account if specified
                if self.target_account:
                    self.follow_account(email, password, self.target_account)
                
                return True
                
            except Exception as e:
                logging.error(f"❌ Attempt {attempt + 1}/{self.config['max_retries']} failed for {email}: {str(e)}")
                self.stats["errors"] += 1
                
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                
                if attempt < self.config["max_retries"] - 1:
                    logging.info(f"Retrying in {self.config['retry_delay']} seconds...")
                    time.sleep(self.config["retry_delay"])
                else:
                    logging.error(f"❌ Failed to create account for {email} after all retries")
                    return False
        
        return False
    
    def follow_account(self, email, password, target_username):
        """Login and follow a target Facebook account"""
        driver = None
        try:
            logging.info(f"Attempting to follow {target_username} with account {email}")
            
            driver = self.create_driver()
            
            # Login to Facebook
            driver.get("https://www.facebook.com/")
            time.sleep(2)
            
            # Enter email
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.send_keys(email)
            
            # Enter password
            password_field = driver.find_element(By.ID, "pass")
            password_field.send_keys(password)
            
            # Click login
            login_btn = driver.find_element(By.NAME, "login")
            login_btn.click()
            
            time.sleep(5)
            
            # Navigate to target profile
            profile_url = f"https://www.facebook.com/{target_username}"
            driver.get(profile_url)
            time.sleep(3)
            
            # Try to find and click Follow/Add Friend button
            try:
                # Look for "Follow" or "Add Friend" button
                follow_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Follow') or contains(text(), 'Add Friend')]"))
                )
                follow_btn.click()
                time.sleep(2)
                
                logging.info(f"✅ Successfully followed {target_username} with account {email}")
                self.stats["followed"] += 1
                
            except Exception as e:
                logging.warning(f"Could not find follow button for {target_username}: {e}")
            
            driver.quit()
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to follow {target_username} with {email}: {str(e)}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            return False
    
    def run(self):
        """Main execution loop"""
        if not self.emails:
            logging.error("❌ No emails to process. Add emails to email.txt")
            return
        
        logging.info("="*60)
        logging.info(f"🚀 Starting Facebook Automation")
        logging.info(f"📧 Emails to process: {len(self.emails)}")
        if self.target_account:
            logging.info(f"👤 Target account to follow: {self.target_account}")
        logging.info("="*60)
        
        for idx, email in enumerate(self.emails, 1):
            if not self.running:
                break
            
            logging.info(f"\n[{idx}/{len(self.emails)}] Processing: {email}")
            self.create_account(email)
            
            # Delay between accounts
            if idx < len(self.emails):
                delay = random.uniform(*self.config["delay_range"])
                logging.info(f"⏳ Waiting {delay:.1f} seconds before next account...")
                time.sleep(delay)
        
        # Final stats
        duration = (datetime.now() - datetime.fromisoformat(self.stats["start_time"])).total_seconds()
        logging.info("\n" + "="*60)
        logging.info("📊 AUTOMATION COMPLETED")
        logging.info(f"✅ Accounts created: {self.stats['created']}")
        logging.info(f"👥 Accounts followed: {self.stats['followed']}")
        logging.info(f"❌ Errors: {self.stats['errors']}")
        logging.info(f"⏱️  Duration: {duration:.1f} seconds")
        logging.info("="*60)
        logging.info("💾 Account credentials saved to: accounts.txt")
    
    def stop(self):
        """Graceful shutdown"""
        self.running = False
        logging.info("🛑 Stopping automation...")

if __name__ == "__main__":
    print("="*60)
    print("🤖 Facebook Account Automation Bot")
    print("="*60)
    
    # Get target account from user
    target = input("\n👤 Enter Facebook username/profile to follow (or press Enter to skip): ").strip()
    
    if not target:
        target = None
        print("ℹ️  Skipping follow feature - will only create accounts")
    else:
        print(f"✓ Will follow: {target}")
    
    print("\n📝 Make sure you have emails in 'email.txt' file (one per line)")
    input("Press Enter to start...\n")
    
    automation = FacebookAutomation(target_account=target)
    
    try:
        automation.run()
    except KeyboardInterrupt:
        logging.info("\n⚠️  Interrupted by user")
        automation.stop()
    except Exception as e:
        logging.error(f"\n❌ Fatal error: {e}")
        automation.stop()