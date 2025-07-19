import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Use environment variables for production deployment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 7734))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)