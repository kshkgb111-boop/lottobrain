#!/bin/bash
# ──────────────────────────────────────────────
# 로또브레인 Mac .app 빌드 스크립트
# 실행: chmod +x build_mac.sh && ./build_mac.sh
#
# ※ 빌드 전 반드시 lotto.db에 최신 데이터가 수집된 상태여야 합니다.
#   python3 lotto.py → [D] 실행 후 빌드하세요.
# ──────────────────────────────────────────────

APP_NAME="로또브레인"
ENTRY="launcher.py"

echo ""
echo "🧠 로또브레인 Mac 앱 빌드 시작..."
echo "────────────────────────────────────"

# lotto.db 데이터 확인
DB_COUNT=$(python3 -c "import sqlite3; c=sqlite3.connect('lotto.db'); print(c.execute('SELECT COUNT(*) FROM draws').fetchone()[0]); c.close()" 2>/dev/null || echo "0")
if [ "$DB_COUNT" -lt "100" ]; then
  echo "⚠️  경고: lotto.db에 데이터가 부족합니다 (현재 ${DB_COUNT}건)"
  echo "   python3 lotto.py → [D] 로 데이터를 먼저 수집하세요."
  echo ""
  read -p "   그래도 계속 빌드할까요? (y/N) " confirm
  if [ "$confirm" != "y" ]; then
    echo "빌드를 취소합니다."
    exit 1
  fi
else
  echo "✅ DB 확인: ${DB_COUNT}회차 데이터 준비됨"
fi

echo ""

# 의존성 설치
pip3 install streamlit plotly pandas requests pyinstaller -q

# 이전 빌드 제거
rm -rf build dist __pycache__

pyinstaller \
  --noconfirm \
  --windowed \
  --name "$APP_NAME" \
  --add-data "app.py:." \
  --add-data "lotto_core.py:." \
  --add-data "lotto.db:." \
  --hidden-import streamlit \
  --hidden-import streamlit.runtime \
  --hidden-import streamlit.web \
  --hidden-import plotly \
  --hidden-import pandas \
  --hidden-import requests \
  --collect-all streamlit \
  --collect-all plotly \
  "$ENTRY" 2>&1

if [ -d "dist/$APP_NAME.app" ]; then
  echo ""
  echo "✅ 빌드 완료! (DB ${DB_COUNT}회차 데이터 포함)"
  echo "   위치: dist/$APP_NAME.app"
  echo ""
  echo "📦 배포용 ZIP 생성 중..."
  cd dist && zip -r "${APP_NAME}.zip" "${APP_NAME}.app" && cd ..
  echo "   dist/${APP_NAME}.zip 생성 완료"
  echo ""
  echo "👉 구매자는 ZIP 압축 해제 후 앱 실행만 하면 됩니다."
  echo "   (최신 회차만 자동 업데이트, 전체 재수집 불필요)"
else
  echo "❌ 빌드 실패. 위 로그를 확인하세요."
fi
