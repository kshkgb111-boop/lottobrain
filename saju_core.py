"""
사주팔자 기반 로또 번호 추천 모듈
"""
import random
from datetime import date

# ── 천간 (10 Heavenly Stems) ──
STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]

# ── 지지 (12 Earthly Branches) ──
BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

# ── 오행 매핑 ──
STEM_ELEMENT = {
    "갑": "목", "을": "목",
    "병": "화", "정": "화",
    "무": "토", "기": "토",
    "경": "금", "신": "금",
    "임": "수", "계": "수",
}
BRANCH_ELEMENT = {
    "자": "수", "축": "토",
    "인": "목", "묘": "목",
    "진": "토", "사": "화",
    "오": "화", "미": "토",
    "신": "금", "유": "금",
    "술": "토", "해": "수",
}

# ── 오행별 번호 매핑 (1~45) ──
ELEMENT_NUMBERS = {
    "목": [1, 2, 11, 12, 21, 22, 31, 32, 41, 42],
    "화": [3, 4, 13, 14, 23, 24, 33, 34, 43, 44],
    "토": [5, 6, 15, 16, 25, 26, 35, 36, 45],
    "금": [7, 8, 17, 18, 27, 28, 37, 38],
    "수": [9, 10, 19, 20, 29, 30, 39, 40],
}

# ── 오행 UI 정보 ──
ELEMENT_COLORS = {
    "목": "#4ade80",
    "화": "#f87171",
    "토": "#fbbf24",
    "금": "#e2e8f0",
    "수": "#60a5fa",
}
ELEMENT_EMOJI = {
    "목": "🌳",
    "화": "🔥",
    "토": "🌍",
    "금": "⚡",
    "수": "💧",
}
ELEMENT_DESC = {
    "목": "성장·창조·추진력",
    "화": "열정·표현·직관",
    "토": "안정·신뢰·중용",
    "금": "결단·논리·완성",
    "수": "지혜·유연·잠재력",
}


# ─────────────────────────────────────────
# 사주 계산
# ─────────────────────────────────────────

def _year_pillar(year: int) -> tuple[str, str]:
    """년주: (year - 4) mod 60"""
    stem_idx   = (year - 4) % 10
    branch_idx = (year - 4) % 12
    return STEMS[stem_idx], BRANCHES[branch_idx]


def _month_pillar(year: int, month: int) -> tuple[str, str]:
    """월주: 절기 대신 양력 월 기준 간략화 (오호둔월법)"""
    # 월지: 1월=인(2), 2월=묘(3), ..., 12월=축(1)
    branch_idx = (month + 1) % 12
    # 오호둔월법: 년간 인덱스 % 5 → 월간 시작점
    year_stem_idx = (year - 4) % 10
    month_stem_base = [2, 4, 6, 8, 0][year_stem_idx % 5]  # 병·무·경·임·갑
    stem_idx = (month_stem_base + month - 1) % 10
    return STEMS[stem_idx], BRANCHES[branch_idx]


def _day_pillar(birth_date: date) -> tuple[str, str]:
    """일주: 2000-01-01 = 갑신(甲申) 기준"""
    ref = date(2000, 1, 1)
    delta = (birth_date - ref).days
    stem_idx   = (0 + delta) % 10   # 갑=0
    branch_idx = (8 + delta) % 12   # 신=8
    return STEMS[stem_idx], BRANCHES[branch_idx]


def _hour_pillar(birth_date: date, hour: int) -> tuple[str, str]:
    """시주: 일간 기준 오자둔시법"""
    # 시지: 자시=23~01시, 이후 2시간마다 순환
    branch_idx = ((hour + 1) // 2) % 12
    # 오자둔시법: 일간 인덱스 % 5 → 시간 시작점
    day_stem, _ = _day_pillar(birth_date)
    day_stem_idx = STEMS.index(day_stem)
    stem_base = [0, 2, 4, 6, 8][day_stem_idx % 5]  # 갑·병·무·경·임
    stem_idx = (stem_base + branch_idx) % 10
    return STEMS[stem_idx], BRANCHES[branch_idx]


def calc_saju(year: int, month: int, day: int, hour: int) -> dict:
    """
    사주 8자 계산.

    Returns:
        {
          "pillars": [ {"name":"년주","stem":"갑","branch":"자"}, ... ],
          "elements": {"목":2, "화":2, "토":2, "금":1, "수":1},
          "yongshin": "수",   # 가장 부족한 오행
          "gishin":   "목",   # 가장 많은 오행
        }
    """
    birth_date = date(year, month, day)

    pillars = [
        {"name": "년주", "stem": _year_pillar(year)[0],              "branch": _year_pillar(year)[1]},
        {"name": "월주", "stem": _month_pillar(year, month)[0],      "branch": _month_pillar(year, month)[1]},
        {"name": "일주", "stem": _day_pillar(birth_date)[0],         "branch": _day_pillar(birth_date)[1]},
        {"name": "시주", "stem": _hour_pillar(birth_date, hour)[0],  "branch": _hour_pillar(birth_date, hour)[1]},
    ]

    # 오행 카운트 (8자 각각 집계)
    elements = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    for p in pillars:
        elements[STEM_ELEMENT[p["stem"]]] += 1
        elements[BRANCH_ELEMENT[p["branch"]]] += 1

    sorted_els = sorted(elements.items(), key=lambda x: x[1])
    yongshin = sorted_els[0][0]   # 최소
    gishin   = sorted_els[-1][0]  # 최대

    return {
        "pillars":  pillars,
        "elements": elements,
        "yongshin": yongshin,
        "gishin":   gishin,
    }


# ─────────────────────────────────────────
# 사주 기반 번호 추천
# ─────────────────────────────────────────

def gen_saju_numbers(saju: dict, freq: dict | None = None) -> list[int]:
    """
    사주 분석 결과로 로또 번호 6개 생성.
    - 용신(부족한 기운) 번호에서 3개
    - 2번째 부족한 오행에서 2개
    - 균형 오행에서 1개
    - freq 가중치로 당첨 통계 반영
    """
    elements = saju["elements"]
    sorted_els = sorted(elements.items(), key=lambda x: x[1])  # 오름차순

    pool_priority = [e for e, _ in sorted_els]  # [부족→풍부] 순서

    def weighted_pick(pool: list[int], n: int, exclude: set) -> list[int]:
        candidates = [x for x in pool if x not in exclude]
        if not candidates:
            candidates = [x for x in range(1, 46) if x not in exclude]
        if freq:
            weights = [freq.get(x, 1) + 1 for x in candidates]
            chosen = []
            while len(chosen) < n and candidates:
                total = sum(weights)
                probs  = [w / total for w in weights]
                idx = random.choices(range(len(candidates)), weights=probs)[0]
                chosen.append(candidates.pop(idx))
                weights.pop(idx)
            return chosen
        else:
            return random.sample(candidates, min(n, len(candidates)))

    chosen: set[int] = set()

    # 용신 → 3개
    nums = weighted_pick(ELEMENT_NUMBERS[pool_priority[0]], 3, chosen)
    chosen.update(nums)

    # 2번째 부족 → 2개
    nums = weighted_pick(ELEMENT_NUMBERS[pool_priority[1]], 2, chosen)
    chosen.update(nums)

    # 균형(중간) → 1개
    nums = weighted_pick(ELEMENT_NUMBERS[pool_priority[2]], 1, chosen)
    chosen.update(nums)

    # 혹시 6개 미만이면 채우기
    while len(chosen) < 6:
        n = random.randint(1, 45)
        chosen.add(n)

    return sorted(list(chosen))[:6]
