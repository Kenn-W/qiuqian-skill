# qiuqian

一个可公开分发的 Claude Code skill：模拟六爻铜钱起卦，完成装卦断卦，并输出带五维评分与建议的签文内容。

## 仓库内容

- `SKILL.md`：Claude skill 定义与输出规范
- `engine.py`：起卦、识卦、装卦、评分引擎
- `render_qian_html.py`：推荐的 HTML/CSS + Playwright 签文渲染器
- `render_qian.py`：PIL 纯 Python 渲染备选方案
- `data/`：64 卦、装卦规则、索引数据
- `templates/` + `static/`：HTML 模板与样式

## 安装到 Claude Code

如果你想把它作为本地 skill 使用，直接把本仓库放到 Claude 的 skills 目录下：

```bash
git clone https://github.com/<your-name>/qiuqian.git ~/.claude/skills/qiuqian
```

或者已经在本地有仓库时：

```bash
mkdir -p ~/.claude/skills
ln -s /absolute/path/to/qiuqian ~/.claude/skills/qiuqian
```

## 运行依赖

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

Linux 建议额外安装 `Noto CJK` 中文字体，避免截图渲染时回退乱码。

## 快速测试

只跑引擎：

```bash
python3 engine.py
```

生成 PNG 签文图（推荐方案）：

```bash
python3 engine.py | python3 render_qian_html.py -o /tmp/qianwen.png
```

使用内置测试数据：

```bash
python3 render_qian_html.py --test -o /tmp/qianwen.png
```

如果 Playwright 不方便安装，可退回 PIL 版本：

```bash
python3 engine.py | python3 render_qian.py -o /tmp/qianwen.png
```

## 说明

- skill 元数据声明为 `MIT`，本仓库附带 `LICENSE`
- 数据与文案主题涉及周易占卜，适合娱乐化或文化体验场景
- `render_qian.py` 在 macOS 字体下效果最好；跨平台优先用 `render_qian_html.py`
