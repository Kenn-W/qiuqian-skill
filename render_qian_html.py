#!/usr/bin/env python3
"""签文图片渲染器 (HTML/CSS + Playwright) — 六爻求签结果生成 PNG 长条签文图。

Usage: python3 engine.py | python3 render_qian_html.py [-o qian.png]
       python3 render_qian_html.py --test
"""

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent


# ═══ 卦辞简译 ═══
JUDGMENT_BRIEF = {
    "乾":"自强不息，大有作为","坤":"厚德载物，以柔克刚","屯":"万事开头难，耐心可成",
    "蒙":"启蒙发智，宜学习请教","需":"等待时机，勿急躁冒进","訟":"争讼不利，退一步开阔",
    "師":"行险而顺，宜团队协作","比":"亲附和合，广结善缘","小畜":"小有积蓄，积少成多",
    "履":"如履薄冰，谨慎行事","泰":"天地交泰，万事亨通","否":"天地闭塞，韬光养晦",
    "同人":"志同道合，利合作交友","大有":"大丰收，一切顺遂","謙":"谦逊自持，终获善果",
    "豫":"愉悦安乐，顺势而动","隨":"顺势而行，跟从正道","蠱":"革除弊病，除旧布新",
    "臨":"居高临下，宜督导关怀","觀":"观察入微，审时度势","噬嗑":"咬合决断，宜解决纠纷",
    "賁":"外饰内质，宜文宜朴","剝":"剥落衰颓，守静待时","復":"一阳来复，万象更新",
    "无妄":"不妄为，守正防意外","大畜":"厚积薄发，蓄力待时","頤":"颐养身心，注意口腹",
    "大過":"过犹不及，调整平衡","坎":"身处险境，步步为营","離":"依附光明，借势而上",
    "咸":"感应互通，感情顺遂","恆":"持之以恒，长久之道","遯":"退避自保，以退为进",
    "大壯":"强盛壮大，勿逞强","晉":"蒸蒸日上，前途光明","明夷":"光明受损，隐忍待时",
    "家人":"家庭和睦，宜顾内务","睽":"乖离不合，小事可为","蹇":"艰难险阻，宜求助贵人",
    "解":"困难解除，万事缓和","損":"损下益上，有舍有得","益":"增益福祉，利于前进",
    "夬":"决断果敢，当机立断","姤":"不期而遇，随机应变","萃":"汇聚一堂，利集体活动",
    "升":"步步高升，前景可期","困":"困顿受阻，守正待援","井":"井养不穷，稳定为上",
    "革":"变革图新，顺势改革","鼎":"鼎立更新，革故鼎新","震":"雷震百里，临危不乱",
    "艮":"止于当止，适可而止","漸":"循序渐进，水到渠成","歸妹":"婚嫁之象，宜顾关系",
    "豐":"丰盛盈满，惜福感恩","旅":"旅居在外，谨慎行事","巽":"柔顺谦逊，顺势而为",
    "兌":"喜悦和合，沟通顺利","渙":"涣散离散，宜凝聚人心","節":"节制有度，适可而止",
    "中孚":"诚信为本，以诚待人","小過":"小事可为，大事待时","既濟":"事已成就，居安思危",
    "未濟":"事尚未成，继续努力",
}


def score_color(s):
    if s >= 70:
        return "#4A8C3F"
    if s >= 50:
        return "#D4942B"
    return "#C0392B"


def wx_color(wx):
    return {"金":"白/银","木":"绿/青","水":"黑/蓝","火":"红/紫","土":"黄/棕"}.get(wx, "?")


def gong_dir(palace):
    return {"乾宫":"西北","坤宫":"西南","震宫":"东","巽宫":"东南",
            "坎宫":"北","离宫":"南","艮宫":"东北","兑宫":"西"}.get(palace, "中")


# ═══ 卦象线数据 ═══

def compute_bian_lines(lines_raw):
    """变卦: 动爻翻转阴阳."""
    return [
        {"yang": not l["yang"] if l["moving"] else l["yang"], "moving": False}
        for l in lines_raw
    ]


def compute_hu_lines(lines_raw):
    """互卦: 取本卦 2,3,4,3,4,5 爻 (零索引: 1,2,3,2,3,4)."""
    idx = [1, 2, 3, 2, 3, 4]
    return [
        {"yang": lines_raw[i]["yang"], "moving": False}
        for i in idx
    ]


