# feishu_demo/sender.py
import base64, hashlib, hmac, json, time, requests
from typing import Optional, Dict, Any
import Config as C

class FeishuSender:
    def __init__(self, url: str, secret: Optional[str] = None, timeout_sec: int = 6):
        self.url = url
        self.secret = secret
        self.timeout = timeout_sec

    def _sign(self, ts: str) -> str:
        # 说明：你当前环境已能发文本，这里保持原逻辑不改动，避免影响现有联调。
        # 若后续启用“签名校验”，请对照官方文档确认签名算法。
        assert self.secret
        s = f"{ts}\n{self.secret}"
        digest = hmac.new(s.encode("utf-8"), digestmod=hashlib.sha256).digest()
        return base64.b64encode(digest).decode()

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = payload.copy()
        if self.secret:
            ts = str(int(time.time()))
            data.update({"timestamp": ts, "sign": self._sign(ts)})
        r = requests.post(self.url, json=data, timeout=self.timeout)
        try:
            body = r.json()
        except Exception:
            body = {"non_json_body": r.text}
        if not r.ok or body.get("StatusCode") not in (0, None):
            raise RuntimeError(f"Feishu webhook failed: http={r.status_code}, body={body}")
        return body

    def send_text(self, text: str) -> Dict[str, Any]:
        return self._post({"msg_type": "text", "content": {"text": text}})

    def send_card(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送交互卡片。card 为飞书互动卡片 JSON（已在 formatter 中构造）。
        用法：sender.send_card(build_summary_card(...)) / sender.send_card(build_security_card(...))
        """
        return self._post({"msg_type": "interactive", "card": card})

# 工厂：默认读取 Config
def default_sender() -> FeishuSender:
    return FeishuSender(C.WEBHOOK_URL, C.WEBHOOK_SECRET, C.TIMEOUT_SEC)
