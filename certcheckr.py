#!/usr/bin/env python3
"""
CertCheckr - Certificate Expiration Monitoring Tool
A tool for monitoring certificate expiration dates and sending notifications via webhook.
"""

import json
import os
import sys
import time
import logging
from datetime import datetime, timedelta
import requests
from pathlib import Path
from urllib.parse import urlparse

# Configure paths
CONFIG_DIR = Path.home() / '.certcheckr'
CONFIG_FILE = CONFIG_DIR / 'config.json'

# Configure logging
LOG_DIR = CONFIG_DIR / 'logs'
LOG_FILE = LOG_DIR / 'certcheckr.log'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Default English translations
ENGLISH = {
    'menu_title': '=== CertCheckr Menu ===',
    'add_cert': '1. Add new certificate',
    'list_certs': '2. List certificates',
    'set_webhook': '3. Set webhook URL',
    'set_days': '4. Set notification days',
    'exit': '5. Exit',
    'enter_choice': '\nEnter your choice (1-5): ',
    'cert_name': 'Enter certificate name: ',
    'expiry_date': 'Enter expiry date (YYYY-MM-DD): ',
    'cert_added': 'Certificate added successfully!',
    'invalid_date': 'Invalid date format. Please use YYYY-MM-DD',
    'no_certs': 'No certificates configured.',
    'webhook_url': 'Enter webhook URL: ',
    'webhook_updated': 'Webhook URL updated!',
    'days_prompt': 'Enter number of days before expiry to notify: ',
    'days_updated': 'Notification days updated!',
    'invalid_number': 'Please enter a valid number.',
    'positive_number': 'Please enter a positive number.',
    'goodbye': 'Goodbye!',
    'invalid_choice': 'Invalid choice. Please try again.',
    'cert_expiring': 'Warning: Certificate {name} expires in {days} days',
    'webhook_error': 'Error sending notification: {error}',
    'cert_alert': '⚠️ Certificate Alert\nCertificate: {name}\nExpires in: {days} days\nExpiry date: {date}'
}

def setup_logging():
    """Set up logging configuration."""
    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_webhook_url(url):
    """Validate webhook URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def load_translations(language='en'):
    """Load translations for the specified language."""
    if language == 'en':
        return ENGLISH
    
    try:
        # Get the actual script location, even when running from symlink
        script_dir = Path(os.path.dirname(os.path.realpath(__file__)))
        translation_file = script_dir / 'translations' / f'{language}.py'
        
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            f"translations.{language}",
            translation_file
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.TRANSLATIONS
    except Exception as e:
        logging.warning(f"Failed to load translations for {language}: {e}")
    
    return ENGLISH

class CertChecker:
    def __init__(self, language='en'):
        self.logger = setup_logging()
        self.logger.info("Initializing CertChecker")
        self.translations = load_translations(language)
        self.config = self.load_config()
        self.webhook_url = self.config.get('webhook_url', '')
        self.notification_days = self.config.get('notification_days', 7)
        self.certificates = self.config.get('certificates', [])

    def load_config(self):
        """Load configuration from file or create default if not exists."""
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir(parents=True)
        
        if not CONFIG_FILE.exists():
            default_config = {
                'webhook_url': '',
                'notification_days': 7,
                'certificates': []
            }
            self.save_config(default_config)
            return default_config
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {
                'webhook_url': '',
                'notification_days': 7,
                'certificates': []
            }

    def save_config(self, config=None):
        """Save current configuration to file."""
        if config is None:
            config = self.config
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def add_certificate(self, name, expiry_date):
        """Add a new certificate to monitor."""
        try:
            self.certificates.append({
                'name': name,
                'expiry_date': expiry_date,
                'added_by': os.getenv('USER', 'unknown'),
                'added_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            self.config['certificates'] = self.certificates
            self.save_config()
            self.logger.info(f"Added certificate: {name} (expires: {expiry_date})")
        except Exception as e:
            self.logger.error(f"Error adding certificate: {e}")

    def check_certificates(self):
        """Check all certificates and send notifications if needed."""
        for cert in self.certificates:
            try:
                expiry_date = datetime.strptime(cert['expiry_date'], '%Y-%m-%d')
                days_until_expiry = (expiry_date - datetime.now()).days
                
                if 0 < days_until_expiry <= self.notification_days:
                    self.send_notification(cert, days_until_expiry)
            except Exception as e:
                self.logger.error(f"Error checking certificate {cert.get('name', 'unknown')}: {e}")

    def send_notification(self, cert, days_until_expiry):
        """Send notification via webhook."""
        if not self.webhook_url:
            self.logger.warning(self.translations['cert_expiring'].format(
                name=cert['name'],
                days=days_until_expiry
            ))
            return

        message = {
            'text': self.translations['cert_alert'].format(
                name=cert['name'],
                days=days_until_expiry,
                date=cert['expiry_date']
            )
        }

        try:
            response = requests.post(self.webhook_url, json=message)
            response.raise_for_status()
            self.logger.info(f"Notification sent for certificate: {cert['name']}")
        except Exception as e:
            self.logger.error(self.translations['webhook_error'].format(error=str(e)))

    def interactive_menu(self):
        """Display and handle the interactive menu."""
        while True:
            print(f"\n{self.translations['menu_title']}")
            print(self.translations['add_cert'])
            print(self.translations['list_certs'])
            print(self.translations['set_webhook'])
            print(self.translations['set_days'])
            print(self.translations['exit'])
            
            choice = input(self.translations['enter_choice'])
            
            if choice == '1':
                name = input(self.translations['cert_name'])
                expiry_date = input(self.translations['expiry_date'])
                try:
                    datetime.strptime(expiry_date, '%Y-%m-%d')
                    self.add_certificate(name, expiry_date)
                    print(self.translations['cert_added'])
                except ValueError:
                    print(self.translations['invalid_date'])
            
            elif choice == '2':
                if not self.certificates:
                    print(self.translations['no_certs'])
                else:
                    print("\nConfigured Certificates:")
                    for cert in self.certificates:
                        print(f"- {cert['name']} (Expires: {cert['expiry_date']})")
            
            elif choice == '3':
                url = input(self.translations['webhook_url'])
                if validate_webhook_url(url):
                    self.webhook_url = url
                    self.config['webhook_url'] = url
                    self.save_config()
                    print(self.translations['webhook_updated'])
                else:
                    print("Invalid webhook URL format")
            
            elif choice == '4':
                try:
                    days = int(input(self.translations['days_prompt']))
                    if days > 0:
                        self.notification_days = days
                        self.config['notification_days'] = days
                        self.save_config()
                        print(self.translations['days_updated'])
                    else:
                        print(self.translations['positive_number'])
                except ValueError:
                    print(self.translations['invalid_number'])
            
            elif choice == '5':
                print(self.translations['goodbye'])
                sys.exit(0)
            
            else:
                print(self.translations['invalid_choice'])

def main():
    # Get language from environment variable or default to English
    language = os.getenv('CERTCHECKR_LANG', 'en')
    checker = CertChecker(language)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        # Run in daemon mode
        while True:
            checker.check_certificates()
            time.sleep(86400)  # Check once per day
    else:
        # Run interactive menu
        checker.interactive_menu()

if __name__ == '__main__':
    main() 