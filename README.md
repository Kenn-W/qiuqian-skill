# 求签.skill

用六爻铜钱法起卦，自动完成识卦、装卦、动爻提取、简要断卦和五维运势评分，并可渲染为签文图片。

## 它能做什么

- 🎲 随机起卦，或用固定爻值复现同一结果
- ☯️ 识别本卦、变卦、互卦
- 🧭 自动装卦：六亲、六兽、世应、宫位、五行
- 📝 输出结构化 JSON，方便接到任意 agent / workflow
- 🖼️ 生成古风签文图，适合聊天回复、卡片展示或内容实验

## 仓库结构

- `SKILL.md`：skill 说明与输出格式约束
- `engine.py`：起卦、识卦、装卦、评分引擎
- `render_qian_html.py`：推荐渲染器，HTML/CSS + Playwright
- `render_qian.py`：纯 Python / PIL 备选渲染器
- `data/`：64 卦数据、装卦规则、索引
- `templates/`、`static/`：HTML 模板与样式资源

安装

### 1. 依赖

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

Linux 建议额外安装 `Noto CJK` 中文字体，避免截图时回退乱码。

### 2. 运行

```bash
python3 engine.py
```

它会输出一段 JSON，包含：

- 日期与日柱
- 本卦 / 变卦 / 互卦
- 六爻装卦详情
- 动爻爻辞
- 分析提示
- 五维评分

### 3. 生成签文图

推荐的 HTML 渲染方案：

```bash
python3 engine.py | python3 render_qian_html.py -o /tmp/qianwen.png
```

如果 Playwright 不方便安装，可以退回 PIL 版本：

```bash
python3 engine.py | python3 render_qian.py -o /tmp/qianwen.png
```

## 运行结果示例

下面这个示例使用固定爻值，结果可复现：

```bash
python3 engine.py --lines 7,7,8,6,9,7
```

对应结果节选：

```json
{
  "date": "2026-05-06",
  "sexagenary_day": "庚辰",
  "ben": {
    "id": 61,
    "symbol": "䷼",
    "name": "中孚"
  },
  "bian": {
    "id": 38,
    "symbol": "䷥",
    "name": "睽"
  },
  "hu": {
    "id": 27,
    "symbol": "䷚",
    "name": "頤"
  },
  "moving_positions": [4, 5],
  "moving_texts": [
    {
      "pos": "六四",
      "text": "月幾望，馬匹亡，无咎。"
    },
    {
      "pos": "九五",
      "text": "有孚攣如，无咎。"
    }
  ],
  "analysis_hints": [
    "应生世：对方生我，事易成",
    "四爻动临世爻：自身变化，事在人为"
  ],
  "scores": {
    "事业": [65, "官鬼在位，事业平稳"],
    "财运": [55, "妻财不显，今日守成为上"],
    "感情": [75, "应生世，对方有意，心意相通"],
    "健康": [45, "世爻被官鬼所克，注意身体"],
    "人际": [55, "兄弟动，须防口舌竞争"]
  }
}
```

如果把这段 JSON 继续送进渲染器：

```bash
python3 engine.py --lines 7,7,8,6,9,7 | python3 render_qian_html.py -o /tmp/qianwen.png
```

你会得到一张完整签文图，适合直接发给用户。

## 接入agent

最简单的用法是直接运行脚本；如果你的 agent 平台支持目录式 skill / prompt / tool 定义，可以直接复用 `SKILL.md`。

例如，在支持本地 skills 目录的环境里：

```bash
git clone https://github.com/<your-name>/qiuqian-skill.git /path/to/skills/qiuqian
```

或者：

```bash
mkdir -p /path/to/skills
ln -s /absolute/path/to/qiuqian /path/to/skills/qiuqian
```

实际集成时，通常只需要两步：

1. 让 agent 调用 `engine.py` 生成结构化 JSON
2. 按 `SKILL.md` 的格式约束，把 JSON 转成回复文本，或调用渲染器输出图片
