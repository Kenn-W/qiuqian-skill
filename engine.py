#!/usr/bin/env python3
"""六爻装卦引擎 — 起卦、识卦、装卦，输出 JSON。

Usage: python3 engine.py              # random cast
       python3 engine.py --help       # show options
       python3 engine.py --lines 7,7,8,6,9,7  # fixed lines for testing

Output: JSON to stdout, one line per hexagram detail.
"""

import json
import random
import sys
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

# ── 五行生克表 ──
# 相生: 木→火→土→金→水→木
WX_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 相克: 木→土→水→火→金→木
WX_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# ── 八卦二进制映射 (阳=1, 阴=0, 从初爻到三爻) ──
YAO_TO_TRIGRAM = {
    (1, 1, 1): ("☰", "乾"),
    (1, 1, 0): ("☱", "兑"),
    (1, 0, 1): ("☲", "离"),
    (1, 0, 0): ("☳", "震"),
    (0, 1, 1): ("☴", "巽"),
    (0, 1, 0): ("☵", "坎"),
    (0, 0, 1): ("☶", "艮"),
    (0, 0, 0): ("☷", "坤"),
}

TRIGRAM_NAME = {s: n for s, n in YAO_TO_TRIGRAM.values()}  # ☰→乾

# ── 地支五行 ──
DZ_WX = {
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
    "申": "金", "酉": "金",
    "亥": "水", "子": "水",
}

# ── 六兽 ──
LIUSHOU = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
STEM_TO_SHOU = {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2,
                "己": 3, "庚": 4, "辛": 4, "壬": 5, "癸": 5}

# ── 爻位名称 ──
POS_NAMES = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]


# ═══════════════════════════════════════════════
# 起卦
# ═══════════════════════════════════════════════

def toss_coins():
    """三钱起卦。每爻3枚铜钱，正3反2，求和得6/7/8/9。
    返回 [(yang:bool, moving:bool), ...] 初爻→上爻。"""
    lines = []
    for _ in range(6):
        total = sum(random.randint(2, 3) for _ in range(3))
        if total == 6:      # 老阴 ⚋⊙
            lines.append((False, True))
        elif total == 7:    # 少阳 ⚊
            lines.append((True, False))
        elif total == 8:    # 少阴 ⚋
            lines.append((False, False))
        else:               # total == 9 老阳 ⚊⊙
            lines.append((True, True))
    return lines


# ═══════════════════════════════════════════════
# 识卦
# ═══════════════════════════════════════════════

def trigram_from_yang(yangs):
    """三个 yang bool → (symbol, name)"""
    return YAO_TO_TRIGRAM[tuple(yangs)]


def find_hexagram(upper_symbol, lower_symbol, index):
    """在索引中查找匹配的卦"""
    for h in index["hexagrams"]:
        if h["upper"] == upper_symbol and h["lower"] == lower_symbol:
            return h
    return None


def identify(lines, index):
    """从六爻识别本卦、变卦、互卦。
    lines: [(yang, moving), ...] 初→上
    """
    y = [l[0] for l in lines]

    # 本卦
    lo_sym, lo_name = trigram_from_yang(y[:3])
    up_sym, up_name = trigram_from_yang(y[3:])
    ben = find_hexagram(up_sym, lo_sym, index)

    # 变卦 — 动爻翻转
    flipped = [(not a if m else a) for a, m in lines]
    flo_sym, flo_name = trigram_from_yang(flipped[:3])
    fup_sym, fup_name = trigram_from_yang(flipped[3:])
    bian = find_hexagram(fup_sym, flo_sym, index)

    # 互卦 — 二三四为下卦, 三四五为上卦
    hlo_sym, hlo_name = trigram_from_yang((y[1], y[2], y[3]))
    hup_sym, hup_name = trigram_from_yang((y[2], y[3], y[4]))
    hu = find_hexagram(hup_sym, hlo_sym, index)

    moving_positions = [i + 1 for i, (_, m) in enumerate(lines) if m]

    return {
        "ben": ben,
        "bian": bian,
        "hu": hu,
        "lines_raw": [{"yang": a, "moving": m} for a, m in lines],
        "moving_positions": moving_positions,
    }


# ═══════════════════════════════════════════════
# 装卦
# ═══════════════════════════════════════════════

