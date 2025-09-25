# Security Guide

This guide covers security best practices, threat mitigation, and secure deployment for ForexSmartBot.

## Table of Contents

- [Security Overview](#security-overview)
- [Threat Model](#threat-model)
- [Secure Configuration](#secure-configuration)
- [Data Protection](#data-protection)
- [Network Security](#network-security)
- [Application Security](#application-security)
- [Deployment Security](#deployment-security)
- [Monitoring & Incident Response](#monitoring--incident-response)
- [Compliance & Auditing](#compliance--auditing)

## Security Overview

### Security Principles

1. **Defense in Depth**: Multiple layers of security
2. **Least Privilege**: Minimum necessary permissions
3. **Fail Secure**: Secure by default
4. **Security by Design**: Built-in security features
5. **Regular Updates**: Keep dependencies current

### Security Features

- **Local Data Storage**: No sensitive data transmitted externally
- **Input Validation**: Comprehensive input sanitization
- **Error Handling**: Secure error messages
- **Access Control**: User permission management
- **Audit Logging**: Comprehensive security logging

## Threat Model

### Potential Threats

1. **Data Theft**: Unauthorized access to trading data
2. **API Key Theft**: Compromise of broker credentials
3. **Man-in-the-Middle**: Network interception
4. **Malware**: System compromise
5. **Social Engineering**: Human factor exploitation
6. **Insider Threats**: Authorized user misuse

### Attack Vectors

1. **Network Attacks**: Packet sniffing, DNS spoofing
2. **Application Attacks**: SQL injection, XSS
3. **System Attacks**: Privilege escalation, rootkits
4. **Physical Attacks**: Device theft, unauthorized access
5. **Social Engineering**: Phishing, pretexting

### Risk Assessment

| Threat | Likelihood | Impact | Risk Level | Mitigation |
|--------|------------|--------|------------|------------|
| Data Theft | Medium | High | High | Encryption, Access Control |
| API Key Theft | Low | High | Medium | Secure Storage, Rotation |
| Network Attacks | Medium | Medium | Medium | VPN, TLS |
| Malware | Low | High | Medium | Antivirus, Updates |
| Social Engineering | High | Medium | High | Training, Awareness |

## Secure Configuration

### Environment Variables

1. **Store sensitive data in environment variables**:
   ```bash
   # Set environment variables
   export FOREXSMARTBOT_API_KEY="your_api_key_here"
   export FOREXSMARTBOT_MT4_HOST="localhost"
   export FOREXSMARTBOT_MT4_PORT="5555"
   export FOREXSMARTBOT_LOG_LEVEL="INFO"
   ```

2. **Use .env files for development**:
   ```bash
   # .env file (never commit to version control)
   FOREXSMARTBOT_API_KEY=your_api_key_here
   FOREXSMARTBOT_MT4_HOST=localhost
   FOREXSMARTBOT_MT4_PORT=5555
   ```

3. **Load environment variables securely**:
   ```python
   import os
   from dotenv import load_dotenv
   
   # Load .env file
   load_dotenv()
   
   # Get environment variables
   api_key = os.getenv('FOREXSMARTBOT_API_KEY')
   if not api_key:
       raise ValueError("API key not found in environment variables")
   ```

### Configuration Security

1. **Validate configuration**:
   ```python
   from pydantic import BaseModel, validator
   
   class SecurityConfig(BaseModel):
       api_key: str
       mt4_host: str
       mt4_port: int
       
       @validator('api_key')
       def validate_api_key(cls, v):
           if len(v) < 32:
               raise ValueError('API key must be at least 32 characters')
           return v
       
       @validator('mt4_port')
       def validate_port(cls, v):
           if not 1 <= v <= 65535:
               raise ValueError('Port must be between 1 and 65535')
           return v
   ```

2. **Use secure defaults**:
   ```python
   class SecureConfig:
       # Secure defaults
       DEFAULT_LOG_LEVEL = "INFO"
       DEFAULT_TIMEOUT = 30
       DEFAULT_RETRY_COUNT = 3
       
       # Security settings
       REQUIRE_HTTPS = True
       ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
       MAX_REQUEST_SIZE = 1024 * 1024  # 1MB
   ```

## Data Protection

### Data Encryption

1. **Encrypt sensitive data at rest**:
   ```python
   from cryptography.fernet import Fernet
   import base64
   
   class DataEncryption:
       def __init__(self, key=None):
           if key is None:
               key = Fernet.generate_key()
           self.cipher = Fernet(key)
       
       def encrypt(self, data):
           return self.cipher.encrypt(data.encode())
       
       def decrypt(self, encrypted_data):
           return self.cipher.decrypt(encrypted_data).decode()
   ```

2. **Encrypt database files**:
   ```python
   import sqlite3
   from cryptography.fernet import Fernet
   
   class EncryptedDatabase:
       def __init__(self, db_path, encryption_key):
           self.encryption_key = encryption_key
           self.db_path = db_path
       
       def encrypt_data(self, data):
           cipher = Fernet(self.encryption_key)
           return cipher.encrypt(data.encode())
       
       def decrypt_data(self, encrypted_data):
           cipher = Fernet(self.encryption_key)
           return cipher.decrypt(encrypted_data).decode()
   ```

3. **Use secure file permissions**:
   ```python
   import os
   import stat
   
   def secure_file_permissions(file_path):
       # Set restrictive permissions (owner read/write only)
       os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
   ```

### Data Sanitization

1. **Sanitize user input**:
   ```python
   import re
   import html
   
   def sanitize_input(user_input):
       # Remove potentially dangerous characters
       sanitized = re.sub(r'[<>"\']', '', user_input)
       
       # HTML escape
       sanitized = html.escape(sanitized)
       
       # Limit length
       sanitized = sanitized[:1000]
       
       return sanitized
   ```

2. **Validate data types**:
   ```python
   def validate_trade_data(data):
       required_fields = ['symbol', 'side', 'quantity', 'price']
       
       for field in required_fields:
           if field not in data:
               raise ValueError(f"Missing required field: {field}")
       
       # Validate symbol format
       if not re.match(r'^[A-Z]{6}$', data['symbol']):
           raise ValueError("Invalid symbol format")
       
       # Validate side
       if data['side'] not in [-1, 1]:
           raise ValueError("Side must be -1 or 1")
       
       # Validate quantity
       if not isinstance(data['quantity'], (int, float)) or data['quantity'] <= 0:
           raise ValueError("Quantity must be a positive number")
       
       return data
   ```

### Data Retention

1. **Implement data retention policies**:
   ```python
   import datetime
   
   class DataRetention:
       def __init__(self, retention_days=365):
           self.retention_days = retention_days
       
       def cleanup_old_data(self):
           cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
           
           # Delete old trades
           self.delete_old_trades(cutoff_date)
           
           # Delete old logs
           self.delete_old_logs(cutoff_date)
       
       def delete_old_trades(self, cutoff_date):
           conn = sqlite3.connect('trades.db')
           cursor = conn.cursor()
           cursor.execute("DELETE FROM trades WHERE entry_time < ?", (cutoff_date,))
           conn.commit()
           conn.close()
   ```

2. **Secure data deletion**:
   ```python
   import os
   import random
   
   def secure_delete_file(file_path):
       # Overwrite file with random data multiple times
       with open(file_path, 'r+b') as f:
           file_size = os.path.getsize(file_path)
           for _ in range(3):
               f.seek(0)
               f.write(os.urandom(file_size))
               f.flush()
               os.fsync(f.fileno())
       
       # Delete file
       os.remove(file_path)
   ```

## Network Security

### Secure Communication

1. **Use TLS for all communications**:
   ```python
   import ssl
   import socket
   
   def create_secure_socket(host, port):
       context = ssl.create_default_context()
       context.check_hostname = True
       context.verify_mode = ssl.CERT_REQUIRED
       
       sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       secure_sock = context.wrap_socket(sock, server_hostname=host)
       secure_sock.connect((host, port))
       
       return secure_sock
   ```

2. **Validate SSL certificates**:
   ```python
   import ssl
   import socket
   
   def validate_ssl_certificate(hostname, port):
       context = ssl.create_default_context()
       
       with socket.create_connection((hostname, port)) as sock:
           with context.wrap_socket(sock, server_hostname=hostname) as ssock:
               cert = ssock.getpeercert()
               
               # Check certificate validity
               if not cert:
                   raise ssl.SSLError("No certificate received")
               
               # Check hostname
               ssl.match_hostname(cert, hostname)
   ```

### VPN and Tunneling

1. **Use VPN for remote access**:
   ```bash
   # OpenVPN configuration
   client
   dev tun
   proto udp
   remote your-vpn-server.com 1194
   resolv-retry infinite
   nobind
   persist-key
   persist-tun
   ca ca.crt
   cert client.crt
   key client.key
   cipher AES-256-CBC
   ```

2. **Use SSH tunneling**:
   ```bash
   # SSH tunnel for secure communication
   ssh -L 5555:localhost:5555 user@remote-server
   ```

### Firewall Configuration

1. **Configure firewall rules**:
   ```bash
   # UFW firewall configuration
   sudo ufw default deny incoming
   sudo ufw default allow outgoing
   sudo ufw allow ssh
   sudo ufw allow 5555/tcp  # MT4 port
   sudo ufw enable
   ```

2. **Use iptables for advanced rules**:
   ```bash
   # iptables rules
   iptables -A INPUT -i lo -j ACCEPT
   iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
   iptables -A INPUT -p tcp --dport 22 -j ACCEPT
   iptables -A INPUT -p tcp --dport 5555 -j ACCEPT
   iptables -A INPUT -j DROP
   ```

## Application Security

### Input Validation

1. **Validate all inputs**:
   ```python
   from pydantic import BaseModel, validator
   import re
   
   class TradeInput(BaseModel):
       symbol: str
       side: int
       quantity: float
       price: float
       
       @validator('symbol')
       def validate_symbol(cls, v):
           if not re.match(r'^[A-Z]{6}$', v):
               raise ValueError('Invalid symbol format')
           return v
       
       @validator('side')
       def validate_side(cls, v):
           if v not in [-1, 1]:
               raise ValueError('Side must be -1 or 1')
           return v
       
       @validator('quantity')
       def validate_quantity(cls, v):
           if v <= 0:
               raise ValueError('Quantity must be positive')
           return v
   ```

2. **Sanitize file uploads**:
   ```python
   import os
   import magic
   
   def validate_file_upload(file_path):
       # Check file type
       file_type = magic.from_file(file_path, mime=True)
       allowed_types = ['text/csv', 'application/json']
       
       if file_type not in allowed_types:
           raise ValueError('Invalid file type')
       
       # Check file size
       file_size = os.path.getsize(file_path)
       max_size = 10 * 1024 * 1024  # 10MB
       
       if file_size > max_size:
           raise ValueError('File too large')
   ```

### Authentication and Authorization

1. **Implement API key authentication**:
   ```python
   import hashlib
   import hmac
   import time
   
   class APIKeyAuth:
       def __init__(self, secret_key):
           self.secret_key = secret_key
       
       def generate_signature(self, message):
           return hmac.new(
               self.secret_key.encode(),
               message.encode(),
               hashlib.sha256
           ).hexdigest()
       
       def verify_signature(self, message, signature):
           expected_signature = self.generate_signature(message)
           return hmac.compare_digest(expected_signature, signature)
   ```

2. **Implement role-based access control**:
   ```python
   from enum import Enum
   
   class Role(Enum):
       ADMIN = "admin"
       TRADER = "trader"
       VIEWER = "viewer"
   
   class AccessControl:
       def __init__(self):
           self.permissions = {
               Role.ADMIN: ["read", "write", "delete", "admin"],
               Role.TRADER: ["read", "write"],
               Role.VIEWER: ["read"]
           }
       
       def has_permission(self, user_role, action):
           return action in self.permissions.get(user_role, [])
   ```

### Error Handling

1. **Secure error messages**:
   ```python
   import logging
   
   class SecureErrorHandler:
       def __init__(self):
           self.logger = logging.getLogger('security')
       
       def handle_error(self, error, user_message="An error occurred"):
           # Log detailed error for debugging
           self.logger.error(f"Error: {str(error)}", exc_info=True)
           
           # Return generic message to user
           return user_message
   ```

2. **Avoid information disclosure**:
   ```python
   def safe_error_response(error):
       # Don't expose internal details
       if isinstance(error, ValueError):
           return "Invalid input provided"
       elif isinstance(error, PermissionError):
           return "Access denied"
       else:
           return "An error occurred"
   ```

## Deployment Security

### Secure Deployment

1. **Use secure containers**:
   ```dockerfile
   FROM python:3.11-slim
   
   # Create non-root user
   RUN groupadd -r forexsmartbot && useradd -r -g forexsmartbot forexsmartbot
   
   # Set working directory
   WORKDIR /app
   
   # Copy requirements and install
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy application
   COPY . .
   
   # Change ownership
   RUN chown -R forexsmartbot:forexsmartbot /app
   
   # Switch to non-root user
   USER forexsmartbot
   
   # Expose port
   EXPOSE 8080
   
   # Start application
   CMD ["python", "app.py"]
   ```

2. **Use secrets management**:
   ```yaml
   # docker-compose.yml
   version: '3.8'
   services:
     forexsmartbot:
       build: .
       environment:
         - API_KEY_FILE=/run/secrets/api_key
       secrets:
         - api_key
   
   secrets:
     api_key:
       file: ./secrets/api_key.txt
   ```

### System Hardening

1. **Disable unnecessary services**:
   ```bash
   # Disable unnecessary services
   sudo systemctl disable bluetooth
   sudo systemctl disable cups
   sudo systemctl disable avahi-daemon
   ```

2. **Configure secure defaults**:
   ```bash
   # Set secure kernel parameters
   echo 'net.ipv4.conf.all.send_redirects = 0' >> /etc/sysctl.conf
   echo 'net.ipv4.conf.default.send_redirects = 0' >> /etc/sysctl.conf
   echo 'net.ipv4.conf.all.accept_redirects = 0' >> /etc/sysctl.conf
   echo 'net.ipv4.conf.default.accept_redirects = 0' >> /etc/sysctl.conf
   ```

3. **Use AppArmor or SELinux**:
   ```bash
   # AppArmor configuration
   sudo apt install apparmor-utils
   sudo aa-enforce /usr/bin/python3
   ```

### Backup Security

1. **Encrypt backups**:
   ```bash
   # Encrypt backup files
   tar -czf - ~/.forexsmartbot | gpg --symmetric --cipher-algo AES256 -o backup.tar.gz.gpg
   ```

2. **Secure backup storage**:
   ```bash
   # Store backups in secure location
   sudo mkdir -p /secure/backups
   sudo chmod 700 /secure/backups
   sudo chown root:root /secure/backups
   ```

## Monitoring & Incident Response

### Security Monitoring

1. **Implement security logging**:
   ```python
   import logging
   import json
   from datetime import datetime
   
   class SecurityLogger:
       def __init__(self):
           self.logger = logging.getLogger('security')
           handler = logging.FileHandler('security.log')
           formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
           handler.setFormatter(formatter)
           self.logger.addHandler(handler)
           self.logger.setLevel(logging.INFO)
       
       def log_security_event(self, event_type, details):
           event = {
               'timestamp': datetime.now().isoformat(),
               'event_type': event_type,
               'details': details
           }
           self.logger.info(json.dumps(event))
   ```

2. **Monitor for suspicious activity**:
   ```python
   class SecurityMonitor:
       def __init__(self):
           self.failed_attempts = {}
           self.max_attempts = 5
           self.lockout_duration = 300  # 5 minutes
       
       def check_failed_attempts(self, user_id):
           now = time.time()
           if user_id in self.failed_attempts:
               attempts = self.failed_attempts[user_id]
               # Remove old attempts
               attempts = [t for t in attempts if now - t < self.lockout_duration]
               
               if len(attempts) >= self.max_attempts:
                   return False  # Account locked
               
               self.failed_attempts[user_id] = attempts
           
           return True
   ```

### Incident Response

1. **Create incident response plan**:
   ```python
   class IncidentResponse:
       def __init__(self):
           self.incidents = []
       
       def report_incident(self, incident_type, severity, description):
           incident = {
               'id': len(self.incidents) + 1,
               'type': incident_type,
               'severity': severity,
               'description': description,
               'timestamp': datetime.now().isoformat(),
               'status': 'open'
           }
           self.incidents.append(incident)
           self.notify_security_team(incident)
       
       def notify_security_team(self, incident):
           # Send notification to security team
           pass
   ```

2. **Implement automated response**:
   ```python
   def automated_response(incident):
       if incident['type'] == 'brute_force':
           # Block IP address
           block_ip(incident['source_ip'])
       elif incident['type'] == 'malware':
           # Isolate system
           isolate_system()
       elif incident['type'] == 'data_breach':
           # Notify users
           notify_users()
   ```

## Compliance & Auditing

### Security Auditing

1. **Implement audit logging**:
   ```python
   class AuditLogger:
       def __init__(self):
           self.logger = logging.getLogger('audit')
           handler = logging.FileHandler('audit.log')
           formatter = logging.Formatter('%(asctime)s - %(message)s')
           handler.setFormatter(formatter)
           self.logger.addHandler(handler)
           self.logger.setLevel(logging.INFO)
       
       def log_audit_event(self, user, action, resource, result):
           event = f"User: {user}, Action: {action}, Resource: {resource}, Result: {result}"
           self.logger.info(event)
   ```

2. **Regular security assessments**:
   ```python
   class SecurityAssessment:
       def __init__(self):
           self.checks = []
       
       def add_check(self, check_name, check_function):
           self.checks.append((check_name, check_function))
       
       def run_assessment(self):
           results = {}
           for check_name, check_function in self.checks:
               try:
                   result = check_function()
                   results[check_name] = result
               except Exception as e:
                   results[check_name] = f"Error: {str(e)}"
           return results
   ```

### Compliance Requirements

1. **GDPR Compliance**:
   ```python
   class GDPRCompliance:
       def __init__(self):
           self.data_subjects = {}
       
       def register_data_subject(self, subject_id, data):
           self.data_subjects[subject_id] = {
               'data': data,
               'consent': False,
               'retention_date': None
           }
       
       def request_data_deletion(self, subject_id):
           if subject_id in self.data_subjects:
               del self.data_subjects[subject_id]
               self.audit_logger.log_audit_event(
                   'system', 'data_deletion', subject_id, 'success'
               )
   ```

2. **SOX Compliance**:
   ```python
   class SOXCompliance:
       def __init__(self):
           self.controls = {}
       
       def implement_control(self, control_id, control_function):
           self.controls[control_id] = control_function
       
       def test_controls(self):
           results = {}
           for control_id, control_function in self.controls.items():
               result = control_function()
               results[control_id] = result
           return results
   ```

## Security Best Practices

### General Security

1. **Keep software updated**:
   ```bash
   # Regular updates
   sudo apt update && sudo apt upgrade -y
   pip install --upgrade -r requirements.txt
   ```

2. **Use strong passwords**:
   ```python
   import secrets
   import string
   
   def generate_strong_password(length=16):
       alphabet = string.ascii_letters + string.digits + string.punctuation
       return ''.join(secrets.choice(alphabet) for _ in range(length))
   ```

3. **Implement two-factor authentication**:
   ```python
   import pyotp
   import qrcode
   
   class TwoFactorAuth:
       def __init__(self):
           self.secret = pyotp.random_base32()
       
       def generate_qr_code(self, user_email):
           totp = pyotp.TOTP(self.secret)
           qr_data = totp.provisioning_uri(
               name=user_email,
               issuer_name="ForexSmartBot"
           )
           return qrcode.make(qr_data)
       
       def verify_token(self, token):
           totp = pyotp.TOTP(self.secret)
           return totp.verify(token)
   ```

### Development Security

1. **Secure coding practices**:
   - Always validate input
   - Use parameterized queries
   - Implement proper error handling
   - Follow principle of least privilege
   - Keep dependencies updated

2. **Code review process**:
   - Review all security-sensitive code
   - Use automated security scanning
   - Implement peer review requirements
   - Document security decisions

3. **Testing security**:
   - Include security tests in CI/CD
   - Perform penetration testing
   - Use vulnerability scanning
   - Test incident response procedures

## Security Checklist

### Pre-Deployment

- [ ] All sensitive data encrypted
- [ ] Input validation implemented
- [ ] Error handling secure
- [ ] Dependencies updated
- [ ] Security tests passing
- [ ] Access controls configured
- [ ] Logging implemented
- [ ] Backup procedures tested

### Post-Deployment

- [ ] Monitor security logs
- [ ] Regular security updates
- [ ] Incident response tested
- [ ] Access reviews conducted
- [ ] Vulnerability assessments
- [ ] Penetration testing
- [ ] Compliance audits
- [ ] Security training

## Conclusion

Security is a critical aspect of ForexSmartBot that requires:

1. **Continuous attention**: Security is not a one-time task
2. **Layered approach**: Multiple security controls
3. **Regular updates**: Keep systems current
4. **Monitoring**: Continuous security monitoring
5. **Training**: Educate users and developers

Remember that security is a shared responsibility between developers, administrators, and users. Everyone must play their part in maintaining a secure environment.

---

**Note**: This guide provides general security recommendations. Always consult with security professionals and follow your organization's security policies and procedures.
