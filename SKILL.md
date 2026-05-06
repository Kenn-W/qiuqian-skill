---
name: qiuqian
description: 赛博抽签 — 六爻铜钱起卦，装卦断卦，五维运势评分与建议
license: MIT
metadata:
  category: entertainment
  tags: [六爻, 铜钱卦, 周易, 占卜, fortune-telling, i-ching]
---

# 求签 · 六爻赛博抽签

模拟三钱摇卦六次，生成六爻卦象，完成装卦断卦，输出五维运势评分与建议。

## 环境依赖

首次部署到 Linux 需安装：

```bash
# Python 包
pip install pillow jinja2 playwright

# Chromium (Playwright 截图用)
python -m playwright install chromium

# 中文字体 (推荐 Noto CJK，避免 fallback)
# Debian/Ubuntu
sudo apt install fonts-noto-cjk
# CentOS/Rocky
sudo dnf install google-noto-cjk-fonts
# Arch
sudo pacman -S noto-fonts-cjk
```

macOS 开箱即用（系统自带 PingFang / Songti / Heiti）。

## 数据文件

| 文件 | 内容 |
|:--|:--|
| `data/hexagrams-1-64.json` | 64卦卦辞 + 386爻爻辞 (ctext.org) |
| `data/zhuang-gua-rules.json` | 八宫卦序、纳甲、六亲、六兽规则 |
| `data/index-64-full.json` | 64卦索引 (id/卦符/卦名/上下卦) |
| `engine.py` | 起卦+装卦+评分引擎 |
| `render_qian.py` | 签文图片渲染器 (PIL 方案，纯 Python) |
| `render_qian_html.py` | 签文图片渲染器 (HTML/CSS + Playwright，推荐) |
| `templates/qianwen.html` | Jinja2 模板 |
| `static/qianwen.css` | 签文样式 |

## 执行流程

### 步骤 1：运行引擎

```bash
python3 engine.py
```

引擎输出 JSON 到 stdout，包含本卦/变卦/互卦、装卦详情、动爻爻辞、五维评分、分析提示。

### 步骤 2：生成签文图片

**推荐 (HTML/CSS + Playwright)：**

```bash
python3 engine.py | python3 render_qian_html.py -o /tmp/qianwen.png
```

跨平台字体、CSS 手绘六爻、自然间距。需 `pip install jinja2 playwright && python -m playwright install chromium`。

**备选 (PIL 纯 Python，无外部依赖)：**

```bash
python3 engine.py | python3 render_qian.py -o /tmp/qianwen.png
```

### 步骤 3：解析引擎输出

从 JSON 提取以下字段用于格式化：

- `date` / `sexagenary_day` — 日期和日柱
- `ben` / `bian` / `hu` — 本卦/变卦/互卦 (含 symbol, name, id)
- `zhuang.palace` / `palace_wuxing` / `gua_type` — 宫位/五行/卦型
- `zhuang.lines[]` — 六爻详情 (pos_name, yang, moving, branch, wuxing, liuqin, shiying, liushou)
- `moving_texts[]` — 动爻爻辞 (pos, text)
- `ben_data.judgment` — 本卦卦辞
- `scores` — 五维评分 dict (dim→[score, note])
- `analysis_hints[]` — 断卦提示

### 步骤 4：格式化文本输出

先发送签文图片，然后按以下模板生成 markdown 文本。一条消息输出。**必须严格按此模板格式**。

---

## 输出模板