def zhuang_gua(hex_info, lines, rules):
    """完整装卦，返回 line_details 列表。"""
    hex_id = hex_info["id"]
    upper_sym = hex_info["upper"]
    lower_sym = hex_info["lower"]

    # 1. 找宫位 + 世爻位置
    palace_name = gong_wuxing = gua_type = shi_pos = None
    for pname, pinfo in rules["bagong"]["palaces"].items():
        for h in pinfo["hexagrams"]:
            if h["id"] == hex_id:
                palace_name = pname
                gong_wuxing = pinfo["five_element"]
                gua_type = h["type"]
                shi_pos = h["shi_position"]
                break
        if palace_name:
            break

    # 2. 纳甲 — 地支
    lower_name = TRIGRAM_NAME[lower_sym]
    upper_name = TRIGRAM_NAME[upper_sym]
    branch_db = rules["najia"]["line_branches"]["details"]

    lower_br = branch_db[lower_name]  # 6 地支，初→上
    upper_br = branch_db[upper_name]

    # 下卦取前三爻，上卦取后三爻
    branches = [
        lower_br[0],  # 初
        lower_br[1],  # 二
        lower_br[2],  # 三
        upper_br[3],  # 四
        upper_br[4],  # 五
        upper_br[5],  # 上
    ]

    # 3. 六亲
    wuxing = [DZ_WX[b] for b in branches]
    liuqin = [get_liuqin(gong_wuxing, wx) for wx in wuxing]

    # 4. 世应
    ying_pos = ((shi_pos + 2) % 6) + 1  # 1→4, 2→5, 3→6, 4→1, 5→2, 6→3

    # 5. 六兽 (按日干)
    day_stem = get_day_stem()
    start_idx = STEM_TO_SHOU[day_stem]
    liushou = [LIUSHOU[(start_idx + i) % 6] for i in range(6)]

    # 组装
    line_details = []
    for i in range(6):
        pos = i + 1
        line_details.append({
            "pos": pos,
            "pos_name": POS_NAMES[i],
            "yang": lines[i][0],
            "moving": lines[i][1],
            "branch": branches[i],
            "wuxing": wuxing[i],
            "liuqin": liuqin[i],
            "shiying": "世" if pos == shi_pos else ("应" if pos == ying_pos else ""),
            "liushou": liushou[i],
        })

    return {
        "palace": palace_name,
        "palace_wuxing": gong_wuxing,
        "gua_type": gua_type,
        "shi_position": shi_pos,
        "ying_position": ying_pos,
        "day_stem": day_stem,
        "lines": line_details,
    }


def get_liuqin(gong_wx, yao_wx):
    """宫五行 vs 爻五行 → 六亲"""
    if gong_wx == yao_wx:
        return "兄弟"
    if WX_SHENG[gong_wx] == yao_wx:
        return "子孙"  # 宫生爻 = 我生
    if WX_SHENG[yao_wx] == gong_wx:
        return "父母"  # 爻生宫 = 生我
    if WX_KE[gong_wx] == yao_wx:
        return "妻财"  # 宫克爻 = 我克
    if WX_KE[yao_wx] == gong_wx:
        return "官鬼"  # 爻克宫 = 克我
    return "？"


# ═══════════════════════════════════════════════
# 干支
# ═══════════════════════════════════════════════

def get_day_stem():
    """计算今日天干"""
    d = date.today()
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12 * a - 3
    jdn = d.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    sex_day = (jdn + 49) % 60
    return "甲乙丙丁戊己庚辛壬癸"[sex_day % 10]


def get_sexagenary_day():
    """返回 (天干, 地支, 干支) 今天的日柱"""
    d = date.today()
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12 * a - 3
    jdn = d.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    sex_day = (jdn + 49) % 60
    stems = "甲乙丙丁戊己庚辛壬癸"
    branches = "子丑寅卯辰巳午未申酉戌亥"
    return stems[sex_day % 10], branches[sex_day % 12]


# ═══════════════════════════════════════════════
# 断卦辅助
# ═══════════════════════════════════════════════

