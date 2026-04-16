"""
로또브레인 (LottoBrain) - Streamlit 웹앱  v3.0
실행: streamlit run app.py
"""

import os
import time
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from collections import Counter

os.chdir(os.path.dirname(os.path.abspath(__file__)))
import lotto_core as core

WELCOME_FLAG = ".welcome_shown"

st.set_page_config(
    page_title="로또브레인",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

/* ── Reset ── */
*, *::before, *::after {
    font-family: 'Noto Sans KR', -apple-system, sans-serif !important;
    box-sizing: border-box;
}

/* ── Streamlit 기본 UI 완전 제거 ── */
#MainMenu, footer, header[data-testid="stHeader"],
.stDeployButton, div[data-testid="stToolbar"],
[data-testid="manage-app-button"],
[data-testid="stStatusWidget"],
div[class*="viewerBadge"] { display: none !important; }

/* ── 사이드바 << 접기 / >> 펼치기 버튼 숨김 ── */
button[data-testid="stBaseButton-headerNoPadding"],
button[data-testid="stExpandSidebarButton"] { display: none !important; }

/* ════════════════════════════════════════
   📱 모바일 반응형 (768px 이하)
   ════════════════════════════════════════ */
@media (max-width: 768px) {
    /* 사이드바 숨김 */
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }

    /* 메인 콘텐츠 전체 너비 + 하단 탭바 여백 */
    .main .block-container {
        padding: 12px 14px calc(80px + env(safe-area-inset-bottom)) !important;
        max-width: 100% !important;
    }

    /* 볼 크기 축소 */
    .ball {
        width: 42px !important; height: 42px !important;
        font-size: 14px !important; margin: 3px !important;
    }

    /* 카드 패딩 축소 */
    .num-card { padding: 16px 14px 14px !important; }

    /* 페이지 타이틀 */
    .page-title { font-size: 20px !important; margin-top: 16px !important; }

    /* stat box 폰트 */
    .stat-num { font-size: 26px !important; }

    /* 탭 텍스트 작게 */
    .stTabs [data-baseweb="tab"] { font-size: 11px !important; padding: 6px 10px !important; }

    /* 하단 탭바 보임 */
    .mobile-nav { display: flex !important; }
}


