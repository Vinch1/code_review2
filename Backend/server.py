import os
from flask import Flask
import settings
app = Flask(__name__)
# Ensure JSON responses use UTF-8 and don't escape non-ASCII characters
try:
    # Flask 2.3+/3.x JSON provider
    app.json.ensure_ascii = False
except Exception:
    # Fallback for older Flask versions
    app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'
app.testing = False
from route.security_audit_route import security_audit
from route.metrics_route import metrics


app.register_blueprint(security_audit, url_prefix='/api/security_audit')
app.register_blueprint(metrics, url_prefix='/api/metrics')


if __name__ == '__main__':
    app.run(host=settings.FLASK_HOST, port=settings.FLASK_PORT, debug=settings.DEBUG)
