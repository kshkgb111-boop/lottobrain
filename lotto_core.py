"""
로또 핵심 로직 (DB, 수집, 분석, 생성)
app.py(Streamlit)와 lotto.py(CLI) 공용
"""

import os
import random
import sqlite3
import time
from collections import Counter
from datetime import datetime

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    requests = None

# DB 경로 결정:
# 1) LOTTOBRAIN_DATA_DIR 환경변수 (launcher.py 배포용)
# 2) Streamlit Cloud: 소스 폴더가 읽기 전용이므로 /tmp/ 에 복사해서 사용
# 3) 로컬 개발: 현재 디렉토리
def _resolve_db_path() -> str:
    import shutil
    env_dir = os.environ.get("LOTTOBRAIN_DATA_DIR", "")
    if env_dir:
        return os.path.join(env_dir, "lotto.db")

    # 현재 디렉토리 쓰기 가능 여부 확인
    local_db = "lotto.db"
    try:
        with open(local_db, "ab"):
            pass
        return local_db  # 로컬 개발 환경
    except (IOError, OSError):
        pass

    # Streamlit Cloud 등 읽기 전용 환경 → /tmp/ 사용
    tmp_db = "/tmp/lotto.db"
    if not os.path.exists(tmp_db):
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lotto.db")
        if os.path.exists(src):
            shutil.copy2(src, tmp_db)
    return tmp_db

DB_PATH = _resolve_db_path()

# ─────────────────────────────────────────
# DB
# ─────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            drw_no INTEGER PRIMARY KEY,
            no1 INTEGER, no2 INTEGER, no3 INTEGER,
            no4 INTEGER, no5 INTEGER, no6 INTEGER,
            bonus INTEGER, date TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            saved_at TEXT,
            target_drw INTEGER,
            no1 INTEGER, no2 INTEGER, no3 INTEGER,
            no4 INTEGER, no5 INTEGER, no6 INTEGER,
            strategy TEXT,
            matched  INTEGER DEFAULT NULL,
            bonus_match INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# 데이터 수집
# ─────────────────────────────────────────
_SESSION = None
_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def _get_session():
    global _SESSION
    if _SESSION is None and requests:
        _SESSION = requests.Session()
        _SESSION.headers.update(_HEADERS)
    return _SESSION


def fetch_draw(drw_no: int) -> dict | None:
    """superkts.com 에서 특정 회차 당첨 정보 수집"""
    if not requests:
        return None
    import re
    s = _get_session()
    try:
        r = s.get(f"http://www.superkts.com/lotto/{drw_no}", timeout=8, verify=False)
        desc = re.search(r'<meta name="description" content="([^"]+)"', r.text)
        if not desc:
            return None
        text = desc.group(1)
        nums = re.search(r'당첨번호는\s*([\d,]+)\s*보너스\s*(\d+)', text)
        date = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', text)
        if not nums or not date:
            return None
        n = [int(x) for x in nums.group(1).split(",")]
        if len(n) != 6:
            return None
        y, m, d = date.group(1), date.group(2).zfill(2), date.group(3).zfill(2)
        return {
            "drwNo": drw_no,
            "drwtNo1": n[0], "drwtNo2": n[1], "drwtNo3": n[2],
            "drwtNo4": n[3], "drwtNo5": n[4], "drwtNo6": n[5],
            "bnusNo": int(nums.group(2)),
            "drwNoDate": f"{y}-{m}-{d}",
            "returnValue": "success",
        }
    except Exception:
        return None


def get_latest_drw_no() -> int:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT MAX(drw_no) FROM draws").fetchone()
    conn.close()
    return row[0] or 0


def save_draw(data: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO draws VALUES (?,?,?,?,?,?,?,?,?)",
        (data["drwNo"], data["drwtNo1"], data["drwtNo2"], data["drwtNo3"],
         data["drwtNo4"], data["drwtNo5"], data["drwtNo6"],
         data["bnusNo"], data.get("drwNoDate", "")),
    )
    conn.commit()
    conn.close()


class NetworkError(Exception):
    pass


def _get_latest_drw_no_remote() -> int:
    """superkts.com 메인 페이지에서 최신 회차 번호 파싱"""
    import re
    s = _get_session()
    try:
        r = s.get("http://www.superkts.com/lotto/", timeout=8, verify=False)
        m = re.search(r'href="/lotto/(\d+)"[^>]*>\s*\1회', r.text)
        if m:
            return int(m.group(1))
        # fallback: gnb에서 첫 번째 회차
        m2 = re.search(r'/lotto/(\d{4})"', r.text)
        if m2:
            return int(m2.group(1))
    except Exception:
        pass
    return 0