def reverse_lines(lines):
    """反转爻序: 初→上 变为 上→初 (用于渲染)."""
    return list(reversed(lines))


# ═══ 视图模型 ═══

def build_view(data):
    """从引擎 JSON 构建模板视图模型."""
    bz = data["zhuang"]
    is_jing = len(data["moving_positions"]) == 0
    brief = JUDGMENT_BRIEF.get(data["ben"]["name"], "顺势守正，依卦而行")

    # ── 卦象线数据 ──
    raw = data["lines_raw"]
    ben_lines = reverse_lines([dict(l) for l in raw])  # 上→初

    if is_jing:
        hexagrams = {
            "ben": {"name": data["ben"]["name"], "lines": ben_lines, "label": "本卦"},
        }
    else:
        bian_lines = reverse_lines(compute_bian_lines(raw))
        hu_lines = reverse_lines(compute_hu_lines(raw))
        hexagrams = {
            "ben":  {"name": data["ben"]["name"],  "lines": ben_lines,  "label": "本卦"},
            "bian": {"name": data["bian"]["name"], "lines": bian_lines, "label": "变卦"},
            "hu":   {"name": data["hu"]["name"],   "lines": hu_lines,   "label": "互卦"},
        }

    # ── 装卦表行 (上→初) ──
    zhuang_lines = list(reversed(bz["lines"]))

    # ── 动爻文本 ──
    moving_texts = data.get("moving_texts", [])

    # ── 五维评分 ──
    dims = ["事业", "财运", "感情", "健康", "人际"]
    scores = []
    for dim in dims:
        s, note = data["scores"][dim]
        scores.append({
            "dim": dim,
            "score": s,
            "note": note[:24] if len(note) > 24 else note,
            "color": score_color(s),
        })

    # ── 结语 ──
    ben_name = data["ben"]["name"]
    judgment = data["ben_data"]["judgment"]
    best_dim = max(dims, key=lambda d: data["scores"][d][0])
    worst_dim = min(dims, key=lambda d: data["scores"][d][0])
    shi_l = next((l for l in bz["lines"] if l["shiying"] == "世"), None)

    if is_jing:
        conclusion = (
            f"{ben_name}卦静而无动，今日运势平稳。"
            f"卦辞点明「{judgment[:12]}」。"
            f"今日{best_dim}最佳，{worst_dim}稍逊。宜守正顺势，踏实行事。"
        )
    else:
        mp = "、".join(str(p) for p in data["moving_positions"])
        conclusion = (
            f"{ben_name}卦动于{mp}。"
            f"世{shi_l['liuqin']}持世于{shi_l['pos_name']}。"
            f"今日{best_dim}为亮点，{worst_dim}须留意。"
            f"卦曰「{judgment[:8]}」，顺势而行。"
        )

    # ── 建议 ──
    advice = {
        "dos": f"把握{best_dim}机会，顺势而为，稳中求进",
        "donts": f"忽视{worst_dim}，冲动决策，过度消耗",
        "lucky_color": wx_color(bz["palace_wuxing"]),
        "lucky_direction": gong_dir(bz["palace"]),
    }

    return {
        "date": data["date"],
        "sexagenary_day": data["sexagenary_day"],
        "is_jing": is_jing,
        "hexagrams": hexagrams,
        "palace_info": f"{bz['palace']} · {bz['gua_type']}",
        "judgment": judgment,
        "brief": brief,
        "moving_texts": moving_texts,
        "zhuang_lines": zhuang_lines,
        "scores": scores,
        "conclusion": conclusion,
        "advice": advice,
    }


# ═══ 渲染 ═══

def render_html(view, css_path=None):
    """Jinja2 渲染 HTML 字符串."""
    from jinja2 import Environment, FileSystemLoader

    if css_path is None:
        css_path = ROOT / "static" / "qianwen.css"

    css = css_path.read_text(encoding="utf-8")

    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")))
    template = env.get_template("qianwen.html")
    return template.render(css=css, **view)


