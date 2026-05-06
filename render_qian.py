#!/usr/bin/env python3
"""签文图片渲染器 — 六爻求签结果生成 PNG 长条签文图。
无外部字体依赖，手绘所有装饰元素。emoji-free，纯 PIL 绘制。

Usage: python3 engine.py | python3 render_qian.py [-o qian.png]
       python3 render_qian.py --test
"""

import json
import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ═══ 画布配置 ═══
W = 640          # 图片宽度
P = 36           # 左右内边距
CW = W - 2 * P   # 内容宽度

# ═══ 颜色：暖色签文 ═══
BG     = "#FBF5E8"   # 宣纸底
CARD   = "#FFFDF5"   # 卡片白
TEXT   = "#3D2B1F"   # 正文褐
SUB    = "#7B6B5F"   # 副文灰褐
ACCENT = "#B8402C"   # 朱砂红
BORDER = "#D4C5A0"   # 框线浅金
DIV    = "#E5D8C0"   # 分隔淡金
SHADOW = "#D8CFC0"   # 卡片阴影
GRN    = "#4A8C3F"   # 绿 (吉)
YLW    = "#D4942B"   # 黄 (平)
RED_C  = "#C0392B"   # 红 (慎)
TBG    = "#EDE5D5"   # 表头底色

# ═══ 字号 ═══
SZ_TITLE   = 44
SZ_HEX     = 70
SZ_SECTION = 26
SZ_BODY    = 22
SZ_SMALL   = 18
SZ_TINY    = 15

# ═══ 字体 ═══
FONT_TITLE = "/System/Library/Fonts/Supplemental/Songti.ttc"
FONT_BODY  = "/System/Library/Fonts/STHeiti Medium.ttc"


def get_font(path, size):
    try:
        return ImageFont.truetype(path, size, index=0)
    except Exception:
        return ImageFont.load_default()


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
    if s >= 70: return GRN
    if s >= 50: return YLW
    return RED_C


def yao_sym(yang, moving):
    return ("⚊" if yang else "⚋") + ("⊙" if moving else "")


def wx_color(wx):
    return {"金":"白/银","木":"绿/青","水":"黑/蓝","火":"红/紫","土":"黄/棕"}.get(wx,"?")


def gong_dir(palace):
    return {"乾宫":"西北","坤宫":"西南","震宫":"东","巽宫":"东南",
            "坎宫":"北","离宫":"南","艮宫":"东北","兑宫":"西"}.get(palace,"中")


# ═══ Canvas ═══

class CV:
    def __init__(self, w):
        self.w = w
        self.h = 2000
        self.img = Image.new("RGBA", (w, self.h), BG)
        self.d = ImageDraw.Draw(self.img)
        self.y = 0

    def ensure(self, need):
        if self.y + need > self.h:
            new_h = self.h + max(need, 600)
            im = Image.new("RGBA", (self.w, new_h), BG)
            im.paste(self.img, (0, 0))
            self.img = im
            self.d = ImageDraw.Draw(self.img)
            self.h = new_h

    def sp(self, h):
        self.y += h

    def crop(self):
        self.img = self.img.crop((0, 0, self.w, self.y + P))
        return self.img

    # ── helpers ──

    def card(self, h, fill=CARD, shadow=True):
        self.ensure(h + 16)
        if shadow:
            self.d.rounded_rectangle((P+3, self.y+3, W-P+3, self.y+h+3), 12, fill=SHADOW)
        self.d.rounded_rectangle((P, self.y, W-P, self.y+h), 12, fill=fill, outline=BORDER, width=1)

    def section(self, title):
        self.sp(18)
        # 红色装饰短竖线
        self.d.rounded_rectangle((P+2, self.y+2, P+7, self.y+SZ_SECTION), 2, fill=ACCENT)
        f = get_font(FONT_BODY, SZ_SECTION)
        self.d.text((P+16, self.y), title, fill=TEXT, font=f)
        self.sp(SZ_SECTION + 8)

    def body_text(self, text, color=TEXT, size=SZ_BODY, max_w=None):
        if max_w is None:
            max_w = CW - 10
        font = get_font(FONT_BODY, size)
        lines = []
        for para in text.split("\n"):
            if not para:
                lines.append("")
                continue
            cur = ""
            for ch in para:
                t = cur + ch
                if font.getbbox(t)[2] > max_w:
                    lines.append(cur)
                    cur = ch
                else:
                    cur = t
            if cur:
                lines.append(cur)
        for ln in lines:
            self.ensure(size + 6)
            self.d.text((P+8, self.y), ln, fill=color, font=font)
            self.sp(size + 6)

    def divider(self):
        self.sp(10)
        my = self.y + 5
        self.d.line((P+10, my, W-P-10, my), fill=DIV, width=1)
        self.sp(16)


