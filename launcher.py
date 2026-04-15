"""
로또브레인 런처
더블클릭으로 실행 시 Streamlit 서버를 띄우고 브라우저를 자동으로 엽니다

DB 전략:
  - 번들 내부 lotto.db → 최초 실행 시 ~/로또브레인/lotto.db 로 복사
  - 이후 업데이트는 복사된 파일에 누적 저장 (앱 재설치해도 데이터 유지)
"""

import subprocess
import sys
import os
import shutil
import webbrowser
import time
import threading


# 구매자 데이터 저장 경로
DATA_DIR  = os.path.join(os.path.expanduser("~"), "로또브레인")
USER_DB   = os.path.join(DATA_DIR, "lotto.db")


def setup_user_data():
    """번들 DB를 사용자 홈에 복사 (최초 1회 또는 없을 때)"""
    os.makedirs(DATA_DIR, exist_ok=True)

    if getattr(sys, "frozen", False):
        bundle_db = os.path.join(sys._MEIPASS, "lotto.db")
    else:
        bundle_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lotto.db")

    if not os.path.exists(USER_DB) and os.path.exists(bundle_db):
        shutil.copy2(bundle_db, USER_DB)

    # 환경변수로 app.py에 경로 전달
    os.environ["LOTTOBRAIN_DATA_DIR"] = DATA_DIR


def open_browser():
    time.sleep(2.5)
    webbrowser.open("http://localhost:8501")


def main():
    setup_user_data()

    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))

    app_path = os.path.join(base, "app.py")

    threading.Thread(target=open_browser, daemon=True).start()

    subprocess.run([
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.headless", "true",
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false",
    ])


if __name__ == "__main__":
    main()