```
🔮 今日一卦
`{date}` `{sexagenary_day}日`

　　本卦　　　　变卦　　　　互卦
　**{ben.symbol}**　→　**{bian.symbol}**　　　**{hu.symbol}**
　**{ben.name}**　　　**{bian.name}**　　　**{hu.name}**
　`{palace}·{gua_type}`

---

**📖 卦辞**

> {ben_data.judgment}
> 
> *{一句白话解读，≤20字}*

---

**⚡ 动爻**

若无动爻（静卦），写：
> 本卦无动爻，以卦辞为断。{一句静卦解读}

若有动爻，每条格式：
> **{pos}**｜{text}
> *{一句白话解读，≤20字}*

---

**📊 装卦**

```
爻位  阴阳  地支  五行  六亲  世应  六兽
━━━━━━━━━━━━━━━━━━━━━━━━
上爻   {⚊/⚋}{⊙}  {branch}   {wx}   {liuqin}   {世/应/空}   {liushou}
五爻   ...
四爻   ...
三爻   ...
二爻   ...
初爻   ...
```
> ⊙ = 动爻　世 = 自己　应 = 对方/事体

阳爻用 `⚊`，阴爻用 `⚋`。动爻在符号后加 `⊙`。

---

**🔮 五维运势**

| | 维度 | 评分 | 简评 |
|:--|:--|:--|:--|
| {色} | 事业 | {score} | {note} |
| {色} | 财运 | {score} | {note} |
| {色} | 感情 | {score} | {note} |
| {色} | 健康 | {score} | {note} |
| {色} | 人际 | {score} | {note} |

> 🟢 吉 (≥70)　🟡 平 (50–69)　🔴 慎 (<50)

颜色规则：score ≥ 70 → 🟢，50–69 → 🟡，<50 → 🔴。

---

**📝 结语**

{2-3句总结，结合卦辞和世应动爻。点明今日关键注意事项。语气：客观、有帮助性、不煽动。}

**💡 建议**
- ✅ 宜：{2-3项}
- ❌ 忌：{2-3项}
- 🎨 幸运色：{根据宫位五行：金=白, 木=绿, 水=黑/蓝, 火=红, 土=黄}
- 🧭 幸运方位：{根据宫位八卦方位}
```

---

## 格式规则

### 阴阳爻符号
- `⚊` (U+268A) = 阳爻
- `⚋` (U+268B) = 阴爻
- 动爻标记 `⊙` (U+2299) 跟在爻符后面，如 `⚊⊙`

### 五维评分

引擎已计算评分和简评，直接使用。颜色圆点按分数区间选择。

如果引擎返回的简评过长（>20字），适当精简。

### 卦辞白话解读

用一句话（≤20字）以日常语言解释卦辞。参考：
- 乾：自强不息，大有作为之日
- 坤：厚德载物，以柔克刚
- 随：顺势而行，跟从正道
- 賁：外饰内质，宜文宜朴
- etc.

根据卦辞原意，结合日柱和动爻，给出一句贴合当下的解读。

### 动爻白话解读

每句≤20字，点出该爻对今日的实际影响。参考引擎的 `analysis_hints`。

### 结语

综合以下要素写 2-3 句结语：
1. 卦辞总体吉凶
2. 世应关系
3. 动爻关键提示
4. 五维评分中的高点和低点
5. 给出一个关键行动建议

语气：客观、有帮助性、不制造焦虑。

### 建议

- 宜：基于高评分维度和吉祥爻辞
- 忌：基于低评分维度和凶险爻辞
- 幸运色：宫位五行 → 金=白/银, 木=绿/青, 水=黑/蓝, 火=红/紫, 土=黄/棕
- 幸运方位：宫位八卦 → 乾=西北, 坤=西南, 震=东, 巽=东南, 坎=北, 离=南, 艮=东北, 兑=西

### 长度控制

- 卦辞白话 ≤20 字
- 每条动爻白话 ≤20 字
- 五维评分简评每项 ≤18 字
- 结语 ≤80 字
- 最终总消息控制在 600 字以内（不含装卦 code block）

---

## 特殊情形

### 静卦（无动爻）
- 不展示变卦、互卦
- 以本卦卦辞为主断
- 动爻段改为 "本卦无动爻，以卦辞为断"
- 评分趋保守（加减幅度减半）

### 六爻全动
- 以变卦卦辞为主断
- 附本卦动爻爻辞供参考

### 用九/用六（乾卦六爻全阳动、坤卦六爻全阴动）
- 乾卦全动 → 引用「用九：见群龙无首，吉」
- 坤卦全动 → 引用「用六：利永贞」

### 艮宫/坤宫卦
- 艮宫属土 → 幸运色黄/棕，方位东北
- 坤宫属土 → 幸运色黄/棕，方位西南
- 注意区分艮宫≠坤宫

### 评分边界
- 评分为引擎计算值，不要手动修改
- 如果某项 score > 90，颜色仍为 🟢
- 如果某项 score < 30，颜色为 🔴，结语中委婉提醒

---

## 示例

用户输入：`/openclaw`

执行：
```bash
python3 engine.py
```

读取输出 JSON，按模板格式化。

参考文件：
- 卦辞爻辞原文：`data/hexagrams-1-64.json`
- 装卦规则：`data/zhuang-gua-rules.json`