# ═══ Render ═══

def render(data):
    cv = CV(W)
    bz = data["zhuang"]
    is_jing = len(data["moving_positions"]) == 0
    brief = JUDGMENT_BRIEF.get(data["ben"]["name"], "顺势守正，依卦而行")

    # ── 顶栏 ──
    cv.sp(28)
    cv.d.line((P+30, cv.y, W-P-30, cv.y), fill=ACCENT, width=2)
    cv.sp(2)
    cv.d.line((P+30, cv.y, W-P-30, cv.y), fill=BORDER, width=1)
    cv.sp(16)

    tf = get_font(FONT_TITLE, SZ_TITLE)
    title = "今 日 一 卦"
    tb = tf.getbbox(title)
    cv.d.text(((W-tb[2])//2, cv.y), title, fill=ACCENT, font=tf)
    cv.sp(SZ_TITLE + 6)

    df = get_font(FONT_BODY, SZ_SMALL)
    ds = f"{data['date']}   {data['sexagenary_day']}日"
    db = df.getbbox(ds)
    cv.d.text(((W-db[2])//2, cv.y), ds, fill=SUB, font=df)
    cv.sp(SZ_SMALL + 8)

    cv.d.line((P+30, cv.y, W-P-30, cv.y), fill=BORDER, width=1)
    cv.sp(2)
    cv.d.line((P+30, cv.y, W-P-30, cv.y), fill=ACCENT, width=2)
    cv.sp(22)

    # ── 卦象卡片 ──
    ch = 138
    cv.ensure(ch + 20)
    cv.d.rounded_rectangle((P+3, cv.y+3, W-P+3, cv.y+ch+3), 14, fill=SHADOW)
    cv.d.rounded_rectangle((P, cv.y, W-P, cv.y+ch), 14, fill=CARD, outline=BORDER, width=1)

    if is_jing:
        hf = get_font(FONT_BODY, SZ_HEX)
        sym = data["ben"]["symbol"]
        sb = hf.getbbox(sym)
        cv.d.text(((W-sb[2])//2, cv.y+14), sym, fill=TEXT, font=hf)
        nf = get_font(FONT_BODY, SZ_BODY)
        name = data["ben"]["name"]
        nb = nf.getbbox(name)
        cv.d.text(((W-nb[2])//2, cv.y+14+SZ_HEX+4), name, fill=TEXT, font=nf)
        pf = get_font(FONT_BODY, SZ_TINY)
        ps = f"{bz['palace']} · {bz['gua_type']}"
        pb = pf.getbbox(ps)
        cv.d.text(((W-pb[2])//2, cv.y+14+SZ_HEX+SZ_BODY+8), ps, fill=SUB, font=pf)
    else:
        hf = get_font(FONT_BODY, SZ_HEX)
        lf = get_font(FONT_BODY, SZ_TINY)
        nf = get_font(FONT_BODY, SZ_BODY)
        cw = CW // 3
        cols = [("本卦", data["ben"]["symbol"], data["ben"]["name"]),
                ("变卦", data["bian"]["symbol"], data["bian"]["name"]),
                ("互卦", data["hu"]["symbol"], data["hu"]["name"])]
        for i, (lb, sy, nm) in enumerate(cols):
            cx = P + cw*i + cw//2
            lb_b = lf.getbbox(lb)
            cv.d.text((cx-lb_b[2]//2, cv.y+8), lb, fill=SUB, font=lf)
            sy_b = hf.getbbox(sy)
            cv.d.text((cx-sy_b[2]//2, cv.y+24), sy, fill=TEXT, font=hf)
            nm_b = nf.getbbox(nm)
            cv.d.text((cx-nm_b[2]//2, cv.y+24+SZ_HEX+2), nm, fill=TEXT, font=nf)
            if i == 0:
                af = get_font(FONT_BODY, 38)
                cv.d.text((P+cw-12, cv.y+24+SZ_HEX//3), "→", fill=ACCENT, font=af)
        pf = get_font(FONT_BODY, SZ_TINY)
        ps = f"{bz['palace']} · {bz['gua_type']}"
        pb = pf.getbbox(ps)
        cv.d.text(((W-pb[2])//2, cv.y+ch-22), ps, fill=SUB, font=pf)

    cv.sp(ch + 20)

    # ── 卦辞 ──
    cv.section("卦  辞")
    judgment = data["ben_data"]["judgment"]
    j_lines = []
    jf = get_font(FONT_BODY, SZ_BODY)
    cur = ""
    for c in judgment:
        t = cur + c
        if jf.getbbox(t)[2] > CW - 20:
            j_lines.append(cur)
            cur = c
        else:
            cur = t
    if cur:
        j_lines.append(cur)

    jh = len(j_lines)*(SZ_BODY+4) + SZ_SMALL + 24
    cv.card(jh)
    for i, ln in enumerate(j_lines):
        cv.d.text((P+12, cv.y+10+i*(SZ_BODY+4)), ln, fill=TEXT, font=jf)
    bf = get_font(FONT_BODY, SZ_SMALL)
    cv.d.text((P+16, cv.y+10+len(j_lines)*(SZ_BODY+4)+2), brief, fill=ACCENT, font=bf)
    cv.sp(jh + 16)

    # ── 动爻 ──
    if is_jing:
        cv.section("静  卦")
        cv.card(48)
        cv.d.text((P+16, cv.y+10), "本卦无动爻 · 以卦辞为断", fill=SUB, font=get_font(FONT_BODY, SZ_SMALL))
        cv.sp(48 + 16)
    else:
        cv.section("动  爻")
        for mt in data["moving_texts"]:
            cv.card(64)
            pf = get_font(FONT_BODY, SZ_SMALL)
            cv.d.text((P+16, cv.y+8), mt["pos"], fill=ACCENT, font=pf)
            txt = mt["text"]
            tbf = get_font(FONT_BODY, SZ_SMALL)
            if tbf.getbbox(txt)[2] > CW - 70:
                while tbf.getbbox(txt+"...")[2] > CW - 70 and len(txt) > 2:
                    txt = txt[:-1]
                txt += "..."
            cv.d.text((P+16, cv.y+30), txt, fill=TEXT, font=tbf)
            cv.sp(64 + 6)

    # ── 装卦表 ──
    cv.section("装  卦")

    cols = ["爻位","阴阳","地支","五行","六亲","世应","六兽"]
    cw_list = [48, 50, 48, 48, 66, 48, 72]
    tw = sum(cw_list) + 8*7 + 4
    tx = P + (CW - tw)//2
    rh = 30

    # 表头
    cv.ensure(34 + rh*6 + 30)
    cv.d.rectangle((tx, cv.y, tx+tw, cv.y+34), fill=TBG)
    thf = get_font(FONT_BODY, SZ_TINY)
    x = tx + 6
    for i, col in enumerate(cols):
        cv.d.text((x, cv.y+6), col, fill=SUB, font=thf)
        x += cw_list[i] + 8

    cv.sp(34)

    # 表行
    tdf = get_font(FONT_BODY, SZ_TINY)
    for l in reversed(bz["lines"]):
        ry = cv.y
        if l["pos"] % 2 == 1:
            cv.d.rectangle((tx, ry, tx+tw, ry+rh), fill="#FCF9F2")
        if l["moving"]:
            cv.d.rectangle((tx, ry, tx+tw, ry+rh), fill="#FDF0E0", outline="#E8C898", width=1)

        x = tx + 6
        vals = [l["pos_name"], yao_sym(l["yang"], l["moving"]),
                l["branch"], l["wuxing"], l["liuqin"],
                l["shiying"] or "", l["liushou"]]
        for i, val in enumerate(vals):
            c = ACCENT if (l["moving"] or val in ("世","应")) else TEXT
            cv.d.text((x, ry+4), val, fill=c, font=tdf)
            x += cw_list[i] + 8
        cv.sp(rh)

    # 表注
    nf = get_font(FONT_BODY, 14)
    cv.d.text((tx+4, cv.y+4), "⊙ = 动爻    世 = 自己    应 = 对方/事体", fill=SUB, font=nf)
    cv.sp(28)

    # ── 五维运势 ──
    cv.section("五维运势")

    dims = ["事业","财运","感情","健康","人际"]
    bar_h = 40
    for dim in dims:
        s, note = data["scores"][dim]
        sc = score_color(s)
        cv.ensure(bar_h + 6)

        # 颜色圆点 (手绘)
        dot_r = 10
        dot_x = P + 6 + dot_r
        dot_y = cv.y + bar_h//2
        cv.d.ellipse((dot_x-dot_r, dot_y-dot_r, dot_x+dot_r, dot_y+dot_r), fill=sc)

        # 维度名
        df_ = get_font(FONT_BODY, SZ_BODY)
        cv.d.text((P + 28, cv.y + 4), dim, fill=TEXT, font=df_)

        # 分数
        sf_ = get_font(FONT_BODY, SZ_BODY)
        cv.d.text((P + 100, cv.y + 4), str(s), fill=sc, font=sf_)

        # 进度条
        bx = P + 138
        bw = CW - 150
        cv.d.rounded_rectangle((bx, cv.y+8, bx+bw, cv.y+bar_h-8), 8, fill="#E8E0D0")
        if s > 0:
            cv.d.rounded_rectangle((bx, cv.y+8, bx+int(bw*s/100), cv.y+bar_h-8), 8, fill=sc)

        # 简评
        nf_ = get_font(FONT_BODY, SZ_SMALL)
        sn = note[:20] if len(note) > 20 else note
        cv.d.text((bx+10, cv.y+bar_h-4), sn, fill=TEXT, font=nf_)
        cv.sp(bar_h + 4)

    cv.sp(8)

    # ── 结语 ──
    cv.section("结  语")

    ben_name = data["ben"]["name"]
    judgment = data["ben_data"]["judgment"]
    best_dim = max(dims, key=lambda d: data["scores"][d][0])
    worst_dim = min(dims, key=lambda d: data["scores"][d][0])
    shi_l = next((l for l in bz["lines"] if l["shiying"]=="世"), None)

    if is_jing:
        concl = f"{ben_name}卦静而无动，今日运势平稳。卦辞点明「{judgment[:12]}」。今日{best_dim}最佳，{worst_dim}稍逊。宜守正顺势，踏实行事。"
    else:
        mp = "、".join(str(p) for p in data["moving_positions"])
        concl = f"{ben_name}卦动于{mp}。世{shi_l['liuqin']}持世于{shi_l['pos_name']}。今日{best_dim}为亮点，{worst_dim}须留意。卦曰「{judgment[:8]}」，顺势而行。"

    cf = get_font(FONT_BODY, SZ_BODY)
    cl = []
    cur = ""
    for c in concl:
        t = cur + c
        if cf.getbbox(t)[2] > CW - 20:
            cl.append(cur)
            cur = c
        else:
            cur = t
    if cur:
        cl.append(cur)

    ch2 = len(cl)*(SZ_BODY+6) + 24
    cv.card(ch2)
    for i, ln in enumerate(cl):
        cv.d.text((P+14, cv.y+12+i*(SZ_BODY+6)), ln, fill=TEXT, font=cf)
    cv.sp(ch2 + 14)

    # ── 建议 ──
    cv.section("建  议")

    lc = wx_color(bz["palace_wuxing"])
    ld = gong_dir(bz["palace"])
    al = [
        f"宜：把握{best_dim}机会，顺势而为，稳中求进",
        f"忌：忽视{worst_dim}，冲动决策，过度消耗",
        f"幸运色：{lc}      幸运方位：{ld}",
    ]
    af = get_font(FONT_BODY, SZ_SMALL)
    ah = len(al)*(SZ_SMALL+8) + 24
    cv.card(ah)
    for i, ln in enumerate(al):
        cv.d.text((P+14, cv.y+12+i*(SZ_SMALL+8)), ln, fill=TEXT, font=af)
    cv.sp(ah + 14)

    # ── 底栏 ──
    cv.sp(8)
    cv.d.line((P+30, cv.y, W-P-30, cv.y), fill=ACCENT, width=2)
    cv.sp(2)
    cv.d.line((P+30, cv.y, W-P-30, cv.y), fill=BORDER, width=1)
    cv.sp(12)
    sf = get_font(FONT_TITLE, SZ_SECTION)
    st = "签  文"
    sb = sf.getbbox(st)
    cv.d.text(((W-sb[2])//2, cv.y), st, fill=ACCENT, font=sf)
    cv.sp(SZ_SECTION + 6)
    xf = get_font(FONT_BODY, SZ_TINY)
    xt = "六爻铜钱卦 · 赛博求签"
    xb = xf.getbbox(xt)
    cv.d.text(((W-xb[2])//2, cv.y), xt, fill=SUB, font=xf)
    cv.sp(30)

    return cv.crop()


# ═══ main ═══

def main():
    import argparse
    ap = argparse.ArgumentParser(description="签文图片渲染器")
    ap.add_argument("--input","-i", help="JSON 输入 (默认 stdin)")
    ap.add_argument("--output","-o", default="qianwen.png", help="输出路径")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()

    if args.test:
        # 内置测试数据: ䷥睽→䷍大有
        data = {
            "date": str(date.today()), "sexagenary_day": "己卯",
            "day_stem":"己","day_branch":"卯",
            "lines_raw":[{"yang":True,"moving":False},{"yang":True,"moving":False},
                         {"yang":False,"moving":True},{"yang":True,"moving":False},
                         {"yang":False,"moving":False},{"yang":True,"moving":False}],
            "moving_positions":[3],
            "ben":{"id":38,"symbol":"䷥","name":"睽","pinyin":"kui","upper":"☲","lower":"☱","ctext":"kui"},
            "bian":{"id":14,"symbol":"䷍","name":"大有","pinyin":"da-you","upper":"☲","lower":"☰","ctext":"da-you"},
            "hu":{"id":63,"symbol":"䷾","name":"既濟","pinyin":"ji-ji","upper":"☵","lower":"☲","ctext":"ji-ji"},
            "zhuang":{"palace":"艮宫","palace_wuxing":"土","gua_type":"四世","shi_position":4,"ying_position":1,"day_stem":"己",
                "lines":[
                    {"pos":1,"pos_name":"初爻","yang":True,"moving":False,"branch":"巳","wuxing":"火","liuqin":"父母","shiying":"应","liushou":"螣蛇"},
                    {"pos":2,"pos_name":"二爻","yang":True,"moving":False,"branch":"卯","wuxing":"木","liuqin":"官鬼","shiying":"","liushou":"白虎"},
                    {"pos":3,"pos_name":"三爻","yang":False,"moving":True,"branch":"丑","wuxing":"土","liuqin":"兄弟","shiying":"","liushou":"玄武"},
                    {"pos":4,"pos_name":"四爻","yang":True,"moving":False,"branch":"酉","wuxing":"金","liuqin":"子孙","shiying":"世","liushou":"青龙"},
                    {"pos":5,"pos_name":"五爻","yang":False,"moving":False,"branch":"未","wuxing":"土","liuqin":"兄弟","shiying":"","liushou":"朱雀"},
                    {"pos":6,"pos_name":"上爻","yang":True,"moving":False,"branch":"巳","wuxing":"火","liuqin":"父母","shiying":"","liushou":"勾陈"},
                ]},
            "ben_data":{"id":38,"symbol":"䷥","name":"睽","judgment":"小事吉。","lines":[]},
            "bian_data":{"id":14,"symbol":"䷍","name":"大有","judgment":"元亨。","lines":[]},
            "hu_data":{"id":63,"symbol":"䷾","name":"既濟","judgment":"亨，小利貞，初吉終亂。","lines":[]},
            "moving_texts":[{"pos":"六三","text":"見輿曳，其牛掣，其人天且劓，无初有終。"}],
            "analysis_hints":["应克世：对方克我，须谨慎"],
            "scores":{"事业":[60,"官鬼在位，事业平稳"],"财运":[55,"妻财不显，今日守成为上"],
                      "感情":[55,"应克世，对方强势"],"健康":[50,"子孙护身，注意饮食"],
                      "人际":[45,"兄弟暗动，须防口舌"]},
        }
    else:
        inp = open(args.input) if args.input else sys.stdin
        data = json.load(inp)

    img = render(data)
    img.save(args.output, "PNG")
    print(f"签文: {args.output}")


if __name__ == "__main__":
    main()