def fetch_all(progress_cb=None) -> int:
    """전체 회차 수집. progress_cb(current, total) 콜백 선택
    네트워크 실패 시 NetworkError 발생"""

    # 연결 가능 여부 사전 확인
    test = fetch_draw(1)
    if test is None:
        raise NetworkError("데이터 서버에 연결할 수 없습니다.\n잠시 후 다시 시도해주세요.")

    # 최신 회차 파악
    end = _get_latest_drw_no_remote()
    if end == 0:
        # fallback: 이진 탐색
        lo, hi = get_latest_drw_no() or 1100, (get_latest_drw_no() or 1100) + 100
        while fetch_draw(hi):
            lo = hi
            hi += 50
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if fetch_draw(mid):
                lo = mid
            else:
                hi = mid
        end = lo

    existing = get_latest_drw_no()
    start = existing + 1
    if start > end:
        return end

    total = end - start + 1
    fail_count = 0
    for i, drw_no in enumerate(range(start, end + 1), 1):
        data = fetch_draw(drw_no)
        if data:
            save_draw(data)
            fail_count = 0
        else:
            fail_count += 1
            if fail_count >= 5:
                raise NetworkError("연속 5회 요청 실패 — 네트워크 연결을 확인하세요.")
        if progress_cb:
            progress_cb(i, total)
        time.sleep(0.05)
    return end


# ─────────────────────────────────────────
# 통계
# ─────────────────────────────────────────
def load_all_draws() -> list[tuple]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT drw_no,no1,no2,no3,no4,no5,no6,bonus,date FROM draws ORDER BY drw_no"
    ).fetchall()
    conn.close()
    return rows


def load_all_numbers() -> list[list[int]]:
    return [list(r[1:7]) for r in load_all_draws()]


def get_frequency() -> Counter:
    c = Counter()
    for nums in load_all_numbers():
        c.update(nums)
    return c


def get_last_appearance() -> dict[int, int]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT drw_no,no1,no2,no3,no4,no5,no6 FROM draws ORDER BY drw_no DESC"
    ).fetchall()
    conn.close()
    last = {}
    for i, row in enumerate(rows):
        for num in row[1:]:
            if num not in last:
                last[num] = i
    return last


# ─────────────────────────────────────────
# 번호 생성
# ─────────────────────────────────────────
def gen_random() -> list[int]:
    return sorted(random.sample(range(1, 46), 6))


def gen_frequency_weighted() -> list[int]:
    freq = get_frequency()
    if not freq:
        return gen_random()
    nums = list(range(1, 46))
    w = [freq.get(n, 1) for n in nums]
    chosen: set[int] = set()
    while len(chosen) < 6:
        chosen.add(random.choices(nums, weights=w, k=1)[0])
    return sorted(chosen)


def gen_balanced() -> list[int]:
    freq = get_frequency()
    last_app = get_last_appearance()
    numbers = list(range(1, 46))
    weights = []
    for n in numbers:
        wt = freq.get(n, 1)
        if last_app.get(n, 0) >= 10:
            wt += last_app[n] * 2
        if n <= 31:
            wt = int(wt * 0.85)
        weights.append(wt)
    for _ in range(10000):
        chosen: set[int] = set()
        while len(chosen) < 6:
            chosen.add(random.choices(numbers, weights=weights, k=1)[0])
        nums = sorted(chosen)
        odd = sum(1 for n in nums if n % 2 == 1)
        consec = sum(1 for i in range(5) if nums[i+1] - nums[i] == 1)
        if 100 <= sum(nums) <= 175 and 2 <= odd <= 4 and consec <= 2:
            return nums
    return gen_random()


def gen_cold() -> list[int]:
    last_app = get_last_appearance()
    pool = sorted(range(1, 46), key=lambda n: last_app.get(n, 9999), reverse=True)[:20]
    return sorted(random.sample(pool, 6))


# ─────────────────────────────────────────
# 스코어링
# ─────────────────────────────────────────
DEFAULT_WEIGHTS = {
    "frequency": 20, "trend": 5, "gap_bonus": 8, "sum_fit": 30,
    "odd_even": 15, "high_low": 15, "zone_spread": 5,
    "consec_pen": 20, "birthday_pen": 10,
}


