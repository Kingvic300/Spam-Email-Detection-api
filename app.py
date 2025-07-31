from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 'yes']

    print("=" * 50)
    print(" Spam Email Detector Starting...")
    print("=" * 50)
    print(f"Environment: {'Development' if debug else 'Production'}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("=" * 50)
    print("\n Available Endpoints:")
    print("  GET  /check-spam           - Check emails for spam")
    print("  GET  /check-spam?action=move_to_spam - Move spam to spam folder")
    print("  GET  /check-spam?action=delete - Delete spam emails")
    print("  GET  /stats                - Get spam detection statistics")
    print("  POST /schedule             - Schedule daily scans")
    print("  GET  /schedule             - Get schedule information")
    print("  GET  /health               - Health check")
    print("  GET  /config               - Get configuration")
    print("=" * 50)
    print("\n️  Configuration:")
    print("  Make sure to set these environment variables:")
    print("  - EMAIL_ADDRESS: Your email address")
    print("  - EMAIL_PASSWORD: Your email password/app password")
    print("  - IMAP_SERVER: IMAP server (default: imap.gmail.com)")
    print("=" * 50)

    try:
        app.run(host=host, port=port, debug=debug)

    except KeyboardInterrupt:
        print("\n\n Spam Email Detector shutting down...")

    except Exception as e:
        print(f"\n Error starting application: {str(e)}")
        exit(1)