def screenshot(html, output_path, width=640):
    """Playwright 截图 HTML 为 PNG."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 800})
        page.set_content(html, timeout=10000)
        # Wait for fonts to load
        page.wait_for_timeout(500)
        # Get full page height
        body = page.locator("body")
        height = body.bounding_box()["height"]
        # Resize and screenshot
        page.set_viewport_size({"width": width, "height": int(height) + 20})
        page.screenshot(path=output_path, full_page=True)
        browser.close()


# ═══ main ═══

def main():
    import argparse
    ap = argparse.ArgumentParser(description="签文图片渲染器 (HTML/CSS + Playwright)")
    ap.add_argument("--input", "-i", help="JSON 输入 (默认 stdin)")
    ap.add_argument("--output", "-o", default="qianwen.png", help="输出路径")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--html", help="仅输出 HTML 到文件 (不截图)")
    args = ap.parse_args()

    if args.test:
        data = {
            "date": str(date.today()), "sexagenary_day": "己卯",
            "day_stem": "己", "day_branch": "卯",
            "lines_raw": [{"yang": True, "moving": False}, {"yang": True, "moving": False},
                          {"yang": False, "moving": True}, {"yang": True, "moving": False},
                          {"yang": False, "moving": False}, {"yang": True, "moving": False}],
            "moving_positions": [3],
            "ben": {"id": 38, "symbol": "䷥", "name": "睽", "pinyin": "kui", "upper": "☲", "lower": "☱", "ctext": "kui"},
            "bian": {"id": 14, "symbol": "䷍", "name": "大有", "pinyin": "da-you", "upper": "☲", "lower": "☰", "ctext": "da-you"},
            "hu": {"id": 63, "symbol": "䷾", "name": "既濟", "pinyin": "ji-ji", "upper": "☵", "lower": "☲", "ctext": "ji-ji"},
            "zhuang": {"palace": "艮宫", "palace_wuxing": "土", "gua_type": "四世", "shi_position": 4, "ying_position": 1, "day_stem": "己",
                "lines": [
                    {"pos": 1, "pos_name": "初爻", "yang": True, "moving": False, "branch": "巳", "wuxing": "火", "liuqin": "父母", "shiying": "应", "liushou": "螣蛇"},
                    {"pos": 2, "pos_name": "二爻", "yang": True, "moving": False, "branch": "卯", "wuxing": "木", "liuqin": "官鬼", "shiying": "", "liushou": "白虎"},
                    {"pos": 3, "pos_name": "三爻", "yang": False, "moving": True, "branch": "丑", "wuxing": "土", "liuqin": "兄弟", "shiying": "", "liushou": "玄武"},
                    {"pos": 4, "pos_name": "四爻", "yang": True, "moving": False, "branch": "酉", "wuxing": "金", "liuqin": "子孙", "shiying": "世", "liushou": "青龙"},
                    {"pos": 5, "pos_name": "五爻", "yang": False, "moving": False, "branch": "未", "wuxing": "土", "liuqin": "兄弟", "shiying": "", "liushou": "朱雀"},
                    {"pos": 6, "pos_name": "上爻", "yang": True, "moving": False, "branch": "巳", "wuxing": "火", "liuqin": "父母", "shiying": "", "liushou": "勾陈"},
                ]},
            "ben_data": {"id": 38, "symbol": "䷥", "name": "睽", "judgment": "小事吉。", "lines": []},
            "bian_data": {"id": 14, "symbol": "䷍", "name": "大有", "judgment": "元亨。", "lines": []},
            "hu_data": {"id": 63, "symbol": "䷾", "name": "既濟", "judgment": "亨，小利貞，初吉終亂。", "lines": []},
            "moving_texts": [{"pos": "六三", "text": "見輿曳，其牛掣，其人天且劓，无初有終。"}],
            "analysis_hints": ["应克世：对方克我，须谨慎"],
            "scores": {"事业": [60, "官鬼在位，事业平稳"], "财运": [55, "妻财不显，今日守成为上"],
                       "感情": [55, "应克世，对方强势"], "健康": [50, "子孙护身，注意饮食"],
                       "人际": [45, "兄弟暗动，须防口舌"]},
        }
    else:
        inp = open(args.input) if args.input else sys.stdin
        data = json.load(inp)

    view = build_view(data)
    css_path = ROOT / "static" / "qianwen.css"
    html = render_html(view, css_path)

    if args.html:
        Path(args.html).write_text(html, encoding="utf-8")
        print(f"HTML: {args.html}")
    else:
        screenshot(html, args.output)
        print(f"签文: {args.output}")


if __name__ == "__main__":
    main()
