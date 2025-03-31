# CertCheckr

A simple certificate expiration monitoring tool that runs on Ubuntu servers. It checks when certificates are about to expire and sends notifications via webhook.

## Features

- Interactive menu for managing certificates
- Webhook notifications for certificate expiration
- Configurable notification period
- Runs as a system service
- Starts automatically on system boot

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/certcheckr.git
cd certcheckr
```

2. Install the required dependencies:
```bash
pip3 install -r requirements.txt
```

3. Copy the program to a system-wide location:
```bash
sudo cp certcheckr.py /usr/local/bin/
sudo chmod +x /usr/local/bin/certcheckr.py
```

4. Install the systemd service:
```bash
sudo cp certcheckr.service /etc/systemd/system/
sudo systemctl daemon-reload
```

5. Enable and start the service (replace USERNAME with your system username):
```bash
sudo systemctl enable certcheckr@USERNAME
sudo systemctl start certcheckr@USERNAME
```

## Usage

### Interactive Mode
Run the program in interactive mode to manage certificates:
```bash
certcheckr.py
```

### Service Management
- Check service status:
```bash
sudo systemctl status certcheckr@USERNAME
```

- Stop the service:
```bash
sudo systemctl stop certcheckr@USERNAME
```

- Start the service:
```bash
sudo systemctl start certcheckr@USERNAME
```

## Configuration

The program stores its configuration in `~/.certcheckr/config.json`. You can configure:
- Webhook URL for notifications
- Number of days before expiry to send notifications
- List of certificates to monitor

## License

This project is licensed under the MIT License - see the LICENSE file for details.