def score_combination(nums, freq, last_app, recent_draws, w) -> float:
    score = 0.0
    avg_freq = sum(freq.values()) / 45
    score += (sum(freq.get(n, 0) / avg_freq for n in nums) / 6) * w["frequency"]

    recent_freq = Counter(n for draw in recent_draws[-10:] for n in draw)
    score += sum(recent_freq.get(n, 0) for n in nums) * w["trend"]

    for n in nums:
        gap = last_app.get(n, 99)
        score += w["gap_bonus"] if 5 <= gap <= 15 else (w["gap_bonus"] * 0.4 if gap > 15 else 0)

    score += max(0, w["sum_fit"] - abs(sum(nums) - 138) * 0.4)

    odd = sum(1 for n in nums if n % 2 == 1)
    m = {3: 1.0, 2: 0.5, 4: 0.5, 1: 0.1, 5: 0.1, 0: -0.3, 6: -0.3}
    score += m.get(odd, 0) * w["odd_even"]

    low = sum(1 for n in nums if n <= 22)
    score += m.get(low, 0) * w["high_low"]

    zones = [0] * 5
    for n in nums:
        zones[min((n - 1) // 9, 4)] += 1
    score += sum(1 for z in zones if z > 0) * w["zone_spread"]

    consec = sum(1 for i in range(5) if nums[i+1] - nums[i] == 1)
    score -= w["consec_pen"] if consec >= 3 else (w["consec_pen"] * 0.25 if consec == 2 else 0)

    bday = sum(1 for n in nums if n <= 31)
    score -= w["birthday_pen"] if bday >= 5 else (-w["birthday_pen"] * 0.5 if bday <= 2 else 0)

    return score


def gen_best_weekly(top_n=5, weights=None, sample_size=50000) -> list[tuple]:
    w = weights or DEFAULT_WEIGHTS.copy()
    freq = get_frequency()
    last_app = get_last_appearance()
    all_draws = load_all_numbers()
    if not all_draws:
        return []

    numbers = list(range(1, 46))
    pool_w = []
    for n in numbers:
        wt = freq.get(n, 1) * 1.0
        gap = last_app.get(n, 0)
        wt *= 1.5 if 5 <= gap <= 15 else (1.2 if gap > 15 else 1.0)
        if n > 31:
            wt *= 1.1
        pool_w.append(wt)

    seen: set[tuple] = set()
    scored = []
    attempts = 0
    while len(scored) < sample_size and attempts < sample_size * 3:
        attempts += 1
        chosen: set[int] = set()
        while len(chosen) < 6:
            chosen.add(random.choices(numbers, weights=pool_w, k=1)[0])
        key = tuple(sorted(chosen))
        if key in seen:
            continue
        seen.add(key)
        scored.append((list(key), score_combination(list(key), freq, last_app, all_draws, w)))

    scored.sort(key=lambda x: x[1], reverse=True)
    result = []
    for nums, s in scored[:top_n]:
        odd = sum(1 for n in nums if n % 2 == 1)
        low = sum(1 for n in nums if n <= 22)
        result.append({
            "nums": nums, "score": s,
            "sum": sum(nums), "odd": odd, "even": 6 - odd,
            "low": low, "high": 6 - low,
            "avg_gap": sum(last_app.get(n, 0) for n in nums) / 6,
        })
    return result


# ─────────────────────────────────────────
# 예측 히스토리
# ─────────────────────────────────────────
def save_prediction(nums: list[int], target_drw: int, strategy: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO predictions (saved_at,target_drw,no1,no2,no3,no4,no5,no6,strategy) VALUES (?,?,?,?,?,?,?,?,?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M"), target_drw,
         nums[0], nums[1], nums[2], nums[3], nums[4], nums[5], strategy),
    )
    conn.commit()
    conn.close()


def check_and_update_results() -> int:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id,target_drw,no1,no2,no3,no4,no5,no6 FROM predictions WHERE matched IS NULL"
    ).fetchall()
    updated = 0
    for row in rows:
        pid, target, *pred = row
        draw = conn.execute(
            "SELECT no1,no2,no3,no4,no5,no6,bonus FROM draws WHERE drw_no=?", (target,)
        ).fetchone()
        if not draw:
            continue
        win = set(draw[:6])
        bonus = draw[6]
        matched = len(set(pred) & win)
        bonus_match = 1 if matched == 5 and bonus in pred else 0
        conn.execute("UPDATE predictions SET matched=?,bonus_match=? WHERE id=?",
                     (matched, bonus_match, pid))
        updated += 1
    conn.commit()
    conn.close()
    return updated


def load_predictions() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT p.id, p.saved_at, p.target_drw,
               p.no1,p.no2,p.no3,p.no4,p.no5,p.no6,
               p.strategy, p.matched, p.bonus_match,
               d.no1,d.no2,d.no3,d.no4,d.no5,d.no6,d.bonus
        FROM predictions p
        LEFT JOIN draws d ON p.target_drw = d.drw_no
        ORDER BY p.id DESC LIMIT 50
    """).fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "id": r[0], "saved_at": r[1], "target_drw": r[2],
            "pred": list(r[3:9]), "strategy": r[9],
            "matched": r[10], "bonus_match": r[11],
            "win": list(r[12:18]) if r[12] else None,
            "bonus": r[18],
        })
    return result


def get_prediction_stats() -> dict:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT matched, COUNT(*) FROM predictions WHERE matched IS NOT NULL GROUP BY matched"
    ).fetchall()
    conn.close()
    return {m: c for m, c in rows}
