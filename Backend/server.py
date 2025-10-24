import os, sys
from flask import Flask
# Ensure Python can import the local 'settings' package when run via Flask CLI
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
from route.web_hook import github_hook
from route.commit_route import commit_records

app.register_blueprint(security_audit, url_prefix='/api/security_audit')
app.register_blueprint(metrics, url_prefix='/api/metrics')
app.register_blueprint(github_hook, url_prefix='/api')
app.register_blueprint(commit_records, url_prefix='/api')


from ..feishu.outbox_poller import start_outbox_poller
_stop_feishu = start_outbox_poller(interval_sec=15, batch_size=10)

if __name__ == '__main__':
    app.run(host=settings.FLASK_HOST, port=settings.FLASK_PORT, debug=False)
