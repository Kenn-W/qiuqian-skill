# 签文图片渲染器 (HTML/CSS + Playwright)

用 HTML/CSS 排版 + Chromium 截图替代 PIL 像素绘制，生成更美观的签文图。

## 对比旧 PIL 方案

| 维度 | PIL (`render_qian.py`) | HTML/CSS (`render_qian_html.py`) |
|------|----------------------|----------------------------------|
| 字体 | 写死 macOS 路径，Linux 易 fallback | 系统字体栈，跨平台一致 |
| 卦象 | Unicode `䷀` 字符，需特殊字体 | CSS div 手绘六爻，无字体依赖 |
| 排版 | 手算像素坐标，易压线 | CSS 流式布局，间距自然 |
| 维护 | 增删模块需重算全部高度 | 改 CSS 即可，高度自适应 |

## 依赖安装

```bash
pip install jinja2 playwright
python -m playwright install chromium
```

Linux 字体建议：

```bash
# Debian/Ubuntu
sudo apt install fonts-noto-cjk

# CentOS/Rocky
sudo dnf install google-noto-cjk-fonts

# Arch
sudo pacman -S noto-fonts-cjk
```

## 用法

```bash
# 测试 (内置数据)
python3 render_qian_html.py --test -o qianwen.png

# 从 engine 流水线
python3 engine.py | python3 render_qian_html.py -o qianwen.png

# 从 JSON 文件
python3 render_qian_html.py -i sample.json -o qianwen.png

# 仅输出 HTML (调试用)
python3 render_qian_html.py --test --html debug.html
```

## 文件结构

```
render_qian_html.py   # 主程序: JSON → view model → HTML → PNG
templates/qianwen.html # Jinja2 模板
static/qianwen.css     # 古风签文样式
README_render_html.md  # 本文件
```

## 回退方案

旧 PIL 渲染器 `render_qian.py` 保留可用。若 Playwright 不可用：

```bash
python3 engine.py | python3 render_qian.py -o qianwen.png
```
