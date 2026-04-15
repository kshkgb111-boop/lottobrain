#!/usr/bin/env python3
"""
로또 번호 생성기 + 통계 분석기  v2.0
동행복권 비공식 API로 역대 데이터 수집 후 분석 기반 번호 추천

신규 기능:
  - [H] 예측 히스토리: 내가 뽑은 번호 저장 → 실제 당첨번호와 자동 비교
  - [C] 커스텀 가중치: 스코어링 9개 지표 가중치 직접 조절
  - --auto CLI 옵션: 바로 TOP 5 출력 후 종료
"""

import argparse
import random
import sqlite3
import time
import sys
from datetime import datetime
from collections import Counter

try:
    import requests
except ImportError:
    print("requests 패키지가 필요합니다: pip install requests")
    sys.exit(1)


# ─────────────────────────────────────────
# DB 초기화
# ─────────────────────────────────────────
DB_PATH = "lotto.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            drw_no   INTEGER PRIMARY KEY,
            no1 INTEGER, no2 INTEGER, no3 INTEGER,
            no4 INTEGER, no5 INTEGER, no6 INTEGER,
            bonus   INTEGER,
            date    TEXT
        )
    """)
    # 예측 히스토리 테이블
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            saved_at TEXT,
            target_drw INTEGER,          -- 예측 대상 회차
            no1 INTEGER, no2 INTEGER, no3 INTEGER,
            no4 INTEGER, no5 INTEGER, no6 INTEGER,
            strategy TEXT,
            matched  INTEGER DEFAULT NULL,  -- 일치 개수 (확인 후 채워짐)
            bonus_match INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# 데이터 수집
# ─────────────────────────────────────────
def fetch_draw(drw_no: int) -> dict | None:
    url = "https://www.dhlottery.co.kr/common.do"
    params = {"method": "getLottoNumber", "drwNo": drw_no}
    try:
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        if data.get("returnValue") == "success":
            return data
    except Exception:
        pass
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
        (
            data["drwNo"],
            data["drwtNo1"], data["drwtNo2"], data["drwtNo3"],
            data["drwtNo4"], data["drwtNo5"], data["drwtNo6"],
            data["bnusNo"],
            data.get("drwNoDate", ""),
        ),
    )
    conn.commit()
    conn.close()


def fetch_all():
    print("  최신 회차 확인 중...")
    lo, hi = 1100, 1200
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
        print(f"  이미 최신 데이터입니다 (총 {end}회차)")
        return end

    total = end - start + 1
    print(f"  {start}회차 ~ {end}회차 ({total}건) 수집 중...")
    for i, drw_no in enumerate(range(start, end + 1), 1):
        data = fetch_draw(drw_no)
        if data:
            save_draw(data)
        if i % 50 == 0:
            print(f"  {i}/{total} 완료...")
        time.sleep(0.05)
    print(f"  수집 완료! (총 {end}회차까지)")
    return end


# ─────────────────────────────────────────
# 통계 분석
# ─────────────────────────────────────────
def load_all_numbers() -> list[list[int]]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT no1,no2,no3,no4,no5,no6 FROM draws ORDER BY drw_no"
    ).fetchall()
    conn.close()
    return [list(r) for r in rows]


def get_frequency() -> Counter:
    counter = Counter()
    for nums in load_all_numbers():
        counter.update(nums)
    return counter


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


def print_stats():
    all_draws = load_all_numbers()
    total = len(all_draws)
    if total == 0:
        print("  데이터가 없습니다. 먼저 [D]로 데이터를 수집하세요.")
        return

    freq = get_frequency()
    last_app = get_last_appearance()

    print(f"\n{'='*55}")
    print(f"  통계 분석 (총 {total}회차 기준)")
    print(f"{'='*55}")
    print(f"{'번호':>4} | {'출현횟수':>6} | {'출현율':>6} | {'마지막출현':>8}")
    print(f"{'─'*4}-+-{'─'*6}-+-{'─'*6}-+-{'─'*8}")
    for num in range(1, 46):
        cnt = freq[num]
        rate = cnt / total * 100
        last = last_app.get(num, 9999)
        last_str = f"{last}회 전" if last < 9999 else "미출현"
        print(f"{num:>4} | {cnt:>6} | {rate:>5.1f}% | {last_str:>8}")

    print(f"\n[ 자주 나온 TOP 10 ]")
    for num, cnt in freq.most_common(10):
        bar = "█" * (cnt // 10)
        print(f"  {num:>2}번: {cnt}회 {bar}")

    print(f"\n[ 최근 10회 미출현 번호 ]")
    cold = sorted(n for n, v in last_app.items() if v >= 10)
    print(f"  {cold}")


# ─────────────────────────────────────────
# 번호 생성 전략
# ─────────────────────────────────────────
def gen_random() -> list[int]:
    return sorted(random.sample(range(1, 46), 6))


def gen_frequency_weighted() -> list[int]:
    freq = get_frequency()
    if not freq:
        return gen_random()
    numbers = list(range(1, 46))
    weights = [freq.get(n, 1) for n in numbers]
    chosen: set[int] = set()
    while len(chosen) < 6:
        chosen.add(random.choices(numbers, weights=weights, k=1)[0])
    return sorted(chosen)


def gen_balanced() -> list[int]:
    freq = get_frequency()
    last_app = get_last_appearance()
    numbers = list(range(1, 46))
    weights = []
    for n in numbers:
        w = freq.get(n, 1)
        if last_app.get(n, 0) >= 10:
            w += last_app[n] * 2
        if n <= 31:
            w = int(w * 0.85)
        weights.append(w)

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


def gen_cold_numbers() -> list[int]:
    last_app = get_last_appearance()
    pool = sorted(range(1, 46), key=lambda n: last_app.get(n, 9999), reverse=True)[:20]
    return sorted(random.sample(pool, 6))


# ─────────────────────────────────────────
# 스코어링 가중치 (기본값)
# ─────────────────────────────────────────
DEFAULT_WEIGHTS = {
    "frequency":   20,   # 역대 출현 빈도
    "trend":        5,   # 최근 10회 트렌드
    "gap_bonus":    8,   # 5~15회 미출현 타이밍
    "sum_fit":     30,   # 합계 분포 (중심 138)
    "odd_even":    15,   # 홀짝 균형
    "high_low":    15,   # 고저 균형
    "zone_spread":  5,   # 구간 분산
    "consec_pen":  20,   # 연속번호 페널티
    "birthday_pen":10,   # 생일범위(1~31) 과도 페널티
}


def score_combination(
    nums: list[int],
    freq: Counter,
    last_app: dict,
    recent_draws: list[list[int]],
    w: dict,
) -> float:
    score = 0.0

    # 1. 역대 빈도
    avg_freq = sum(freq.values()) / 45
    score += (sum(freq.get(n, 0) / avg_freq for n in nums) / 6) * w["frequency"]

    # 2. 최근 트렌드
    recent_freq = Counter(n for draw in recent_draws[-10:] for n in draw)
    score += sum(recent_freq.get(n, 0) for n in nums) * w["trend"]

    # 3. 미출현 보너스 (5~15회)
    for n in nums:
        gap = last_app.get(n, 99)
        if 5 <= gap <= 15:
            score += w["gap_bonus"]
        elif gap > 15:
            score += w["gap_bonus"] * 0.4

    # 4. 합계 분포
    distance = abs(sum(nums) - 138)
    score += max(0, w["sum_fit"] - distance * 0.4)

    # 5. 홀짝 균형
    odd = sum(1 for n in nums if n % 2 == 1)
    score += {3: 1.0, 2: 0.5, 4: 0.5, 1: 0.1, 5: 0.1, 0: -0.3, 6: -0.3}.get(odd, 0) * w["odd_even"]

    # 6. 고저 균형
    low = sum(1 for n in nums if n <= 22)
    score += {3: 1.0, 2: 0.5, 4: 0.5, 1: 0.1, 5: 0.1, 0: -0.3, 6: -0.3}.get(low, 0) * w["high_low"]

    # 7. 구간 분산
    zones = [0] * 5
    for n in nums:
        zones[min((n - 1) // 9, 4)] += 1
    score += sum(1 for z in zones if z > 0) * w["zone_spread"]

    # 8. 연속번호 페널티
    consec = sum(1 for i in range(5) if nums[i+1] - nums[i] == 1)
    if consec >= 3:
        score -= w["consec_pen"]
    elif consec == 2:
        score -= w["consec_pen"] * 0.25

    # 9. 생일범위 페널티
    bday = sum(1 for n in nums if n <= 31)
    if bday >= 5:
        score -= w["birthday_pen"]
    elif bday <= 2:
        score += w["birthday_pen"] * 0.5

    return score


def gen_best_weekly(top_n: int = 5, weights: dict = None) -> list[tuple]:
    w = weights or DEFAULT_WEIGHTS.copy()
    freq = get_frequency()
    last_app = get_last_appearance()
    all_draws = load_all_numbers()
    if not all_draws:
        return []

    numbers = list(range(1, 46))
    pool_weights = []
    for n in numbers:
        wt = freq.get(n, 1) * 1.0
        gap = last_app.get(n, 0)
        if 5 <= gap <= 15:
            wt *= 1.5
        elif gap > 15:
            wt *= 1.2
        if n > 31:
            wt *= 1.1
        pool_weights.append(wt)

    SAMPLE_SIZE = 50000
    print(f"  {SAMPLE_SIZE:,}개 조합 분석 중...", end="", flush=True)

    seen: set[tuple] = set()
    scored = []
    attempts = 0
    while len(scored) < SAMPLE_SIZE and attempts < SAMPLE_SIZE * 3:
        attempts += 1
        chosen: set[int] = set()
        while len(chosen) < 6:
            chosen.add(random.choices(numbers, weights=pool_weights, k=1)[0])
        key = tuple(sorted(chosen))
        if key in seen:
            continue
        seen.add(key)
        s = score_combination(list(key), freq, last_app, all_draws, w)
        scored.append((list(key), s))

    print(" 완료!")
    scored.sort(key=lambda x: x[1], reverse=True)

    result = []
    for nums, s in scored[:top_n]:
        odd = sum(1 for n in nums if n % 2 == 1)
        low = sum(1 for n in nums if n <= 22)
        result.append((nums, s, {
            "score": s,
            "sum": sum(nums),
            "odd": odd,
            "even": 6 - odd,
            "low": low,
            "high": 6 - low,
            "avg_gap": sum(last_app.get(n, 0) for n in nums) / 6,
        }))
    return result


def print_best_weekly(weights: dict = None, save_history: bool = False):
    latest = get_latest_drw_no()
    if latest == 0:
        print("\n  먼저 [D]로 데이터를 수집하세요!")
        return

    target_drw = latest + 1
    print(f"\n{'='*60}")
    print(f"  ★ 이번 주 최고의 번호 조합 TOP 5  (대상: {target_drw}회차)")
    print(f"{'='*60}")
    print(f"  ▸ 합계·홀짝·고저 균형 + 출현빈도 + 미출현 패턴 종합 분석")
    print(f"  ▸ 50,000개 조합을 스코어링하여 상위 5개 선정")
    print(f"{'─'*60}")

    results = gen_best_weekly(5, weights)
    if not results:
        print("  데이터가 부족합니다.")
        return

    max_score = results[0][2]["score"]
    for rank, (nums, score, info) in enumerate(results, 1):
        pct = min(100, score / max_score * 100)
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        balls = "  ".join(f"\033[1;33m[{n:>2}]\033[0m" for n in nums)
        print(f"\n  #{rank}  점수: {pct:5.1f}점  [{bar}]")
        print(f"  {balls}")
        print(
            f"  합계 {info['sum']:>3}  |  홀 {info['odd']}:짝 {info['even']}"
            f"  |  저 {info['low']}:고 {info['high']}  |  평균 미출현 {info['avg_gap']:.1f}회"
        )

        if save_history:
            _save_prediction(nums, target_drw, "best_weekly")

    if save_history:
        print(f"\n  예측 번호 {len(results)}게임이 히스토리에 저장되었습니다.")

    print(f"\n{'─'*60}")
    print(f"  ※ 통계적 분석 기반이며, 당첨을 보장하지 않습니다.")
    print(f"{'='*60}\n")
    return results


# ─────────────────────────────────────────
# 예측 히스토리
# ─────────────────────────────────────────
def _save_prediction(nums: list[int], target_drw: int, strategy: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO predictions
           (saved_at, target_drw, no1,no2,no3,no4,no5,no6, strategy)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (datetime.now().strftime("%Y-%m-%d %H:%M"), target_drw,
         nums[0], nums[1], nums[2], nums[3], nums[4], nums[5], strategy),
    )
    conn.commit()
    conn.close()


def _check_and_update_results():
    """DB에 저장된 당첨번호와 예측 번호를 비교하여 matched 업데이트"""
    conn = sqlite3.connect(DB_PATH)
    # matched가 NULL인 예측 중 당첨번호가 존재하는 것 처리
    rows = conn.execute(
        "SELECT id, target_drw, no1,no2,no3,no4,no5,no6 FROM predictions WHERE matched IS NULL"
    ).fetchall()

    updated = 0
    for row in rows:
        pred_id, target, *pred_nums = row
        draw = conn.execute(
            "SELECT no1,no2,no3,no4,no5,no6,bonus FROM draws WHERE drw_no=?", (target,)
        ).fetchone()
        if not draw:
            continue
        win_nums = set(draw[:6])
        bonus = draw[6]
        pred_set = set(pred_nums)
        matched = len(pred_set & win_nums)
        bonus_match = 1 if (matched == 5 and bonus in pred_set) else 0
        conn.execute(
            "UPDATE predictions SET matched=?, bonus_match=? WHERE id=?",
            (matched, bonus_match, pred_id),
        )
        updated += 1

    conn.commit()
    conn.close()
    return updated


def _grade(matched: int, bonus: int) -> str:
    if matched == 6:             return "\033[1;31m1등\033[0m"
    if matched == 5 and bonus:   return "\033[1;33m2등\033[0m"
    if matched == 5:             return "\033[1;32m3등\033[0m"
    if matched == 4:             return "4등"
    if matched == 3:             return "5등"
    return "낙첨"


def menu_history():
    updated = _check_and_update_results()
    if updated:
        print(f"\n  {updated}건의 결과가 업데이트되었습니다.")

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """SELECT p.id, p.saved_at, p.target_drw,
                  p.no1,p.no2,p.no3,p.no4,p.no5,p.no6,
                  p.strategy, p.matched, p.bonus_match,
                  d.no1,d.no2,d.no3,d.no4,d.no5,d.no6,d.bonus
           FROM predictions p
           LEFT JOIN draws d ON p.target_drw = d.drw_no
           ORDER BY p.id DESC
           LIMIT 30"""
    ).fetchall()
    conn.close()

    if not rows:
        print("\n  저장된 예측 번호가 없습니다.")
        print("  [W]에서 번호 생성 후 저장 여부를 선택하세요.")
        return

    print(f"\n{'='*70}")
    print(f"  예측 히스토리 (최근 30건)")
    print(f"{'='*70}")

    for r in rows:
        (pid, saved_at, target_drw,
         p1,p2,p3,p4,p5,p6, strategy,
         matched, bonus_match,
         w1,w2,w3,w4,w5,w6,wbonus) = r

        pred_balls = " ".join(f"[{n:>2}]" for n in [p1,p2,p3,p4,p5,p6])

        if matched is not None:
            grade = _grade(matched, bonus_match)
            win_set = {w1,w2,w3,w4,w5,w6}
            pred_set = {p1,p2,p3,p4,p5,p6}
            colored = []
            for n in [p1,p2,p3,p4,p5,p6]:
                if n in win_set:
                    colored.append(f"\033[1;32m[{n:>2}]\033[0m")
                else:
                    colored.append(f"[{n:>2}]")
            result_str = f"{' '.join(colored)}  → {matched}개 일치  {grade}"
            win_str = f"당첨: {w1} {w2} {w3} {w4} {w5} {w6} +{wbonus}"
        else:
            result_str = pred_balls + "  → 결과 대기 중"
            win_str = "아직 추첨 전"

        print(f"\n  #{pid}  {saved_at}  ({target_drw}회차 예측)  [{strategy}]")
        print(f"  예측: {result_str}")
        print(f"  {win_str}")

    print(f"\n{'='*70}")

    # 적중 통계 요약
    conn = sqlite3.connect(DB_PATH)
    stats = conn.execute(
        "SELECT matched, COUNT(*) FROM predictions WHERE matched IS NOT NULL GROUP BY matched ORDER BY matched DESC"
    ).fetchall()
    conn.close()
    if stats:
        print("\n  [ 전체 적중 통계 ]")
        total_checked = sum(c for _, c in stats)
        for matched, cnt in stats:
            bar = "█" * cnt
            print(f"  {matched}개 일치: {cnt:>4}건  {bar}")
        print(f"  총 확인된 게임: {total_checked}건")


def menu_save_prediction(nums_list: list[list[int]], target_drw: int, strategy: str):
    for nums in nums_list:
        _save_prediction(nums, target_drw, strategy)
    print(f"  {len(nums_list)}게임이 히스토리에 저장되었습니다! ({target_drw}회차 예측)")


# ─────────────────────────────────────────
# 커스텀 가중치 설정
# ─────────────────────────────────────────
WEIGHT_LABELS = {
    "frequency":   "역대 출현 빈도      (기본 20)",
    "trend":       "최근 10회 트렌드    (기본  5)",
    "gap_bonus":   "미출현 타이밍 보너스 (기본  8)",
    "sum_fit":     "합계 분포 적합도    (기본 30)",
    "odd_even":    "홀짝 균형           (기본 15)",
    "high_low":    "고저 균형           (기본 15)",
    "zone_spread": "구간 분산           (기본  5)",
    "consec_pen":  "연속번호 페널티     (기본 20)",
    "birthday_pen":"생일범위 페널티     (기본 10)",
}


def menu_custom_weights(current: dict) -> dict:
    print(f"\n{'='*55}")
    print("  커스텀 가중치 설정")
    print(f"{'='*55}")
    print("  각 지표의 가중치를 입력하세요. (엔터 = 현재값 유지)\n")

    new_w = current.copy()
    for key, label in WEIGHT_LABELS.items():
        val = input(f"  {label} → 현재 [{current[key]:>3}] 새값: ").strip()
        if val.lstrip("-").isdigit():
            new_w[key] = int(val)

    print("\n  [ 적용된 가중치 ]")
    for key, label in WEIGHT_LABELS.items():
        changed = " ← 변경됨" if new_w[key] != DEFAULT_WEIGHTS[key] else ""
        print(f"  {label}: {new_w[key]}{changed}")
    return new_w


# ─────────────────────────────────────────
# 공통 출력 유틸
# ─────────────────────────────────────────
STRATEGIES = {
    "1": ("순수 랜덤",          gen_random),
    "2": ("빈도 가중치 기반",    gen_frequency_weighted),
    "3": ("균형 잡힌 분석 기반", gen_balanced),
    "4": ("콜드 번호 위주",      gen_cold_numbers),
}


def print_numbers(nums: list[int], label: str = ""):
    balls = "  ".join(f"\033[1;33m[{n:>2}]\033[0m" for n in nums)
    if label:
        print(f"\n  [{label}]")
    print(f"  {balls}")
    print(
        f"  합계: {sum(nums)}  |  홀수: {sum(1 for n in nums if n%2)}개"
        f"  |  짝수: {sum(1 for n in nums if not n%2)}개"
    )


# ─────────────────────────────────────────
# CLI --auto 모드
# ─────────────────────────────────────────
def auto_mode():
    """--auto: 데이터 업데이트 후 TOP 5 출력하고 종료"""
    init_db()
    print("\n[ 로또 번호 자동 추천 모드 ]")
    fetch_all()
    print_best_weekly(save_history=True)


# ─────────────────────────────────────────
# 메인 메뉴
# ─────────────────────────────────────────
def main():
    init_db()
    custom_weights = DEFAULT_WEIGHTS.copy()

    print("\n" + "="*55)
    print("       로또 6/45 번호 생성기  v2.0")
    print("="*55)

    while True:
        latest = get_latest_drw_no()
        print(f"\n  현재 DB: {latest}회차까지 저장됨")
        has_custom = custom_weights != DEFAULT_WEIGHTS
        custom_tag = "  ← 커스텀 가중치 적용 중" if has_custom else ""
        print(f"""
  [D] 데이터 수집/업데이트
  [S] 통계 보기
  [W] ★ 이번 주 최고의 번호 TOP 5{custom_tag}
  [H] 예측 히스토리 보기 / 결과 확인
  [C] 커스텀 가중치 설정
  [1] 순수 랜덤 생성
  [2] 빈도 가중치 기반 생성
  [3] 균형 잡힌 분석 기반 생성
  [4] 콜드 번호 위주 생성
  [A] 모든 전략으로 한 번에 생성
  [Q] 종료
