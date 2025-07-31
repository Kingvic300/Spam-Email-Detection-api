# 🚀 Spam Email Detector

A comprehensive Flask-based application that automatically detects and manages spam emails in your inbox using machine learning algorithms and rule-based detection.

## ✨ Features

- **Real-time Spam Detection**: Advanced spam classification using keyword analysis, domain checking, and pattern recognition
- **Email Management**: Automatically move spam to spam folder or delete it
- **Daily Scheduling**: Automated daily scans with customizable timing
- **Statistics & Reporting**: Track spam detection performance and generate reports
- **Database Logging**: SQLite database for storing spam detection history
- **Background Tasks**: Celery integration for asynchronous processing
- **RESTful API**: Complete API for integration with other systems
- **Multi-provider Support**: Works with Gmail, Outlook, and other IMAP providers

## 🛠️ Installation

### Quick Setup

1. **Clone and setup the project:**
```bash
git clone <your-repo>
cd spam-email-detector
python setup.py
```

2. **Configure your email credentials:**
```bash
# Edit .env file with your email settings
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

3. **Run the application:**
```bash
python app.py
```

### Manual Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Create environment file:**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Initialize database:**
```bash
python -c "from app.model import SpamDetector; SpamDetector()"
```

## 📧 Email Provider Setup

### Gmail Setup
1. Enable 2-Factor Authentication
2. Go to Google Account → Security → 2-Step Verification → App passwords
3. Generate app password for "Mail"
4. Use this password in your `.env` file
5. Ensure IMAP is enabled in Gmail settings

### Outlook Setup
```bash
EMAIL_ADDRESS=your-email@outlook.com
EMAIL_PASSWORD=your-password
IMAP_SERVER=imap-mail.outlook.com
```

### Other Providers
Update `IMAP_SERVER` in your `.env` file with the appropriate IMAP server.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EMAIL_ADDRESS` | Your email address | - |
| `EMAIL_PASSWORD` | Email password/app password | - |
| `IMAP_SERVER` | IMAP server address | `imap.gmail.com` |
| `SPAM_THRESHOLD` | Spam detection threshold (0-100) | `40.0` |
| `DEFAULT_SPAM_ACTION` | Default action for spam | `log` |
| `DAILY_SCAN_TIME` | Daily scan time (HH:MM) | `09:00` |

### Spam Actions
- `log`: Only log spam emails (safe mode)
- `move_to_spam`: Move spam to spam folder
- `delete`: Permanently delete spam emails

## 🌐 API Endpoints

### Check for Spam
```bash
# Basic spam check (log only)
GET /check-spam

# Move spam to spam folder
GET /check-spam?action=move_to_spam

# Delete spam emails
GET /check-spam?action=delete
```

### Statistics
```bash
# Get spam detection statistics
GET /stats
```

### Scheduling
```bash
# Schedule daily scan
POST /schedule
{
  "time": "09:00",
  "action": "log"
}

# Get schedule information
GET /schedule
```

### Health & Config
```bash
# Health check
GET /health

# Get configuration
GET /config
```

## 📊 Usage Examples

### Basic Spam Check
```python
import requests

# Check for spam and log results
response = requests.get('http://localhost:5000/check-spam')
print(response.json())
```

### Schedule Daily Scans
```python
import requests

# Schedule daily scan at 9 AM
data = {
    "time": "09:00",
    "action": "move_to_spam"
}
response = requests.post('http://localhost:5000/schedule', json=data)
print(response.json())
```

### Get Statistics
```python
import requests

response = requests.get('http://localhost:5000/stats')
stats = response.json()
print(f"Total spam detected: {stats['data']['total_spam_detected']}")
```

## 🤖 Spam Detection Algorithm

The spam detector uses multiple techniques:

### 1. Keyword Analysis
- Checks for common spam keywords (e.g., "winner", "free money", "urgent")
- Analyzes subject lines and email body content
- Assigns scores based on keyword frequency

### 2. Domain Analysis
- Identifies suspicious sender domains
- Checks against known temporary email providers
- Flags emails from blacklisted domains

### 3. Pattern Recognition
- Excessive capitalization detection
- Multiple exclamation marks
- Money-related terms and amounts
- URL shorteners and suspicious links