/* ── App 배경 ── */
.stApp { background: #080b14 !important; }
.main .block-container {
    padding: 0 2rem 3rem !important;
    max-width: 900px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c0f1d 0%, #080b14 100%) !important;
    border-right: 1px solid rgba(249,202,36,0.12) !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 24px 16px !important;
}
/* 데스크톱에서 사이드바 항상 펼침 (Streamlit 자동접힘 무력화) */
@media (min-width: 769px) {
    [data-testid="stSidebar"] {
        transform: none !important;
        min-width: 288px !important;
        width: 288px !important;
    }
    /* 사이드바 옆 메인 컨텐츠 위치 맞춤 */
    .main { margin-left: 288px !important; }
}

/* ── 라디오 → 커스텀 네비 ── */
/* 그룹 레이블("메뉴" 텍스트) 숨김 */
div[data-testid="stRadio"] > div[data-testid="stWidgetLabel"],
div[data-testid="stRadio"] [data-testid="stWidgetLabel"] { display: none !important; }

div[data-testid="stRadio"] > div {
    display: flex !important;
    flex-direction: column !important;
    gap: 4px !important;
}
/* 라디오 원형 숨김 */
div[data-testid="stRadio"] input[type="radio"] {
    position: absolute !important;
    opacity: 0 !important;
    width: 0 !important; height: 0 !important;
    pointer-events: none !important;
}
/* 메뉴 아이템 스타일 */
div[data-testid="stRadio"] > div > label {
    display: flex !important;
    align-items: center !important;
    padding: 11px 16px !important;
    border-radius: 12px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    border: 1px solid transparent !important;
    color: #8a9ab0 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    margin: 0 !important;
    position: relative !important;
}
div[data-testid="stRadio"] > div > label:hover {
    background: rgba(249,202,36,0.07) !important;
    color: #d4dce8 !important;
}
div[data-testid="stRadio"] > div > label:has(input:checked) {
    background: linear-gradient(135deg,
        rgba(249,202,36,0.14) 0%,
        rgba(240,147,43,0.08) 100%) !important;
    color: #f9ca24 !important;
    border-color: rgba(249,202,36,0.35) !important;
    font-weight: 700 !important;
    box-shadow: 0 0 16px rgba(249,202,36,0.08) !important;
}

/* ── 사이드바 배지 (번호생성=AI, 통계=NEW, 가중치=PRO) ── */
div[data-testid="stRadio"] > div > label:nth-child(2) p::after {
    content: "AI";
    background: #3b82f6; color: #fff;
    border-radius: 5px; padding: 1px 6px;
    font-size: 10px; font-weight: 700;
    margin-left: 6px; vertical-align: middle;
}
div[data-testid="stRadio"] > div > label:nth-child(3) p::after {
    content: "NEW";
    background: #10b981; color: #fff;
    border-radius: 5px; padding: 1px 6px;
    font-size: 10px; font-weight: 700;
    margin-left: 6px; vertical-align: middle;
}
div[data-testid="stRadio"] > div > label:nth-child(5) p::after {
    content: "NEW";
    background: #a855f7; color: #fff;
    border-radius: 5px; padding: 1px 6px;
    font-size: 10px; font-weight: 700;
    margin-left: 6px; vertical-align: middle;
}
div[data-testid="stRadio"] > div > label:nth-child(6) p::after {
    content: "PRO";
    background: linear-gradient(90deg, #f9ca24, #f0932b); color: #1a1a2e;
    border-radius: 5px; padding: 1px 6px;
    font-size: 10px; font-weight: 700;
    margin-left: 6px; vertical-align: middle;
}

/* ── 로또 볼 ── */
.ball {
    display: inline-flex; align-items: center; justify-content: center;
    width: 56px; height: 56px; border-radius: 50%;
    font-weight: 900; font-size: 17px; color: #fff;
    margin: 4px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.5),
                inset 0 2px 0 rgba(255,255,255,0.3),
                inset 0 -2px 4px rgba(0,0,0,0.3);
    transition: transform 0.2s cubic-bezier(.34,1.56,.64,1);
    animation: ballPop 0.4s cubic-bezier(.34,1.56,.64,1) both;
}
.ball:hover { transform: scale(1.15) translateY(-3px); }
@keyframes ballPop {
    from { transform: scale(0.5); opacity: 0; }
    to   { transform: scale(1);   opacity: 1; }
}
.ball:nth-child(1) { animation-delay: 0.05s; }
.ball:nth-child(2) { animation-delay: 0.10s; }
.ball:nth-child(3) { animation-delay: 0.15s; }
.ball:nth-child(4) { animation-delay: 0.20s; }
.ball:nth-child(5) { animation-delay: 0.25s; }
.ball:nth-child(6) { animation-delay: 0.30s; }

.ball-yellow { background: radial-gradient(circle at 35% 35%, #fde68a, #d97706); }
.ball-blue   { background: radial-gradient(circle at 35% 35%, #93c5fd, #1d4ed8); }
.ball-red    { background: radial-gradient(circle at 35% 35%, #fca5a5, #dc2626); }
.ball-gray   { background: radial-gradient(circle at 35% 35%, #cbd5e1, #475569); }
.ball-green  { background: radial-gradient(circle at 35% 35%, #6ee7b7, #059669); }

/* ── 번호 카드 ── */
.num-card {
    background: rgba(13,17,35,0.9);
    border-radius: 20px;
    padding: 22px 26px 18px;
    margin-bottom: 14px;
    border: 1px solid rgba(249,202,36,0.18);
    box-shadow: 0 4px 24px rgba(0,0,0,0.5),
                inset 0 1px 0 rgba(255,255,255,0.04);
    backdrop-filter: blur(12px);
    transition: all 0.25s ease;
    position: relative;
    overflow: hidden;
}
.num-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #f9ca24 0%, #f0932b 60%, transparent 100%);
}
.num-card:hover {
    border-color: rgba(249,202,36,0.38);
    box-shadow: 0 8px 36px rgba(249,202,36,0.08), 0 4px 24px rgba(0,0,0,0.5);
    transform: translateY(-2px);
}

/* ── 순위 배지 ── */
.rank-badge {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 700; color: #f9ca24;
    background: rgba(249,202,36,0.1);
    border: 1px solid rgba(249,202,36,0.25);
    border-radius: 20px; padding: 3px 12px; margin-bottom: 12px;
    letter-spacing: 0.3px;
}

/* ── 정보 칩 ── */
.info-chip {
    display: inline-flex; align-items: center;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    padding: 3px 12px; font-size: 12px; color: #7a8899; margin: 3px 3px 0 0;
}

/* ── 스코어 바 ── */
.score-track {
    background: rgba(255,255,255,0.06);
    border-radius: 999px; height: 5px;
    margin: 10px 0 14px; overflow: hidden;
}
.score-fill {
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, #f9ca24, #f0932b);
    box-shadow: 0 0 8px rgba(249,202,36,0.6);
}

/* ── 페이지 타이틀 ── */
.page-title {
    font-size: 26px; font-weight: 900; margin: 28px 0 4px;
    background: linear-gradient(135deg, #f9ca24, #f0932b);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
}
.page-sub {
    font-size: 13px; color: #4a5a6a; margin-bottom: 20px; font-weight: 400;
}

/* ── 통계 박스 ── */
.stat-box {
    background: rgba(13,17,35,0.9);
    border-radius: 16px; padding: 20px 16px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    backdrop-filter: blur(8px);
    transition: border-color 0.2s;
}
.stat-box:hover { border-color: rgba(249,202,36,0.25); }
.stat-num {
    font-size: 34px; font-weight: 900; line-height: 1;
    background: linear-gradient(135deg, #f9ca24, #f0932b);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.stat-label { font-size: 12px; color: #4a5a6a; margin-top: 8px; line-height: 1.5; }

/* ── 데이터 상태 필 ── */
.data-pill {
    display: flex; align-items: center; gap: 10px;
    background: rgba(16,185,129,0.08);
    border: 1px solid rgba(16,185,129,0.25);
    border-radius: 12px; padding: 11px 14px; margin: 12px 0;
}
.data-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #10b981; flex-shrink: 0;
    box-shadow: 0 0 8px #10b981;
    animation: dotPulse 2s ease-in-out infinite;
}
@keyframes dotPulse {
    0%,100% { opacity:1; transform:scale(1); }
    50% { opacity:0.5; transform:scale(1.4); }
}
.data-pill-text { font-size: 13px; color: #10b981; font-weight: 600; }

/* ── 업데이트 버튼 ── */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #94a3b8 !important;
    border-radius: 12px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 10px !important;
    transition: all 0.2s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(249,202,36,0.08) !important;
    border-color: rgba(249,202,36,0.3) !important;
    color: #f9ca24 !important;
}

/* ── 메인 버튼 (primary) ── */
.stButton > button[kind="primary"],
button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #f9ca24, #f0932b) !important;
    border: none !important;
    color: #1a1208 !important;
    font-weight: 800 !important;
    font-size: 15px !important;
    border-radius: 14px !important;
    padding: 14px 24px !important;
    box-shadow: 0 6px 20px rgba(249,202,36,0.35) !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.2px;
}
button[data-testid="stBaseButton-primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 28px rgba(249,202,36,0.45) !important;
}

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 10px !important;
    color: #556070 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    border: none !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(249,202,36,0.12) !important;
    color: #f9ca24 !important;
}

/* ── Select / Number input ── */
div[data-testid="stSelectbox"] > div,
div[data-testid="stNumberInput"] > div input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
}

/* ── 추천 이유 박스 ── */
.reason-box {
    margin-top: 14px;
    background: rgba(249,202,36,0.04);
    border: 1px solid rgba(249,202,36,0.12);
    border-radius: 12px;
    padding: 12px 14px;
}
.reason-title {
    font-size: 11px; font-weight: 700; color: #f9ca24;
    letter-spacing: 0.3px; margin-bottom: 8px;
    text-transform: uppercase;
}
.reason-item {
    font-size: 12px; color: #94a3b8;
    padding: 4px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    line-height: 1.5;
}
.reason-item:last-child { border-bottom: none; }

/* ── Blur preview ── */
.blur-wrap { position: relative; }
.blur-inner { filter: blur(7px); opacity: 0.3; pointer-events: none; user-select: none; }
.blur-overlay {
    position: absolute; inset: 0;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 14px; padding: 24px;
}

/* ── 환영 카드 ── */
.welcome-card {
    background: rgba(10,13,22,0.97);
    border-radius: 28px; padding: 52px 44px 44px;
    border: 1px solid rgba(249,202,36,0.25);
    box-shadow: 0 40px 100px rgba(0,0,0,0.8),
                0 0 80px rgba(249,202,36,0.04);
    text-align: center; max-width: 460px; margin: 0 auto;
    backdrop-filter: blur(20px);
}
.welcome-title {
    font-size: 28px; font-weight: 900;
    background: linear-gradient(135deg, #f9ca24, #f0932b);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 24px; line-height: 1.2;
}
.welcome-feature {
    display: flex; align-items: center; gap: 10px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 12px 16px;
    margin: 8px 0; text-align: left;
    font-size: 14px; color: #c4ccd8; font-weight: 500;
}
.welcome-icon { font-size: 18px; flex-shrink: 0; }

/* ── Spinner 색 ── */
div[data-testid="stSpinner"] { color: #f9ca24 !important; }

/* ── Success / Error 박스 ── */
div[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}

/* ── Expander (데모 도구) ── */
[data-testid="stExpander"] {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary {
    color: #3d4a58 !important;
    font-size: 12px !important;
}

/* ── Slider ── */
div[data-testid="stSlider"] > div > div > div {
    background: rgba(249,202,36,0.2) !important;
}
div[data-testid="stSlider"] [role="slider"] {
    background: linear-gradient(135deg, #f9ca24, #f0932b) !important;
    box-shadow: 0 0 8px rgba(249,202,36,0.5) !important;
    border: none !important;
}

/* ── Caption ── */
.stCaption { color: #3d4a58 !important; font-size: 12px !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #080b14; }
::-webkit-scrollbar-thumb { background: rgba(249,202,36,0.2); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

core.init_db()

# ─────────────────────────────────────────
# 방문자 카운터 (누적 + 오늘)
# ─────────────────────────────────────────
import json as _json
from datetime import datetime as _datetime
import zoneinfo as _zi

def _today_kst() -> str:
    return _datetime.now(_zi.ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")

_VISIT_FILE = "/tmp/lotto_visits.json"
_VISIT_BASE = 1000  # 카운터 미설치 이전 누적 기준값

def _load_visits() -> dict:
    try:
        with open(_VISIT_FILE) as f:
            return _json.load(f)
    except Exception:
        return {}

def _save_visits(data: dict):
    try:
        with open(_VISIT_FILE, "w") as f:
            _json.dump(data, f)
    except Exception:
        pass

def _increment_visit() -> dict:
    today = _today_kst()
    data = _load_visits()
    data["total"] = data.get("total", _VISIT_BASE) + 1
    if data.get("today_date") != today:
        data["today_date"] = today
        data["today"] = 1
    else:
        data["today"] = data.get("today", 0) + 1
    _save_visits(data)
    return data

def _get_visits() -> dict:
    today = _today_kst()
    data = _load_visits()
    if data.get("today_date") != today:
        data["today"] = 0
    return data

if "visited" not in st.session_state:
    st.session_state["visited"] = True
    _vdata = _increment_visit()
else:
    _vdata = _get_visits()
st.session_state["visit_total"] = _vdata.get("total", _VISIT_BASE)
st.session_state["visit_today"] = _vdata.get("today", 0)

# ─────────────────────────────────────────
# 모바일 하단 탭바 (components.html로 parent DOM 조작)
# ─────────────────────────────────────────
import streamlit.components.v1 as components
components.html("""
<script>
(function(){
  if (window === window.parent) return;
  var p = window.parent.document;

  // 중복 삽입 방지
  if (p.getElementById('lbMobileNav')) { syncNav(); return; }

  // ── CSS 주입 ──
  var style = p.createElement('style');
  style.id = 'lbMobileNavStyle';
  style.textContent = [
    '#lbMobileNav{',
      'display:none;position:fixed;bottom:0;left:0;right:0;z-index:9999;',
      'height:calc(62px + env(safe-area-inset-bottom));',
      'background:rgba(10,13,22,0.97);',
      'border-top:1px solid rgba(249,202,36,0.18);',
      'backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);',
      'align-items:center;justify-content:space-around;',
      'padding:0 4px;padding-bottom:env(safe-area-inset-bottom);',
    '}',
    '@media(max-width:768px){#lbMobileNav{display:flex;}}',
    '.mnav-btn{',
      'display:flex;flex-direction:column;align-items:center;gap:2px;',
      'padding:4px 4px;flex:1;cursor:pointer;border:none;background:none;',
      'border-radius:10px;color:#4a5a6a;font-size:9px;font-weight:600;',
      'font-family:"Noto Sans KR",sans-serif;-webkit-tap-highlight-color:transparent;',
      'transition:color 0.2s;',
    '}',
    '.mnav-btn .mi{font-size:20px;line-height:1;}',
    '.mnav-btn.active{color:#f9ca24;}',
    '.mnav-btn.active .mi{filter:drop-shadow(0 0 4px rgba(249,202,36,0.6));}'
  ].join('');
  p.head.appendChild(style);

  // ── HTML 주입 ──
  var nav = p.createElement('div');
  nav.id = 'lbMobileNav';
  nav.innerHTML =
    '<button class="mnav-btn" onclick="lbNav(0)"><span class="mi">🏆</span>TOP 5</button>' +
    '<button class="mnav-btn" onclick="lbNav(1)"><span class="mi">🎰</span>번호생성</button>' +
    '<button class="mnav-btn" onclick="lbNav(2)"><span class="mi">📊</span>통계</button>' +
    '<button class="mnav-btn" onclick="lbNav(3)"><span class="mi">📋</span>히스토리</button>' +
    '<button class="mnav-btn" onclick="lbNav(4)"><span class="mi">🔮</span>사주</button>' +
    '<button class="mnav-btn" onclick="lbNav(5)"><span class="mi">⚙️</span>설정</button>';
  p.body.appendChild(nav);

  // ── 네비게이션 클릭 ──
  window.parent.lbNav = function(idx) {
    var radios = p.querySelectorAll('div[data-testid="stRadio"] input[type="radio"]');
    if (radios[idx]) radios[idx].click();
  };

  // ── active 동기화 ──
  function syncNav() {
    var radios = p.querySelectorAll('div[data-testid="stRadio"] input[type="radio"]');
    var btns   = p.querySelectorAll('#lbMobileNav .mnav-btn');
    radios.forEach(function(r, i){ if(btns[i]) btns[i].classList.toggle('active', r.checked); });
  }
  var obs = new MutationObserver(syncNav);
  obs.observe(p.body, {subtree:true, childList:true});
  syncNav();
})();
</script>
""", height=0)


# ─────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────
def ball_color_class(n):
    if n <= 10: return "ball-yellow"
    if n <= 20: return "ball-blue"
    if n <= 30: return "ball-red"
    if n <= 40: return "ball-gray"
    return "ball-green"

def render_balls(nums, highlight=None):
    html = ""
    for n in nums:
        cls = ball_color_class(n)
        style = "opacity:0.2;animation:none;" if (highlight is not None and n not in highlight) else ""
        html += f'<span class="ball {cls}" style="{style}">{n}</span>'
    return html

def grade_label(matched, bonus):
    if matched == 6:           return "🥇 1등"
    if matched == 5 and bonus: return "🥈 2등"
    if matched == 5:           return "🥉 3등"
    if matched == 4:           return "4등"
    if matched == 3:           return "5등"
    return "낙첨"

SAMPLE_CARDS = [
    {"nums":[3,11,23,34,38,42],"sum":151,"odd":3,"even":3,"low":3,"high":3,"avg_gap":9.2,"score":195},
    {"nums":[7,16,25,31,40,44],"sum":163,"odd":4,"even":2,"low":2,"high":4,"avg_gap":7.5,"score":188},
    {"nums":[2,14,19,27,36,43],"sum":141,"odd":2,"even":4,"low":3,"high":3,"avg_gap":11.0,"score":183},
    {"nums":[8,13,21,29,37,45],"sum":153,"odd":3,"even":3,"low":3,"high":3,"avg_gap":6.3,"score":178},
    {"nums":[5,17,24,33,39,41],"sum":159,"odd":3,"even":3,"low":3,"high":3,"avg_gap":8.8,"score":172},
]

def gen_reason(r, freq, last_app):
    """AI 스코어링 근거를 사람이 읽을 수 있는 문장으로 생성"""
    nums = r["nums"]
    reasons = []
    avg_freq = sum(freq.values()) / 45

    # 1. 합계 분석
    s = r["sum"]
    if abs(s - 138) <= 4:
        reasons.append(f"✅ 합계 {s} — 역대 당첨 평균(138)과 거의 일치")
    elif abs(s - 138) <= 12:
        reasons.append(f"✅ 합계 {s} — 적정 범위(125~155) 내 안정적 조합")

    # 2. 홀짝 비율
    odd = r["odd"]
    if odd == 3:
        reasons.append("✅ 홀짝 3:3 — 역대 출현 빈도 1위 황금 비율")
    elif odd in (2, 4):
        reasons.append(f"✅ 홀짝 {odd}:{6-odd} — 높은 확률의 두 번째 비율")

    # 3. 구간 분산
    zones = [0] * 5
    for n in nums:
        zones[min((n - 1) // 9, 4)] += 1
    covered = sum(1 for z in zones if z > 0)
    if covered >= 5:
        reasons.append("✅ 5개 구간 완전 분산 — 번호가 전 범위에 고르게 분포")
    elif covered == 4:
        reasons.append("✅ 4개 구간 분산 — 한쪽 편중 없이 고른 분포")

    # 4. 출현 타이밍 (5~15회 휴식 = 나올 때)
    timing = [(n, last_app.get(n, 0)) for n in nums if 5 <= last_app.get(n, 0) <= 15]
    timing.sort(key=lambda x: x[1], reverse=True)
    if timing:
        desc = ", ".join(f"{n}번({g}회 휴식)" for n, g in timing[:3])
        reasons.append(f"⏰ 출현 타이밍 포착 — {desc}")

    # 5. 고빈도 번호
    hot = sorted([(n, freq.get(n, 0)) for n in nums if freq.get(n, 0) > avg_freq * 1.08],
                 key=lambda x: x[1], reverse=True)
    if hot:
        desc = ", ".join(f"{n}번({c}회)" for n, c in hot[:3])
        reasons.append(f"📊 고빈도 번호 포함 — {desc}")

    # 6. 연속번호 없음
    consec = sum(1 for i in range(5) if nums[i+1] - nums[i] == 1)
    if consec == 0:
        reasons.append("✅ 연속번호 없음 — 실제 당첨 패턴과 일치")

    # 7. 저고 균형
    low = r["low"]
    if low == 3:
        reasons.append("✅ 저번호(1~22) : 고번호(23~45) = 3:3 균형")

    return reasons[:4]  # 최대 4개


def render_num_card(rank, r, pct, highlight=None):
    balls_html = render_balls(r["nums"], highlight)
    medal = ["🥇","🥈","🥉","4️⃣","5️⃣"][rank]
    return f"""<div class="num-card">
<div class="rank-badge">{medal}&nbsp; #{rank+1}위 &nbsp;·&nbsp; {pct:.1f}점</div>
<div style="margin:10px 0 4px">{balls_html}</div>
<div class="score-track"><div class="score-fill" style="width:{pct}%"></div></div>
<span class="info-chip">합계 {r['sum']}</span>
<span class="info-chip">홀 {r['odd']} : 짝 {r['even']}</span>
<span class="info-chip">저 {r['low']} : 고 {r['high']}</span>
<span class="info-chip">미출현 평균 {r['avg_gap']:.1f}회</span>
</div>"""

def render_reason_box(reasons):
    rows = "".join(f"<div class='reason-item'>{r}</div>" for r in reasons)
    return (
        "<div class='reason-box'>"
        "<div class='reason-title'>💡 이 번호를 추천한 이유</div>"
        + rows +
        "</div>"
    )

def render_blur_cards(cards):
    inner = "".join(
        render_num_card(i, r, 100 - i*6) for i, r in enumerate(cards)
    )
    return f'<div class="blur-wrap"><div class="blur-inner">{inner}</div>'


# ─────────────────────────────────────────
# 환영 모달
# ─────────────────────────────────────────
def show_welcome():
    if os.path.exists(WELCOME_FLAG): return
    if st.session_state.get("welcome_done"): return

    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
        <div class="welcome-card">
            <div style="font-size:52px;margin-bottom:12px">🧠</div>
            <div class="welcome-title">로또브레인에<br>오신 걸 환영합니다</div>
            <div class="welcome-feature"><span class="welcome-icon">🤖</span>AI 스코어링으로 최적 번호 조합 추천</div>
            <div class="welcome-feature"><span class="welcome-icon">📊</span>1~1200+회차 전체 통계 분석</div>
            <div class="welcome-feature"><span class="welcome-icon">⚖️</span>가중치 직접 조정으로 나만의 전략</div>
            <div class="welcome-feature"><span class="welcome-icon">📋</span>예측 히스토리 & 당첨 결과 추적</div>
            <br>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀  시작하기", type="primary", use_container_width=True):
            st.session_state["welcome_done"] = True
            st.session_state["trigger_update"] = True
            with open(WELCOME_FLAG, "w") as f: f.write("1")
            st.rerun()
    st.stop()


# ─────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────
with st.sidebar:
    # 로고
    st.markdown("""
    <div style="padding:4px 4px 20px">
        <div style="font-size:24px;font-weight:900;
                    background:linear-gradient(135deg,#f9ca24,#f0932b);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    background-clip:text;letter-spacing:-0.5px;line-height:1.1">
            🧠 로또브레인
        </div>
        <div style="font-size:10px;color:#2d3a47;font-weight:500;
                    letter-spacing:2.5px;text-transform:uppercase;margin-top:3px">
            LottoBrain v3.0
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 데이터 상태
    latest = core.get_latest_drw_no()
    if latest:
        st.markdown(f"""
        <div class="data-pill">
            <div class="data-dot"></div>
            <div class="data-pill-text">{latest}회차까지 수집됨</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);
                    border-radius:12px;padding:11px 14px;margin:12px 0;
                    font-size:13px;color:#f87171;font-weight:600">
            ⚠️ 데이터 없음 — 업데이트 필요
        </div>
        """, unsafe_allow_html=True)

    update_clicked = st.button("🔄  최신 데이터 업데이트", use_container_width=True)
    trigger = st.session_state.pop("trigger_update", False)

    if update_clicked or trigger:
        ph = st.empty()
        bar = st.progress(0)
        try:
            ph.info("📥 최신 회차 수집 중...")
            def _cb(cur, total):
                bar.progress(min(cur / total, 1.0))
            core.fetch_all(progress_cb=_cb)
            bar.progress(1.0)
            ph.info("🧠 AI 분석 준비 중...")
            time.sleep(0.6)
            bar.empty(); ph.empty()
            st.rerun()
        except core.NetworkError as e:
            bar.empty(); ph.empty()
            st.warning(f"📡 서버 연결 불가 — 기존 데이터로 분석합니다\n\n잠시 후 다시 시도해주세요.")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("---")

    # 네비게이션
    page = st.radio(
        "메뉴",
        ["🏆  이번 주 TOP 5", "🎰  번호 생성", "📊  통계 분석", "📋  예측 히스토리", "🔮  사주 번호", "⚙️  가중치 설정"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("<p style='color:#4a5568;font-size:11px;margin:0 0 6px;'>🛠️ 데모 도구</p>", unsafe_allow_html=True)
    if st.button("🔁 환영 화면 초기화", use_container_width=True):
        if os.path.exists(WELCOME_FLAG): os.remove(WELCOME_FLAG)
        st.session_state.pop("welcome_done", None)
        st.rerun()
    if st.button("🗑️ 생성 결과 초기화", use_container_width=True):
        st.session_state.pop("weekly_results", None)
        st.session_state.pop("generated", None)
        st.rerun()


# ─────────────────────────────────────────
# 환영 모달
# ─────────────────────────────────────────
show_welcome()


# ─────────────────────────────────────────
# 1. 이번 주 TOP 5
# ─────────────────────────────────────────
if "TOP 5" in page:
    latest = core.get_latest_drw_no()

    v_total = st.session_state.get("visit_total", _VISIT_BASE)
    v_today = st.session_state.get("visit_today", 0)
    st.markdown(f"""
    <div class="page-title">🏆 이번 주 최고의 번호 TOP 5</div>
    <div class="page-sub">AI가 {latest}회차까지의 데이터로 {latest+1 if latest else "?"}회차를 분석합니다 &nbsp;·&nbsp; 50,000개 조합 스코어링</div>
    <div style="display:flex;align-items:center;gap:16px;margin:10px 0 4px;font-size:12px;flex-wrap:wrap;">
      <span style="color:#f9ca24;">👁 오늘 방문자 &nbsp;<b>{v_today:,}명</b></span>
      <span style="color:#8a9ab0;">·</span>
      <span style="color:#a0aec0;">📊 누적 방문자 &nbsp;<b>{v_total:,}명</b></span>
      <span style="color:#8a9ab0;">·</span>
      <a href="https://open.kakao.com/o/px13lLqi" target="_blank"
         style="display:inline-flex;align-items:center;gap:5px;background:#FEE500;color:#3C1E1E;
                font-weight:700;font-size:11px;padding:4px 10px;border-radius:20px;
                text-decoration:none;line-height:1;">
        💬 카카오 오픈채팅
      </a>
    </div>
    """, unsafe_allow_html=True)

    if latest == 0:
        st.markdown(render_blur_cards(SAMPLE_CARDS), unsafe_allow_html=True)
        st.markdown("""
        <div class="blur-overlay" style="top:-100%;height:200%">
            <div style="font-size:40px">🧠</div>
            <div style="font-size:16px;font-weight:700;color:#e2e8f0;text-align:center;line-height:1.7">
                AI 분석 결과가 여기에 표시됩니다<br>
                <span style="font-size:13px;color:#4a5a6a">사이드바에서 데이터를 업데이트하세요</span>
            </div>
        </div></div>
        """, unsafe_allow_html=True)
        st.stop()

    weights = st.session_state.get("custom_weights", core.DEFAULT_WEIGHTS.copy())

    # 회차별 캐시 파일 (같은 회차는 항상 동일한 결과)
    _cache_file = f"/tmp/top5_{latest}.json"

    def _load_cached_results():
        try:
            with open(_cache_file) as f:
                return _json.load(f)
        except Exception:
            return []

    def _save_cached_results(res):
        try:
            with open(_cache_file, "w") as f:
                _json.dump(res, f)
        except Exception:
            pass

    # 세션에 없으면 캐시에서 복원
    if "weekly_results" not in st.session_state:
        cached = _load_cached_results()
        if cached:
            st.session_state["weekly_results"] = cached

    if st.button("✨  AI 번호 분석 시작", type="primary", use_container_width=True):
        cached = _load_cached_results()
        if cached:
            st.session_state["weekly_results"] = cached
        else:
            with st.spinner("🧠 50,000개 조합 분석 중..."):
                results = core.gen_best_weekly(5, weights)
            _save_cached_results(results)
            st.session_state["weekly_results"] = results

    results = st.session_state.get("weekly_results", [])

    if not results:
        st.markdown(render_blur_cards(SAMPLE_CARDS), unsafe_allow_html=True)
        st.markdown("""
        <div class="blur-overlay" style="top:-100%;height:200%">
            <div style="font-size:32px">✨</div>
            <div style="font-size:15px;font-weight:700;color:#c4ccd8;text-align:center">
                위 버튼을 눌러 AI 분석을 시작하세요
            </div>
        </div></div>
        """, unsafe_allow_html=True)
        st.stop()

    max_score = results[0]["score"]
    freq = core.get_frequency()
    last_app = core.get_last_appearance()
    for i, r in enumerate(results):
        pct = min(100.0, r["score"] / max_score * 100)
        st.markdown(render_num_card(i, r, pct), unsafe_allow_html=True)
        if i < 3:
            reasons = gen_reason(r, freq, last_app)
            if reasons:
                st.markdown(render_reason_box(reasons), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📋  히스토리에 저장", use_container_width=True):
        for r in results:
            core.save_prediction(r["nums"], latest + 1, "best_weekly")
        st.success(f"✅ {len(results)}게임 저장 완료 (대상: {latest+1}회차)")


# ─────────────────────────────────────────
# 2. 번호 생성
# ─────────────────────────────────────────
elif "번호 생성" in page:
    latest = core.get_latest_drw_no()
    st.markdown("""
    <div class="page-title">🎰 번호 생성</div>
    <div class="page-sub">전략을 선택하고 원하는 게임 수만큼 번호를 생성하세요</div>
    """, unsafe_allow_html=True)

    if latest == 0:
        st.markdown("""
        <div style="background:rgba(13,17,35,0.9);border-radius:20px;padding:48px;
                    text-align:center;border:1px solid rgba(255,255,255,0.06)">
            <div style="font-size:40px;margin-bottom:16px">🎰</div>
            <div style="font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:8px">
                번호 생성을 위해 데이터가 필요해요
            </div>
            <div style="font-size:13px;color:#4a5a6a">사이드바에서 데이터를 업데이트해주세요</div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    strategies = {
        "🎲  순수 랜덤":           core.gen_random,
        "📈  빈도 가중치 기반":     core.gen_frequency_weighted,
        "⚖️  균형 분석 기반":       core.gen_balanced,
        "🧊  콜드 번호 위주":       core.gen_cold,
    }

    col1, col2 = st.columns([3, 1])
    with col1:
        strategy = st.selectbox("전략 선택", list(strategies.keys()), label_visibility="collapsed")
    with col2:
        count = st.number_input("게임 수", min_value=1, max_value=20, value=5, label_visibility="collapsed")

    # 전략 설명
    descs = {
        "🎲  순수 랜덤": "1~45 중 완전 무작위 추출",
        "📈  빈도 가중치 기반": "역대 자주 나온 번호를 높은 확률로 선택",
        "⚖️  균형 분석 기반": "합계·홀짝·구간 분포를 고려한 균형 번호",
        "🧊  콜드 번호 위주": "오랫동안 나오지 않은 번호를 우선 선택",
    }
    st.markdown(f"""
    <div style="background:rgba(249,202,36,0.06);border:1px solid rgba(249,202,36,0.15);
                border-radius:10px;padding:10px 14px;font-size:12px;color:#8a9ab0;margin:8px 0 16px">
        💡 {descs.get(strategy,"")}
    </div>
    """, unsafe_allow_html=True)

    if st.button("🎯  번호 생성", type="primary", use_container_width=True):
        fn = strategies[strategy]
        st.session_state["generated"] = [fn() for _ in range(count)]
        st.session_state["gen_strategy"] = strategy

    generated = st.session_state.get("generated", [])
    if generated:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div style="font-size:16px;font-weight:700;color:#c4ccd8;margin-bottom:8px">
            생성된 번호</div>""", unsafe_allow_html=True)
        for i, nums in enumerate(generated):
            odd = sum(1 for n in nums if n % 2 == 1)
            st.markdown(f"""
            <div class="num-card">
                <div class="rank-badge">🎟 {i+1}게임</div>
                <div style="margin:10px 0 4px">{render_balls(nums)}</div>
                <span class="info-chip">합계 {sum(nums)}</span>
                <span class="info-chip">홀 {odd} : 짝 {6-odd}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📋  히스토리에 저장", use_container_width=True):
            for nums in generated:
                core.save_prediction(nums, latest + 1, st.session_state.get("gen_strategy", "manual"))
            st.success(f"✅ {len(generated)}게임 저장 완료 (대상: {latest+1}회차)")


# ─────────────────────────────────────────
# 3. 통계 분석
# ─────────────────────────────────────────
elif "통계" in page:
    st.markdown("""
    <div class="page-title">📊 통계 분석</div>
    <div class="page-sub">전체 당첨 이력을 기반으로 번호 패턴을 분석합니다</div>
    """, unsafe_allow_html=True)

    latest = core.get_latest_drw_no()
    if latest == 0:
        st.markdown("""
        <div style="background:rgba(13,17,35,0.9);border-radius:20px;padding:48px;
                    text-align:center;border:1px solid rgba(255,255,255,0.06)">
            <div style="font-size:40px;margin-bottom:16px">📊</div>
            <div style="font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:8px">통계를 보려면 데이터가 필요해요</div>
            <div style="font-size:13px;color:#4a5a6a">사이드바에서 데이터를 업데이트해주세요</div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    freq = core.get_frequency()
    last_app = core.get_last_appearance()
    all_draws = core.load_all_draws()
    total = len(all_draws)
    sums = [sum(list(r[1:7])) for r in all_draws]
    top_num = freq.most_common(1)[0]
    cold_nums = sorted(range(1, 46), key=lambda n: last_app.get(n, 9999), reverse=True)

    c1, c2, c3, c4 = st.columns(4)
    stats = [
        (str(total), "총 회차"),
        (f"{top_num[0]}번", f"최다 출현\n({top_num[1]}회)"),
        (f"{cold_nums[0]}번", f"최장 미출현\n({last_app.get(cold_nums[0],0)}회 전)"),
        (f"{sum(sums)/len(sums):.0f}", "평균 합계"),
    ]
    for col, (num, label) in zip([c1,c2,c3,c4], stats):
        with col:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-num">{num}</div>
                <div class="stat-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["번호별 출현 빈도", "합계 분포", "홀짝 분포", "미출현 현황"])

    _axis = dict(gridcolor="rgba(255,255,255,0.04)", zeroline=False)
    _base = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,17,35,0.6)",
        font=dict(color="#8a9ab0", family="Noto Sans KR, sans-serif", size=12),
        margin=dict(l=0, r=0, t=40, b=0),
        yaxis=_axis,
    )
    plotly_layout       = {**_base, "xaxis": _axis}
    plotly_layout_dtick = {**_base, "xaxis": dict(tickmode="linear", dtick=1, **_axis)}

    with tab1:
        df_freq = pd.DataFrame({
            "번호": list(range(1,46)),
            "출현 횟수": [freq[n] for n in range(1,46)],
            "구간": [f"{((n-1)//10)*10+1}~{((n-1)//10)*10+10}번대" for n in range(1,46)],
        })
        fig = px.bar(df_freq, x="번호", y="출현 횟수", color="구간",
                     color_discrete_sequence=["#f9ca24","#5b9cf6","#f87171","#94a3b8","#34d399"],
                     title=f"번호별 출현 횟수 (총 {total}회차)")
        fig.add_hline(y=total*6/45, line_dash="dash", line_color="#f9ca24",
                      annotation_text="평균", annotation_position="right")
        fig.update_layout(**plotly_layout_dtick)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig2 = px.histogram(sums, nbins=50, title="당첨번호 합계 분포",
                            labels={"value":"합계","count":"빈도"})
        fig2.update_traces(marker_color="#f9ca24", marker_line_color="#f0932b", marker_line_width=1)
        fig2.add_vline(x=138, line_dash="dash", line_color="#f87171",
                       annotation_text="138 (중심)", annotation_position="top right")
        fig2.update_layout(**plotly_layout)
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        odd_dist = Counter(sum(1 for n in list(r[1:7]) if n%2==1) for r in all_draws)
        df_odd = pd.DataFrame({
            "비율": [f"홀{k}:짝{6-k}" for k in sorted(odd_dist)],
            "빈도": [odd_dist[k] for k in sorted(odd_dist)],
        })
        fig3 = px.pie(df_odd, names="비율", values="빈도", title="홀짝 비율 분포",
                      color_discrete_sequence=["#f9ca24","#f0932b","#5b9cf6","#f87171","#34d399","#94a3b8","#a78bfa"])
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#8a9ab0"), margin=dict(t=40))
        st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        df_gap = pd.DataFrame({
            "번호": list(range(1,46)),
            "미출현 회차": [last_app.get(n,0) for n in range(1,46)],
        })
        df_gap["상태"] = df_gap["미출현 회차"].apply(
            lambda x: "🔥 핫 (5회 이내)" if x<=5 else ("❄️ 콜드 (15회 이상)" if x>=15 else "보통"))
        fig4 = px.bar(df_gap, x="번호", y="미출현 회차", color="상태",
                      color_discrete_map={"🔥 핫 (5회 이내)":"#f87171","보통":"#64748b","❄️ 콜드 (15회 이상)":"#5b9cf6"},
                      title="번호별 마지막 출현 이후 경과 회차")
        fig4.update_layout(**plotly_layout_dtick)
        st.plotly_chart(fig4, use_container_width=True)


# ─────────────────────────────────────────
# 4. 예측 히스토리
# ─────────────────────────────────────────
elif "히스토리" in page:
    st.markdown("""
    <div class="page-title">📋 예측 히스토리</div>
    <div class="page-sub">저장한 번호와 실제 당첨 결과를 비교합니다</div>
    """, unsafe_allow_html=True)

    updated = core.check_and_update_results()
    if updated:
        st.info(f"🔄 {updated}건의 결과가 업데이트되었습니다.")

    predictions = core.load_predictions()
    if not predictions:
        st.markdown("""
        <div style="background:rgba(13,17,35,0.9);border-radius:20px;padding:60px;
                    text-align:center;border:1px solid rgba(255,255,255,0.06)">
            <div style="font-size:40px;margin-bottom:16px">📋</div>
            <div style="font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:8px">
                저장된 예측 번호가 없어요
            </div>
            <div style="font-size:13px;color:#4a5a6a">
                이번 주 TOP 5 또는 번호 생성에서 번호를 저장하세요
            </div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    stats = core.get_prediction_stats()
    total_checked = sum(stats.values())
    if total_checked > 0:
        st.markdown("""<div style="font-size:14px;font-weight:700;color:#c4ccd8;margin:0 0 12px">
            📈 전체 적중 통계</div>""", unsafe_allow_html=True)
        cols = st.columns(5)
        items = [(6,"#f9ca24","6개"),(5,"#10b981","5개"),(4,"#5b9cf6","4개"),(3,"#64748b","3개"),(0,"#2d3a47","낙첨")]
        for col, (key, color, label) in zip(cols, items):
            cnt = stats.get(key, 0)
            with col:
                st.markdown(f"""
                <div class="stat-box" style="border-color:{color}30">
                    <div class="stat-num" style="background:none;-webkit-text-fill-color:{color};color:{color}">{cnt}</div>
                    <div class="stat-label">{label} 일치</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    for p in predictions:
        pred_nums, win_nums = p["pred"], p["win"]
        matched, bonus_match = p["matched"], p["bonus_match"]
        if matched is not None and win_nums:
            win_set = set(win_nums)
            highlight = set(pred_nums) & win_set
            color = "#f9ca24" if matched>=4 else ("#10b981" if matched==3 else "#475569")
            bonus_ball = f'<span class="ball ball-green" style="width:44px;height:44px;font-size:13px">{p["bonus"]}⭐</span>'
            st.markdown(f"""
            <div class="num-card" style="border-color:{color}40">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
                    <div>
                        <div class="rank-badge">#{p['id']} · {p['saved_at']}</div>
                        <div style="font-size:11px;color:#3d4a58;margin-top:4px">{p['strategy']}</div>
                    </div>
                    <div style="font-size:16px;font-weight:800;color:{color};text-align:right">
                        {grade_label(matched,bonus_match)}<br>
                        <span style="font-size:12px;font-weight:500">{matched}개 일치</span>
                    </div>
                </div>
                <div style="margin:6px 0">
                    <div style="font-size:11px;color:#3d4a58;margin-bottom:4px">내 번호</div>
                    {render_balls(pred_nums, highlight if highlight else set(pred_nums))}
                </div>
                <div style="margin:6px 0">
                    <div style="font-size:11px;color:#3d4a58;margin-bottom:4px">당첨번호 ({p['target_drw']}회차)</div>
                    {render_balls(win_nums)} {bonus_ball}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="num-card" style="border-color:rgba(91,156,246,0.25)">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                    <div class="rank-badge">#{p['id']} · {p['saved_at']}</div>
                    <div style="font-size:12px;color:#5b9cf6;font-weight:600">⏳ {p['target_drw']}회차 결과 대기</div>
                </div>
                <div>{render_balls(pred_nums)}</div>
                <span class="info-chip" style="margin-top:10px">{p['strategy']}</span>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# 5. 사주 번호
# ─────────────────────────────────────────
elif "사주" in page:
    import saju_core as saju

    st.markdown("""
    <div class="page-title">🔮 사주 번호 추천</div>
    <div class="page-sub">생년월일시를 입력하면 사주 오행을 분석해 맞춤 번호를 추천해드립니다</div>
    """, unsafe_allow_html=True)

    # ── 입력 폼 ──
    with st.form("saju_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            birth_year = st.number_input("태어난 연도", min_value=1930, max_value=2010, value=1990, step=1)
        with c2:
            birth_month = st.number_input("월", min_value=1, max_value=12, value=1, step=1)
        with c3:
            birth_day = st.number_input("일", min_value=1, max_value=31, value=1, step=1)

        HOUR_OPTIONS = {
            "모름 (자시 기준)": 23,
            "자시 (23~01시)": 23, "축시 (01~03시)": 1,
            "인시 (03~05시)": 3, "묘시 (05~07시)": 5,
            "진시 (07~09시)": 7, "사시 (09~11시)": 9,
            "오시 (11~13시)": 11, "미시 (13~15시)": 13,
            "신시 (15~17시)": 15, "유시 (17~19시)": 17,
            "술시 (19~21시)": 19, "해시 (21~23시)": 21,
        }
        birth_hour_label = st.selectbox("태어난 시간 (모르면 '모름' 선택)", list(HOUR_OPTIONS.keys()))
        birth_hour = HOUR_OPTIONS[birth_hour_label]

        count_saju = st.number_input("추천 게임 수", min_value=1, max_value=10, value=5, step=1)
        submitted = st.form_submit_button("🔮  사주 분석 시작", type="primary", use_container_width=True)

    if submitted:
        try:
            result = saju.calc_saju(birth_year, birth_month, birth_day, birth_hour)
        except Exception as e:
            st.error(f"날짜를 확인해주세요: {e}")
            st.stop()

        elements = result["elements"]
        yongshin = result["yongshin"]
        gishin   = result["gishin"]

        # ── 사주 8자 표시 ──
        st.markdown("<br>", unsafe_allow_html=True)
        pillar_parts = []
        for p in result["pillars"]:
            s_color = saju.ELEMENT_COLORS[saju.STEM_ELEMENT[p["stem"]]]
            b_color = saju.ELEMENT_COLORS[saju.BRANCH_ELEMENT[p["branch"]]]
            pillar_parts.append(
                f'<div style="text-align:center;flex:1;min-width:60px">'
                f'<div style="font-size:10px;color:#4a5a6a;margin-bottom:4px">{p["name"]}</div>'
                f'<div style="font-size:22px;font-weight:900;color:{s_color};line-height:1.2">{p["stem"]}</div>'
                f'<div style="font-size:22px;font-weight:900;color:{b_color};line-height:1.2">{p["branch"]}</div>'
                f'</div>'
            )
        pillar_html = "".join(pillar_parts)

        st.markdown(f"""
        <div style="background:rgba(13,17,35,0.9);border-radius:16px;
                    border:1px solid rgba(168,85,247,0.25);padding:20px 16px;margin-bottom:16px">
            <div style="font-size:12px;color:#a855f7;font-weight:700;margin-bottom:14px;letter-spacing:1px">
                사주 팔자 (四柱八字)
            </div>
            <div style="display:flex;gap:8px;justify-content:center">
                {pillar_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 오행 분포 ──
        total_chars = sum(elements.values())
        bar_parts = []
        for el, cnt in sorted(elements.items(), key=lambda x: -x[1]):
            pct = cnt / total_chars * 100
            color = saju.ELEMENT_COLORS[el]
            emoji = saju.ELEMENT_EMOJI[el]
            desc  = saju.ELEMENT_DESC[el]
            tag = ""
            if el == yongshin:
                tag = '<span style="font-size:10px;background:rgba(168,85,247,0.2);color:#a855f7;border-radius:4px;padding:1px 6px;margin-left:6px">용신</span>'
            elif el == gishin:
                tag = '<span style="font-size:10px;background:rgba(249,202,36,0.15);color:#f9ca24;border-radius:4px;padding:1px 6px;margin-left:6px">기신</span>'
            bar_parts.append(
                f'<div style="margin:8px 0">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">'
                f'<span style="font-size:14px">{emoji}</span>'
                f'<span style="font-size:13px;font-weight:700;color:{color}">{el}({cnt})</span>'
                f'<span style="font-size:11px;color:#4a5a6a">{desc}</span>'
                f'{tag}</div>'
                f'<div style="background:rgba(255,255,255,0.06);border-radius:99px;height:6px;overflow:hidden">'
                f'<div style="width:{pct:.0f}%;height:100%;background:{color};border-radius:99px;box-shadow:0 0 6px {color}88"></div>'
                f'</div></div>'
            )
        bar_html = "".join(bar_parts)

        yong_color = saju.ELEMENT_COLORS[yongshin]
        yong_emoji = saju.ELEMENT_EMOJI[yongshin]
        st.markdown(f"""
        <div style="background:rgba(13,17,35,0.9);border-radius:16px;
                    border:1px solid rgba(168,85,247,0.2);padding:20px 16px;margin-bottom:16px">
            <div style="font-size:12px;color:#a855f7;font-weight:700;margin-bottom:14px;letter-spacing:1px">
                오행 분포 분석
            </div>
            {bar_html}
            <div style="margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.05);
                        font-size:13px;color:#94a3b8;line-height:1.7">
                {yong_emoji} <b style="color:{yong_color}">용신 '{yongshin}'</b>
                — 당신에게 가장 필요한 기운입니다.<br>
                이 기운의 번호를 중심으로 행운의 번호를 추천해드립니다.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 번호 생성 ──
        freq = core.get_frequency() if core.get_latest_drw_no() else None

        st.markdown(f"""
        <div style="font-size:14px;font-weight:700;color:#c4ccd8;margin:20px 0 12px">
            {yong_emoji} 사주 맞춤 번호 추천
        </div>
        """, unsafe_allow_html=True)

        for i in range(int(count_saju)):
            nums = saju.gen_saju_numbers(result, freq)
            balls_html = "".join(
                f'<span class="ball {ball_color_class(n)}">{n}</span>'
                for n in nums
            )
            el_tags = ""
            for n in nums:
                # 이 번호가 어느 오행인지 찾기
                for el, pool in saju.ELEMENT_NUMBERS.items():
                    if n in pool:
                        el_tags += f'<span style="display:inline-block;font-size:10px;background:rgba(255,255,255,0.04);color:{saju.ELEMENT_COLORS[el]};border-radius:4px;padding:1px 5px;margin:2px">{saju.ELEMENT_EMOJI[el]}{n}</span>'
                        break

            card_html = (
                f'<div class="num-card" style="border-color:rgba(168,85,247,0.25);">'
                f'<div class="rank-badge" style="color:#a855f7;background:rgba(168,85,247,0.1);border-color:rgba(168,85,247,0.25)">🔮 #{i+1} · 사주 맞춤</div>'
                f'<div style="margin:10px 0 8px">{balls_html}</div>'
                f'<div style="margin-top:6px">{el_tags}</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📋  히스토리에 저장", use_container_width=True):
            latest = core.get_latest_drw_no()
            for i in range(int(count_saju)):
                nums = saju.gen_saju_numbers(result, freq)
                core.save_prediction(nums, latest + 1, "saju")
            st.success(f"✅ {count_saju}게임 저장 완료!")

    else:
        st.markdown("""
        <div style="background:rgba(13,17,35,0.9);border-radius:20px;padding:40px 32px;
                    text-align:center;border:1px solid rgba(168,85,247,0.2);margin-top:8px">
            <div style="font-size:48px;margin-bottom:16px">🔮</div>
            <div style="font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:8px">
                생년월일시를 입력하고 분석을 시작하세요
            </div>
            <div style="font-size:13px;color:#4a5a6a;line-height:1.7">
                사주 오행(목·화·토·금·수) 분포를 분석해<br>
                당신에게 맞는 행운의 번호를 추천해드립니다
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# 6. 가중치 설정
# ─────────────────────────────────────────
elif "가중치" in page:
    st.markdown("""
    <div class="page-title">⚙️ 스코어링 가중치 설정</div>
    <div class="page-sub">각 지표의 영향력을 조절해 나만의 AI 전략을 만드세요</div>
    """, unsafe_allow_html=True)

    if "custom_weights" not in st.session_state:
        st.session_state["custom_weights"] = core.DEFAULT_WEIGHTS.copy()

    w = st.session_state["custom_weights"]
    labels = {
        "frequency":    ("📊 역대 출현 빈도",      "역대에 자주 나온 번호 우대"),
        "trend":        ("🔥 최근 트렌드",          "최근 10회 출현 번호 가중"),
        "gap_bonus":    ("⏰ 미출현 타이밍",         "5~15회 쉬었다 나올 타이밍 우대"),
        "sum_fit":      ("⚖️ 합계 분포 적합도",     "실제 당첨 합계 중심값(138) 근접 우대"),
        "odd_even":     ("🔢 홀짝 균형",            "3홀3짝 조합 최고점"),
        "high_low":     ("📶 고저 균형",            "저:고 번호 균형 우대"),
        "zone_spread":  ("🗺️ 구간 분산",           "5개 구간에 골고루 분포 우대"),
        "consec_pen":   ("🚫 연속번호 페널티",      "3개 이상 연속번호 감점"),
        "birthday_pen": ("🎂 생일범위 페널티",      "1~31 과집중 감점"),
    }

    new_w = {}
    col1, col2 = st.columns(2)
    for i, (key, (label, desc)) in enumerate(labels.items()):
        with (col1 if i % 2 == 0 else col2):
            new_w[key] = st.slider(label, 0, 50, w[key], help=desc)

    st.markdown("<br>", unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        if st.button("✅  가중치 적용", type="primary", use_container_width=True):
            st.session_state["custom_weights"] = new_w
            st.session_state.pop("weekly_results", None)
            st.success("✅ 적용 완료! [이번 주 TOP 5]에서 다시 분석하세요.")
    with cb:
        if st.button("🔄  기본값 초기화", use_container_width=True):
            st.session_state["custom_weights"] = core.DEFAULT_WEIGHTS.copy()
            st.session_state.pop("weekly_results", None)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""<div style="font-size:14px;font-weight:700;color:#c4ccd8;margin-bottom:12px">
        현재 설정 vs 기본값 비교</div>""", unsafe_allow_html=True)
    df_w = pd.DataFrame({
        "지표": [v[0] for v in labels.values()],
        "현재값": [new_w[k] for k in labels],
        "기본값": [core.DEFAULT_WEIGHTS[k] for k in labels],
    })
    fig = go.Figure()
    fig.add_trace(go.Bar(name="현재값", x=df_w["지표"], y=df_w["현재값"],
                         marker_color="#f9ca24", marker_line_width=0))
    fig.add_trace(go.Bar(name="기본값", x=df_w["지표"], y=df_w["기본값"],
                         marker_color="rgba(91,156,246,0.4)", marker_line_width=0))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,17,35,0.6)",
        font=dict(color="#8a9ab0", family="Noto Sans KR, sans-serif"),
        barmode="group", margin=dict(l=0,r=0,t=20,b=0),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zeroline=False),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zeroline=False),
    )
    st.plotly_chart(fig, use_container_width=True)
