# Security Best Practices - ForexSmartBot v3.1.0

Security guidelines for using ForexSmartBot in production.

## 🔒 General Security

### 1. Credential Management

**❌ Never hardcode credentials:**
```python
# BAD
api_key = "sk-1234567890abcdef"
password = "mypassword"
```

**✅ Use environment variables:**
```python
# GOOD
import os
api_key = os.getenv('API_KEY')
password = os.getenv('PASSWORD')
```

**✅ Use .env files:**
```python
# .env file (not in git)
API_KEY=sk-1234567890abcdef
PASSWORD=mypassword

# In code
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('API_KEY')
```

### 2. File Permissions

**Set appropriate file permissions:**
```bash
# Configuration files
chmod 600 config/secrets.json

# Log files
chmod 644 logs/*.log

# Scripts
chmod 755 scripts/*.py
```

### 3. Input Validation

**Always validate user input:**
```python
def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol."""
    if not symbol or len(symbol) > 20:
        return False
    # Check format
    if not re.match(r'^[A-Z]{3,6}(=X)?$', symbol):
        return False
    return True

# Use validation
if not validate_symbol(user_input):
    raise ValueError("Invalid symbol")
```

### 4. SQL Injection Prevention

**If using databases, use parameterized queries:**
```python
# BAD
query = f"SELECT * FROM trades WHERE symbol = '{symbol}'"

# GOOD
query = "SELECT * FROM trades WHERE symbol = ?"
cursor.execute(query, (symbol,))
```

## 🔐 API Security

### 1. API Keys

**Store securely:**
```python
# Use keyring for secure storage
import keyring

# Store
keyring.set_password("forexsmartbot", "api_key", api_key)

# Retrieve
api_key = keyring.get_password("forexsmartbot", "api_key")
```

### 2. Rate Limiting

**Implement rate limiting:**
```python
from functools import wraps
import time

def rate_limit(calls_per_second):
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

@rate_limit(10)  # 10 calls per second
def api_call():
    # Your API call
    pass
```

### 3. HTTPS Only

**Always use HTTPS for API calls:**
```python
# GOOD
url = "https://api.example.com/data"

# BAD
url = "http://api.example.com/data"  # Insecure
```

## 🛡️ Data Security

### 1. Sensitive Data Encryption

**Encrypt sensitive data:**
```python
from cryptography.fernet import Fernet

# Generate key (store securely)
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt
encrypted = cipher.encrypt(b"sensitive data")

# Decrypt
decrypted = cipher.decrypt(encrypted)
```

### 2. Data Sanitization

**Sanitize data before storage:**
```python
import html

# Sanitize user input
user_input = html.escape(user_input)

# Validate data types
if not isinstance(value, (int, float)):
    raise TypeError("Invalid data type")
```

### 3. Secure File Storage

**Use secure file storage:**
```python
import os
import stat

# Create secure file
with open('secrets.json', 'w') as f:
    f.write(secrets)
    
# Set permissions
os.chmod('secrets.json', stat.S_IRUSR | stat.S_IWUSR)  # 600
```

## 🔑 Authentication & Authorization

### 1. Password Security

**Use strong passwords:**
```python
import secrets
import string

def generate_password(length=16):
    """Generate secure random password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))
```

### 2. Token Management

**Use secure tokens:**
```python
import secrets

# Generate secure token
token = secrets.token_urlsafe(32)

# Store securely (not in code)
# Use environment variables or secure storage
```

### 3. Session Management

**Secure session handling:**
```python
import secrets
from datetime import datetime, timedelta

class Session:
    def __init__(self, user_id):
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.expires = datetime.now() + timedelta(hours=1)
    
    def is_valid(self):
        return datetime.now() < self.expires
```

## 🚨 Error Handling

### 1. Don't Expose Sensitive Information

**❌ Bad error messages:**
```python
# BAD
raise Exception(f"API key {api_key} is invalid")
```

**✅ Safe error messages:**
```python
# GOOD
raise ValueError("Invalid API credentials")
```

### 2. Logging Security

**Don't log sensitive data:**
```python
# BAD
logger.info(f"API key: {api_key}")

# GOOD
logger.info("API authentication successful")
```

### 3. Exception Handling

