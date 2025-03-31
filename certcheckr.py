#!/usr/bin/env python3
import json
import os
import sys
import time
from datetime import datetime, timedelta
import requests
from pathlib import Path

CONFIG_FILE = Path.home() / '.certcheckr' / 'config.json'
CONFIG_DIR = CONFIG_FILE.parent

class CertChecker:
    def __init__(self):
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
        
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)

    def save_config(self):
        """Save current configuration to file."""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def add_certificate(self, name, expiry_date):
        """Add a new certificate to monitor."""
        self.certificates.append({
            'name': name,
            'expiry_date': expiry_date
        })
        self.config['certificates'] = self.certificates
        self.save_config()

    def check_certificates(self):
        """Check all certificates and send notifications if needed."""
        for cert in self.certificates:
            expiry_date = datetime.strptime(cert['expiry_date'], '%Y-%m-%d')
            days_until_expiry = (expiry_date - datetime.now()).days
            
            if 0 < days_until_expiry <= self.notification_days:
                self.send_notification(cert, days_until_expiry)

    def send_notification(self, cert, days_until_expiry):
        """Send notification via webhook."""
        if not self.webhook_url:
            print(f"Warning: Certificate {cert['name']} expires in {days_until_expiry} days")
            return

        message = {
            'text': f"⚠️ Certificate Alert\n"
                   f"Certificate: {cert['name']}\n"
                   f"Expires in: {days_until_expiry} days\n"
                   f"Expiry date: {cert['expiry_date']}"
        }

        try:
            requests.post(self.webhook_url, json=message)
        except Exception as e:
            print(f"Error sending notification: {e}")

    def interactive_menu(self):
        """Display and handle the interactive menu."""
        while True:
            print("\n=== CertCheckr Menu ===")
            print("1. Add new certificate")
            print("2. List certificates")
            print("3. Set webhook URL")
            print("4. Set notification days")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ")
            
            if choice == '1':
                name = input("Enter certificate name: ")
                expiry_date = input("Enter expiry date (YYYY-MM-DD): ")
                try:
                    datetime.strptime(expiry_date, '%Y-%m-%d')
                    self.add_certificate(name, expiry_date)
                    print("Certificate added successfully!")
                except ValueError:
                    print("Invalid date format. Please use YYYY-MM-DD")
            
            elif choice == '2':
                if not self.certificates:
                    print("No certificates configured.")
                else:
                    print("\nConfigured Certificates:")
                    for cert in self.certificates:
                        print(f"- {cert['name']} (Expires: {cert['expiry_date']})")
            
            elif choice == '3':
                self.webhook_url = input("Enter webhook URL: ")
                self.config['webhook_url'] = self.webhook_url
                self.save_config()
                print("Webhook URL updated!")
            
            elif choice == '4':
                try:
                    days = int(input("Enter number of days before expiry to notify: "))
                    if days > 0:
                        self.notification_days = days
                        self.config['notification_days'] = days
                        self.save_config()
                        print("Notification days updated!")
                    else:
                        print("Please enter a positive number.")
                except ValueError:
                    print("Please enter a valid number.")
            
            elif choice == '5':
                print("Goodbye!")
                sys.exit(0)
            
            else:
                print("Invalid choice. Please try again.")

def main():
    checker = CertChecker()
    
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