### 4. Scoring System
- Each factor contributes to a spam score (0-100)
- Configurable threshold for spam classification
- Weighted scoring based on spam indicators

## 📈 Monitoring & Logging

### Database Schema
The application creates two main tables:
- `spam_emails`: Individual spam detection records
- `detection_logs`: Summary of scan sessions

### Log Files
- Application logs: `logs/spam_detector.log`
- Rotating file handler with size limits
- Configurable log levels

### Statistics Dashboard
Access statistics via the `/stats` endpoint:
- Total spam detected
- Average spam scores
- Recent scan summaries
- Weekly/monthly trends

## ⚙️ Background Tasks (Optional)

### Celery Setup
1. **Install Redis:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
```

2. **Start Celery worker:**
```bash
celery -A app.celery_tasks worker --loglevel=info
```

3. **Start Celery beat (scheduler):**
```bash
celery -A app.celery_tasks beat --loglevel=info
```

### Available Tasks
- `daily_spam_check_task`: Daily automated spam checking
- `generate_spam_report_task`: Weekly spam reports
- `cleanup_old_logs_task`: Database maintenance

## 🔄 Automation Options

### 1. Cron Jobs
```bash
# Add to crontab (crontab -e)
0 9 * * * cd /path/to/spam-detector && python -c "from app.model import check_email_spam; check_email_spam('log')"
```

### 2. Systemd Service (Linux)
```bash
# Copy service file
sudo cp spam-detector.service /etc/systemd/system/

# Enable and start service
sudo systemctl enable spam-detector
sudo systemctl start spam-detector
```

### 3. Built-in Scheduler
The application includes a built-in scheduler that runs automatically.

## 🔒 Security Considerations

### Email Credentials
- Use app passwords instead of main passwords
- Store credentials in environment variables
- Never commit credentials to version control

### Database Security
- SQLite database is created with appropriate permissions
- Consider encryption for sensitive production environments

### Network Security
- Run behind reverse proxy in production
- Use HTTPS for API endpoints
- Implement rate limiting if needed

## 🐛 Troubleshooting

### Common Issues

**Connection Failed:**
```
Error: Failed to connect to email server
```
- Check email credentials in `.env`
- Verify IMAP server settings
- Ensure 2FA and app passwords are configured

**Database Errors:**
```
Error: Database initialization failed
```
- Check file permissions in project directory
- Ensure SQLite is available
- Run `python setup.py` to reinitialize

**Import Errors:**
```
ModuleNotFoundError: No module named 'app'
```
- Ensure you're in the project root directory
- Check Python path configuration
- Install requirements: `pip install -r requirements.txt`

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python app.py
```

## 📚 Development

### Project Structure
```
spam-email-detector/
├── app/
│   ├── __init__.py          # Application factory
│   ├── model.py             # Spam detection logic
│   ├── routes.py            # API endpoints
│   ├── scheduler.py         # Scheduling system
│   └── celery_tasks.py      # Background tasks
├── config.py                # Configuration
├── app.py                   # Main application
├── requirements.txt         # Dependencies
├── setup.py                # Setup script
└── README.md               # Documentation
```

### Adding New Features
1. **Custom Spam Rules**: Extend `SpamDetector.calculate_spam_score()`
2. **New Actions**: Add actions in `EmailManager.check_email_spam()`
3. **API Endpoints**: Add routes in `routes.py`
4. **Background Tasks**: Add tasks in `celery_tasks.py`

### Testing
```bash
# Test spam detection
curl http://localhost:5000/check-spam

# Test with action
curl "http://localhost:5000/check-spam?action=log"

# Health check
curl http://localhost:5000/health
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- Create an issue for bug reports
- Check existing issues for solutions
- Review the troubleshooting section

## 🎯 Roadmap

- [ ] Machine learning model training
- [ ] Web dashboard interface
- [ ] Email whitelist/blacklist management
- [ ] Advanced reporting features
- [ ] Multi-account support
- [ ] Cloud deployment guides

---

**⚠️ Disclaimer**: This tool is for educational and personal use. Always review emails before taking automated actions. The accuracy of spam detection depends on your configuration and email patterns.