def analyze_shiyin(zhuang):
    """分析世应关系，输出关键提示"""
    lines = zhuang["lines"]
    shi = next((l for l in lines if l["shiying"] == "世"), None)
    ying = next((l for l in lines if l["shiying"] == "应"), None)

    hints = []
    if shi and ying:
        # 世应生克
        if WX_SHENG[shi["wuxing"]] == ying["wuxing"]:
            hints.append("世生应：我生对方，付出有回报")
        elif WX_SHENG[ying["wuxing"]] == shi["wuxing"]:
            hints.append("应生世：对方生我，事易成")
        elif WX_KE[shi["wuxing"]] == ying["wuxing"]:
            hints.append("世克应：我克对方，可掌控")
        elif WX_KE[ying["wuxing"]] == shi["wuxing"]:
            hints.append("应克世：对方克我，须谨慎")
        elif shi["wuxing"] == ying["wuxing"]:
            hints.append("世应比和：双方相当，顺其自然")

    # 动爻位置
    moving = [l for l in lines if l["moving"]]
    for m in moving:
        if m["shiying"] == "世":
            hints.append(f"{m['pos_name']}动临世爻：自身变化，事在人为")
        if m["shiying"] == "应":
            hints.append(f"{m['pos_name']}动临应爻：对方/环境将变")

    # 用神持世
    if shi:
        hints.append(f"世爻{shi['liuqin']}持世：{shi['liuqin']}为当前重心")

    return hints


def score_dimensions(zhuang, ben_hex, moving_lines):
    """五维运势评分 (0-100) + 简评"""
    lines = zhuang["lines"]
    shi = next((l for l in lines if l["shiying"] == "世"), None)
    moving = [l for l in lines if l["moving"]]
    palace_wx = zhuang["palace_wuxing"]

    scores = {}

    # ── 事业 (看官鬼) ──
    guan_gui = [l for l in lines if l["liuqin"] == "官鬼"]
    score_career = 60  # baseline
    career_note = ""
    for g in guan_gui:
        if g["shiying"] == "世":
            score_career += 15
            career_note = "官鬼持世，事业心强，贵人提携"
            break
        elif g["moving"]:
            score_career += 10
            career_note = "官鬼暗动，事业有变，宜把握"
    if not career_note:
        if any(g["moving"] for g in guan_gui):
            career_note = "官鬼动，职场有新动向"
        elif guan_gui:
            career_note = "官鬼在位，事业平稳"
        else:
            career_note = "官鬼不显，事业非今日重点"
    # Adjust by 世 strength
    if shi and shi["moving"]:
        score_career += 5
    scores["事业"] = (min(95, score_career), career_note)

    # ── 财运 (看妻财) ──
    qi_cai = [l for l in lines if l["liuqin"] == "妻财"]
    score_wealth = 55
    wealth_note = ""
    for q in qi_cai:
        if q["shiying"] == "世":
            score_wealth += 15
            wealth_note = "妻财持世，财运自求，宜主动"
            break
        elif q["moving"]:
            score_wealth += 12
            wealth_note = "妻财动，有进账之象"
        elif q["shiying"] == "应":
            score_wealth += 8
            wealth_note = "妻财应爻，财在外，需争取"
    if not wealth_note:
        if qi_cai:
            wealth_note = "妻财平稳，无大进大出"
        else:
            wealth_note = "妻财不显，今日守成为上"
    # If 世克应 and 妻财 on 应 → good for wealth
    if shi:
        for q in qi_cai:
            if q["shiying"] == "应" and WX_KE.get(shi["wuxing"]) == q["wuxing"]:
                score_wealth += 5
    scores["财运"] = (min(95, score_wealth), wealth_note)

    # ── 感情 (看官鬼/妻财 + 应爻) ──
    score_love = 55
    love_note = ""
    # Check 世应 relationship
    ying = next((l for l in lines if l["shiying"] == "应"), None)
    if shi and ying:
        if WX_SHENG.get(shi["wuxing"]) == ying["wuxing"]:
            score_love += 15
            love_note = "世生应，你心向对方，主动表达"
        elif WX_SHENG.get(ying["wuxing"]) == shi["wuxing"]:
            score_love += 20
            love_note = "应生世，对方有意，心意相通"
        elif shi["wuxing"] == ying["wuxing"]:
            score_love += 10
            love_note = "世应比和，两情相悦，平稳发展"
        elif WX_KE.get(shi["wuxing"]) == ying["wuxing"]:
            score_love += 5
            love_note = "世克应，你主导但须照顾对方感受"
        elif WX_KE.get(ying["wuxing"]) == shi["wuxing"]:
            love_note = "应克世，对方强势，须调整心态"
    if not love_note:
        love_note = "感情平稳，顺其自然"
    scores["感情"] = (min(95, score_love), love_note)

    # ── 健康 (看世爻 + 子孙) ──
    score_health = 60
    health_note = ""
    zi_sun = [l for l in lines if l["liuqin"] == "子孙"]
    if shi:
        # Check if 世 is被克
        ke_shi = [l for l in lines if WX_KE.get(l["wuxing"]) == shi["wuxing"]]
        if ke_shi:
            score_health -= 10
            health_note = f"世爻被{ke_shi[0]['liuqin']}所克，注意身体"
    if zi_sun:
        health_note += " 子孙护身，小恙可愈" if health_note else "子孙在位，健康有保障"
    if not health_note:
        health_note = "健康平稳，注意作息"
    # If 世爻 moving, some health fluctuation
    if shi and shi["moving"]:
        score_health -= 5
    scores["健康"] = (min(95, max(20, score_health)), health_note.strip())

    # ── 人际 (看兄弟 + 应爻) ──
    score_social = 50
    social_note = ""
    xiong_di = [l for l in lines if l["liuqin"] == "兄弟"]
    for x in xiong_di:
        if x["moving"]:
            score_social -= 5
            social_note = "兄弟动，须防口舌竞争"
    if not social_note:
        if xiong_di:
            social_note = "兄弟在位，人脉可用但防竞争"
        else:
            social_note = "人际平和，无大波澜"
    # Check 应爻 for social
    if ying and shi and WX_SHENG.get(ying["wuxing"]) == shi["wuxing"]:
        score_social += 10
    scores["人际"] = (min(95, max(25, score_social)), social_note)

    return scores


