import os
from flask import Flask
import settings
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.testing = False
from route.security_audit_route import security_audit


app.register_blueprint(security_audit, url_prefix='/api/security_audit')


if __name__ == '__main__':
    app.run(host=settings.FLASK_HOST, port=settings.FLASK_PORT, debug=settings.DEBUG)