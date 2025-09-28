import os, sys
pwdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(pwdir, ".."))
import time
from flask import Blueprint, request
from utils.api_protocol import *
from utils.common import get_response
from utils.log import logger
from src.run_security_audit import audit_analysis

security_audit = Blueprint('security_audit', __name__)

@security_audit.route('/audit_security', methods=['POST'])
def svr_audit_security():
    """
    security audit
    """
    params_dict = request.get_json()
    logger.info(f"security audit received params: {params_dict}")
    if params_dict is None or params_dict == '':
        return get_response(400, '', 'params are None')
    security_audit_res = audit_analysis(params_dict)
    res_data = {'security_audit_res': security_audit_res, 'timestamp': int(time.time() * 1000)}
    return get_response(200, res_data, 'success')