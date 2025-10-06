# tasks_service/github_poll.py
import os, time, requests
from datetime import datetime
from repo import TaskRepo  # 已有的
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
OWNER, REPO = "Vinch1", "CityUSEGroup2"
SEEN = set()

def fetch_open_prs():
    r = requests.get(
        f"https://api.github.com/repos/{OWNER}/{REPO}/pulls?state=open",
        headers={"Authorization": f"token {TOKEN}",
                 "Accept": "application/vnd.github+json"},
        timeout=10)
    r.raise_for_status()
    return [pr["number"] for pr in r.json()]

def loop():
    while True:
        try:
            for pr in fetch_open_prs():
                if pr not in SEEN:
                    SEEN.add(pr)
                    TaskRepo.create_task(
                        pr_info_id=str(pr),
                        receiver="feishu-bot",
                        send_dt=datetime.utcnow(),
                        template_id="AI审查通知",
                        idem_key=str(pr),
                    )
                    print(f"✅ 登记任务 PR #{pr}")
        except Exception as e:
            print("轮询出错:", e)
        time.sleep(60)  # 每分钟跑一次

if __name__ == "__main__":
    loop()