""")
        choice = input("  선택 > ").strip().upper()

        if choice == "Q":
            print("\n  행운을 빕니다!\n")
            break

        elif choice == "D":
            print("\n  데이터 수집 시작...")
            fetch_all()

        elif choice == "S":
            if latest == 0:
                print("\n  먼저 [D]로 데이터를 수집하세요!")
            else:
                print_stats()

        elif choice == "W":
            if latest == 0:
                print("\n  먼저 [D]로 데이터를 수집하세요!")
                continue
            results = print_best_weekly(weights=custom_weights)
            if results:
                save = input("  히스토리에 저장할까요? (y/N) > ").strip().lower()
                if save == "y":
                    nums_list = [r[0] for r in results]
                    menu_save_prediction(nums_list, latest + 1, "best_weekly")

        elif choice == "H":
            menu_history()

        elif choice == "C":
            custom_weights = menu_custom_weights(custom_weights)
            reset = input("\n  기본값으로 초기화할까요? (y/N) > ").strip().lower()
            if reset == "y":
                custom_weights = DEFAULT_WEIGHTS.copy()
                print("  기본값으로 초기화되었습니다.")

        elif choice in STRATEGIES:
            if latest == 0:
                print("\n  먼저 [D]로 데이터를 수집하세요!")
                continue
            name, fn = STRATEGIES[choice]
            cnt = input(f"  {name} - 몇 게임? (기본 5) > ").strip()
            cnt = int(cnt) if cnt.isdigit() else 5
            print(f"\n  ── {name} ──")
            generated = []
            for i in range(1, cnt + 1):
                nums = fn()
                generated.append(nums)
                print_numbers(nums, f"{i}게임")
            save = input("\n  히스토리에 저장할까요? (y/N) > ").strip().lower()
            if save == "y":
                menu_save_prediction(generated, latest + 1, name)

        elif choice == "A":
            if latest == 0:
                print("\n  먼저 [D]로 데이터를 수집하세요!")
                continue
            print(f"\n  ── 전략별 번호 추천 ──")
            for key, (name, fn) in STRATEGIES.items():
                nums = fn()
                print_numbers(nums, name)

        else:
            print("  잘못된 입력입니다.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="로또 번호 생성기")
    parser.add_argument("--auto", action="store_true",
                        help="데이터 업데이트 후 TOP 5 즉시 출력")
    args = parser.parse_args()

    if args.auto:
        auto_mode()
    else:
        main()
