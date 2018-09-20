"""
Runs flask application
"""
import os
from HarvardEvents import app as application


if __name__ == '__main__':
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    PORT = int(os.environ.get('SERVER_PORT', '5000'))
    application.run(HOST, PORT, ssl_context=('website-env/cert.pem', 'website-env/key.pem'))
