import json, time, requests
import socket
from .log import logger
s = requests.Session()

def get_internal_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip





def post_to_security_audit_srv(data):
    # security_audit_url = 'http://'+get_internal_ip()+':8080/api/security_audit/audit_security'
    security_audit_url = 'http://0.0.0.0:8080/api/security_audit/audit_security'
    headers = {'Content-Type': 'application/json', 'Accept': 'text/plain'}
    response = requests.post(security_audit_url, headers=headers, json=data)
    logger.info(f'post to {security_audit_url} response {response}')
    try:
        data = response.json()  # 自动解析为 Python 字典或列表
        logger.info(data)
    except requests.exceptions.JSONDecodeError:
        logger.error("响应不是合法的 JSON")
    return data


if __name__ == '__main__':
    request_body = {
            "filter_instruction": "",
            "scan_instruction": "",
            "repo_name": "Vinch1/CityUSEGroup2",
            "pr_number": 17
        }
    post_to_security_audit_srv(request_body)