# ═══════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════

def load_json(name):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def cast(lines_override=None):
    """主流程：起卦→识卦→装卦→断卦。返回完整结果 dict。"""
    rules = load_json("zhuang-gua-rules.json")
    index = load_json("index-64-full.json")
    hex_data = load_json("hexagrams-1-64.json")

    # 1. 起卦
    if lines_override:
        # lines_override 格式: [6,7,8,9,7,7] (初→上)
        raw = []
        for v in lines_override:
            if v == 6:
                raw.append((False, True))
            elif v == 7:
                raw.append((True, False))
            elif v == 8:
                raw.append((False, False))
            elif v == 9:
                raw.append((True, True))
    else:
        raw = toss_coins()

    # 2. 识卦
    id_result = identify(raw, index)

    # 3. 装卦
    zhuang = zhuang_gua(id_result["ben"], raw, rules)

    # 4. 取卦辞爻辞
    def find_hex_data(hex_id):
        for h in hex_data["hexagrams"]:
            if h["id"] == hex_id:
                return h
        return None

    ben_data = find_hex_data(id_result["ben"]["id"])
    bian_data = find_hex_data(id_result["bian"]["id"]) if id_result["bian"] else None
    hu_data = find_hex_data(id_result["hu"]["id"]) if id_result["hu"] else None

    # 取动爻爻辞
    _pos_char = {1: "初", 2: "二", 3: "三", 4: "四", 5: "五", 6: "上"}
    moving_texts = []
    if ben_data:
        for pos in id_result["moving_positions"]:
            for line in ben_data["lines"]:
                if _pos_char[pos] in line["pos"]:
                    moving_texts.append(line)
                    break

    # 5. 断卦
    hints = analyze_shiyin(zhuang)
    scores = score_dimensions(zhuang, ben_data, moving_texts)

    # 日柱
    stem, branch = get_sexagenary_day()
    sexagenary = f"{stem}{branch}"

    return {
        "date": date.today().isoformat(),
        "sexagenary_day": sexagenary,
        "day_stem": stem,
        "day_branch": branch,
        "lines_raw": id_result["lines_raw"],
        "moving_positions": id_result["moving_positions"],
        "ben": id_result["ben"],
        "bian": id_result["bian"],
        "hu": id_result["hu"],
        "zhuang": zhuang,
        "ben_data": ben_data,
        "bian_data": bian_data,
        "hu_data": hu_data,
        "moving_texts": moving_texts,
        "analysis_hints": hints,
        "scores": scores,
    }


def main():
    import argparse

    p = argparse.ArgumentParser(description="六爻装卦引擎")
    p.add_argument("--lines", help="固定六爻: 如 7,7,8,6,9,7 (初→上)")
    p.add_argument("--seed", type=int, help="随机种子")
    args = p.parse_args()

    if args.seed:
        random.seed(args.seed)

    if args.lines:
        lines_override = [int(x.strip()) for x in args.lines.split(",")]
        assert len(lines_override) == 6
        assert all(v in (6, 7, 8, 9) for v in lines_override)
    else:
        lines_override = None

    result = cast(lines_override)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
