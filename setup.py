import os
import sys
import subprocess
import sqlite3
from pathlib import Path


def print_banner():
    print("=" * 60)
    print("🚀 Spam Email Detector Setup")
    print("=" * 60)


def check_python_version():
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def install_requirements():
    print("\n📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages")
        sys.exit(1)


def create_directories():
    print("\n📁 Creating directories...")
    directories = ['logs', 'data']

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/ directory")


def setup_environment():
    print("\n⚙️  Setting up environment...")

    if not os.path.exists('.env'):
        if os.path.exists('.env'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your email credentials")
        else:
            with open('.env', 'w') as f:
                f.write("# Edit these settings\n")
                f.write("EMAIL_ADDRESS=your-email@gmail.com\n")
                f.write("EMAIL_PASSWORD=your-app-password\n")
                f.write("SECRET_KEY=change-this-secret-key\n")
            print("✅ Created basic .env file")
            print("⚠️  Please edit .env file with your settings")
    else:
        print("✅ .env file already exists")


def initialize_database():
    print("\n🗄️  Initializing database...")

    try:
        from app.model import SpamDetector
        SpamDetector()
        print("✅ Database initialized successfully")

        conn = sqlite3.connect('spam_detection.db')
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM detection_logs")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO detection_logs (total_emails, spam_detected, emails_processed)
                VALUES (0, 0, 0)
            ''')
            conn.commit()
            print("✅ Added initial database records")

        conn.close()

    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        print("   This might be normal if running for the first time")


def setup_gmail_instructions():
    """Display Gmail setup instructions"""
    print("\n📧 Gmail Setup Instructions:")
    print("-" * 40)
    print("1. Enable 2-Factor Authentication on your Gmail account")
    print("2. Go to Google Account settings")
    print("3. Security → 2-Step Verification → App passwords")
    print("4. Generate an app password for 'Mail'")
    print("5. Use this app password in your .env file")
    print("6. Make sure IMAP is enabled in Gmail settings")


def create_systemd_service():
    if os.name == 'posix':
        print("\n🔧 Creating systemd service file...")

        service_content = f"""[Unit]
Description=Spam Email Detector
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'ubuntu')}
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}/venv/bin
ExecStart={sys.executable} app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

        try:
            with open('spam-detector.service', 'w') as f:
                f.write(service_content)
            print("✅ Created spam-detector.service file")
            print("   To install: sudo cp spam-detector.service /etc/systemd/system/")
            print("   To enable: sudo systemctl enable spam-detector")
            print("   To start: sudo systemctl start spam-detector")
        except Exception as e:
            print(f"⚠️  Could not create service file: {str(e)}")


def create_cron_job():
    print("\n⏰ Cron Job Example:")
    print("-" * 30)
    print("To run spam detection every day at 9 AM, add this to your crontab:")
    print("(Run 'crontab -e' to edit)")
    print()
    print(
        f"0 9 * * * cd {os.getcwd()} && {sys.executable} -c \"from app.model import check_email_spam; check_email_spam('log')\"")


def test_installation():
    print("\n🧪 Testing installation...")

    try:
        from app import create_app
        from app.model import SpamDetector
        create_app()
        print("✅ Flask app creation successful")
        SpamDetector()
        print("✅ Database connection successful")

        print("✅ Installation test passed!")

    except Exception as e:
        print(f"❌ Installation test failed: {str(e)}")
        return False

    return True


def main():
    print_banner()
    check_python_version()
    install_requirements()
    create_directories()
    setup_environment()
    initialize_database()

    if test_installation():
        print("\n" + "=" * 60)
        print("🎉 Setup completed successfully!")
        print("=" * 60)

        setup_gmail_instructions()
        create_cron_job()
        create_systemd_service()

        print("\n🚀 Next Steps:")
        print("1. Edit .env file with your email credentials")
        print("2. Run: python app.py")
        print("3. Test: curl http://localhost:5000/health")
        print("4. Check spam: curl http://localhost:5000/check-spam")

    else:
        print("\n❌ Setup completed with errors")
        print("Please check the error messages above")


if __name__ == "__main__":
    main()