**Handle exceptions securely:**
```python
try:
    # Sensitive operation
    result = process_data(data)
except Exception as e:
    # Log error without sensitive data
    logger.error(f"Processing failed: {type(e).__name__}")
    # Don't expose stack traces in production
    if DEBUG_MODE:
        raise
    else:
        return None
```

## 🔍 Security Auditing

### 1. Dependency Scanning

**Scan for vulnerabilities:**
```bash
# Using pip-audit
pip install pip-audit
pip-audit

# Using safety
pip install safety
safety check
```

### 2. Code Analysis

**Use security linters:**
```bash
# Bandit for security issues
pip install bandit
bandit -r forexsmartbot/

# Pylint security checks
pylint --enable=security forexsmartbot/
```

### 3. Regular Updates

**Keep dependencies updated:**
```bash
# Check for updates
pip list --outdated

# Update securely
pip install --upgrade package-name
```

## 🛡️ Network Security

### 1. Firewall Configuration

**Restrict network access:**
- Only allow necessary ports
- Block unnecessary services
- Use VPN for remote access

### 2. SSL/TLS

**Always use encrypted connections:**
```python
import ssl

# Verify SSL certificates
context = ssl.create_default_context()
context.check_hostname = True
context.verify_mode = ssl.CERT_REQUIRED
```

### 3. Network Monitoring

**Monitor network activity:**
```python
import logging

# Log network requests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('requests')
logger.setLevel(logging.INFO)
```

## 🔐 Marketplace Security

### 1. Strategy Validation

**Validate strategies before sharing:**
```python
from forexsmartbot.builder import StrategyBuilder

builder = StrategyBuilder()
# ... build strategy ...

# Validate before sharing
is_valid, errors = builder.validate_strategy()
if not is_valid:
    raise ValueError(f"Strategy validation failed: {errors}")
```

### 2. Code Review

**Review shared strategies:**
- Check for malicious code
- Verify functionality
- Test thoroughly
- Review dependencies

### 3. Sandbox Execution

**Run strategies in sandbox:**
```python
# Use restricted execution environment
# (Future feature: Strategy sandbox)
```

## 🔒 Production Deployment

### 1. Environment Separation

**Separate environments:**
- Development
- Staging
- Production

**Use different credentials for each:**
```python
ENV = os.getenv('ENVIRONMENT', 'development')

if ENV == 'production':
    api_key = os.getenv('PROD_API_KEY')
else:
    api_key = os.getenv('DEV_API_KEY')
```

### 2. Access Control

**Implement access control:**
```python
def require_permission(permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not has_permission(permission):
                raise PermissionError("Access denied")
            return func(*args, **kwargs)
        return wrapper
    return decorator

@require_permission('trade')
def execute_trade():
    # Trading logic
    pass
```

### 3. Audit Logging

**Log all sensitive operations:**
```python
import logging

audit_logger = logging.getLogger('audit')

def log_trade(trade_details):
    audit_logger.info(f"Trade executed: {trade_details}")
    # Don't log sensitive data like API keys
```

## 📋 Security Checklist

### Pre-Deployment
- [ ] All credentials in environment variables
- [ ] No hardcoded secrets
- [ ] Dependencies scanned for vulnerabilities
- [ ] Code reviewed for security issues
- [ ] SSL/TLS enabled
- [ ] Firewall configured
- [ ] Access control implemented
- [ ] Audit logging enabled

### Runtime
- [ ] Monitor for suspicious activity
- [ ] Regular security updates
- [ ] Backup encryption enabled
- [ ] Log rotation configured
- [ ] Error messages don't expose sensitive data

### Post-Deployment
- [ ] Regular security audits
- [ ] Dependency updates
- [ ] Access review
- [ ] Incident response plan
- [ ] Security monitoring

## 🚨 Incident Response

### If Security Breach Suspected

1. **Immediately**:
   - Disable affected accounts
   - Revoke compromised credentials
   - Isolate affected systems

2. **Investigate**:
   - Review logs
   - Identify scope
   - Document findings

3. **Remediate**:
   - Fix vulnerabilities
   - Update credentials
   - Patch systems

4. **Notify**:
   - Affected users
   - Security team
   - Authorities (if required)

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security](https://python.readthedocs.io/en/latest/library/security.html)
- [Cryptography Best Practices](https://cryptography.io/en/latest/)

---

**Remember**: Security is an ongoing process, not a one-time setup.
