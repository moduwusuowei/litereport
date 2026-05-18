# LiteReport

Lightweight test report visualization tool. **Zero JDK**, single HTML file, offline ready.

An alternative to Allure for teams that want beautiful test reports without Java dependencies.

# En

## Features

- **Self-contained HTML** — Single file, no server needed, works offline
- **Multiple input formats** — Native JSON, JUnit XML, or pytest plugin
- **Dark / Light themes** — Runtime toggle, remembers preference
- **Bilingual** — English and Chinese (zh/en)
- **History tracking** — Browse previous test runs from within the report
- **Expandable suites** — Click any suite row to see individual test cases
- **Search & filter** — Full-text search across test names and descriptions
- **Duration analysis** — Top slowest tests with charts
- **YAML config** — Customize title, theme, language, output path
- **pytest plugin** — `pytest --litereport` generates reports automatically
- **Web UI screenshots** — Capture step-by-step screenshots in web tests, embedded as base64 in reports
- **Screenshot tree view** — Collapsible tree structure showing each step with labeled screenshots

## Installation

```bash
pip install litereport
```

For pytest plugin support:

```bash
pip install litereport[pytest]
```

## Quick Start

### From JSON data

```bash
litereport generate report_data.json
```

### From JUnit XML

```bash
litereport generate junit-results.xml
```

### With pytest

```bash
pytest --litereport
```

The report is generated at `./reports/report.html` by default.

## CLI Reference

```
litereport generate <SOURCE> [OPTIONS]

Options:
  -o, --output TEXT        Output HTML path
  -c, --config TEXT        Config file path
  --format [json|junit]    Force input format (auto-detected by default)
  --with-history           Include history navigation in report

litereport init            Create a litereport.yaml config file
litereport history list    List historical reports
litereport history clean   Remove old history (--keep N)
```

### Examples

```bash
# Generate with custom output path
litereport generate results.json -o ./docs/test-report.html

# Use a config file
litereport generate results.xml -c litereport.yaml

# Generate with history navigation
litereport generate results.json --with-history

# Initialize config
litereport init
```

## Configuration

Create a `litereport.yaml` in your project root (or run `litereport init`):

```yaml
report:
  title: "My Test Report"
  # logo: "./assets/logo.png"   # Optional, base64-embedded into HTML
  theme: "light"                 # light | dark
  lang: "en"                     # en | zh

history:
  enabled: true
  max_entries: 30

output:
  dir: "./reports"
  filename: "report.html"

environment:
  project: "MyProject"
  team: "QA"
```

### Config priority

1. CLI arguments (highest)
2. `litereport.yaml` (project root)
3. `~/.litereport/config.yaml` (global)
4. Built-in defaults (lowest)

## pytest Plugin

Enable with the `--litereport` flag:

```bash
pytest --litereport
pytest --litereport --litereport-config=litereport.yaml
pytest --litereport --litereport-title="Nightly Build"
```

The plugin automatically:
- Collects test results, docstrings, and markers
- Generates the HTML report on session finish
- Saves history snapshots for navigation

## JSON Format

LiteReport uses a simple JSON schema:

```json
{
  "title": "My Test Report",
  "timestamp": "2026-05-13T10:00:00",
  "duration": 12.5,
  "environment": {
    "python": "3.11",
    "platform": "Linux"
  },
  "results": [
    {
      "name": "test_login",
      "nodeid": "tests/test_auth.py::test_login",
      "suite": "test_auth",
      "outcome": "passed",
      "duration": 1.2,
      "description": "Verify user login",
      "markers": ["smoke"],
      "error_message": "",
      "error_traceback": "",
      "stdout": "",
      "properties": {}
    }
  ]
}
```

### Supported outcome values

`passed` | `failed` | `skipped` | `error` | `xfailed` | `xpassed`

## Python API

```python
from litereport import ReportData, TestResult, ReportGenerator, LiteReportConfig

# Build data
data = ReportData(
    title="API Test Report",
    timestamp="2026-05-13 10:00:00",
    duration=25.0,
    environment={"python": "3.11", "os": "Linux"},
    results=[
        TestResult(name="test_get_users", suite="test_api", outcome="passed", duration=0.5),
        TestResult(name="test_create_user", suite="test_api", outcome="failed", duration=1.2,
                   error_message="404 Not Found"),
    ],
)

# Generate
config = LiteReportConfig(theme="dark", lang="zh")
gen = ReportGenerator(config)
gen.generate(data, "reports/report.html")
```

## Web UI Testing with Screenshots

LiteReport supports capturing step-by-step screenshots in web UI tests (e.g. with Playwright) and embedding them directly into the HTML report.

### Setup

```bash
pip install playwright pytest litereport
playwright install chromium
```

### Screenshot API

In your `conftest.py`, define a `screenshot()` helper:

```python
import base64

def screenshot(page, request, label=""):
    """Capture a step screenshot and attach to test report."""
    b64 = base64.b64encode(page.screenshot(full_page=True)).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64}"
    request.node.user_properties.append(("screenshot", {"label": label, "data": data_uri}))
```

### Usage in Tests

```python
from conftest import screenshot

class TestLoginPage:
    def test_login_flow(self, page, base_url, request):
        """Complete login flow with step screenshots"""
        page.goto(f"{base_url}/login")
        screenshot(page, request, "1. Open login page")

        page.fill("input[name='username']", "admin")
        page.fill("input[type='password']", "123456")
        screenshot(page, request, "2. Fill credentials")

        page.click("button[type='submit']")
        page.wait_for_timeout(1000)
        screenshot(page, request, "3. After submit")
```

### Auto-screenshot on Failure

Add to `conftest.py` for automatic failure screenshots:

```python
import pytest

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

def pytest_runtest_teardown(item, nextitem):
    rep = getattr(item, "rep_call", None)
    if rep is None or not rep.failed:
        return
    page = item.funcargs.get("page")
    if page is None or page.is_closed():
        return
    try:
        b64 = base64.b64encode(page.screenshot(full_page=True)).decode("utf-8")
        data_uri = f"data:image/png;base64,{b64}"
        item.user_properties.append(("screenshot", {"label": "[Auto] Failure", "data": data_uri}))
    except Exception:
        pass
```

### Report Display

Screenshots appear in the report as a collapsible tree:

```
📸 Screenshots (3)
├─ ▶ 📷 1. Open login page       ← click to expand
├─ ▶ 📷 2. Fill credentials      ← each step collapsed by default
└─ ▶ ⚠️ [Auto] Failure           ← auto-failure marked in yellow
```

- **All Tests tab**: Click any row with screenshots to expand the step tree
- **Failures tab**: Screenshot tree shown below error traceback
- **Modal viewer**: Click any thumbnail for full-size view with arrow-key navigation

### Data Format

Screenshots are stored in `TestResult.properties.screenshots` as a list:

```json
{
  "properties": {
    "screenshots": [
      {"label": "1. Open login page", "data": "data:image/png;base64,..."},
      {"label": "2. Fill credentials", "data": "data:image/png;base64,..."},
      {"label": "[Auto] Failure", "data": "data:image/png;base64,..."}
    ]
  }
}
```

## Project Structure

```
src/litereport/
├── models.py           # TestResult, ReportData
├── config.py           # YAML config loading
├── generator.py        # Jinja2 HTML renderer
├── history.py          # History management
├── cli.py              # Click CLI
├── adapters/           # JSON + JUnit XML parsers
├── pytest_plugin/      # pytest integration
└── templates/          # Jinja2 templates
```

## Development

```bash
git clone <repo-url>
cd litereport
pip install -e ".[dev]"
pytest
```

# 中文

项目中 litereport 的实际实现，使用方式如下：

## 安装

```bash
# 方式一：从 PyPI（如果已发布）
pip install litereport[pytest]

# 方式二：本地开发安装（像本项目这样）
pip install -e ../litereport[pytest]
```

`[pytest]` 会额外安装 pytest 依赖，并注册 `litereport` 这个 pytest 插件。

## 基本使用

```bash
# 最简方式 — 加 --litereport 即可
pytest --litereport

# 指定报告标题
pytest --litereport --litereport-title="我的测试报告"

# 指定配置文件
pytest --litereport --litereport-config=litereport.yaml
```

不加 `--litereport` 时插件不激活，零开销。

## 配置文件（可选）

在项目根目录创建 `litereport.yaml`：

```yaml
report:
  title: "API 测试报告"
  theme: "light"        # light | dark
  lang: "zh"            # zh | en

history:
  enabled: true
  max_entries: 30

output:
  dir: "./reports"
  filename: "report.html"

environment:
  project: "我的项目"
  team: "QA"
```

没有配置文件也能运行，全部使用内置默认值。

## 产出文件

运行后在 `./reports/` 目录（默认）生成：

| 文件 | 说明 |
|------|------|
| `report.html` | 自包含 HTML 报告，直接浏览器打开 |
| `report_data.json` | 测试数据 JSON，可供二次处理 |
| `history/` | 历史报告快照（如果 history.enabled=true） |

## 工作原理

litereport 通过 `pyproject.toml` 中的 `pytest11` entry point 注册为 pytest 插件：

```toml
# litereport/pyproject.toml
[project.entry-points.pytest11]
litereport = "litereport.pytest_plugin"
```

`pip install` 后 pytest 自动发现插件。`--litereport` 开关控制是否激活（`plugin.py:36`）：

```python
def pytest_configure(config):
    if config.getoption("--litereport", default=False):
        plugin = LiteReportPlugin(...)
        config.pluginmanager.register(plugin, "litereport_plugin")
```

激活后，插件通过 pytest hooks 收集每条测试结果，session 结束时自动生成报告。

## 本项目的实际例子

```bash
cd api-test
venv\Scripts\activate
pytest --litereport --litereport-title="基金监控系统 API 测试报告" -v
# 报告输出到 reports/report.html
```

## Web UI 测试与截图

LiteReport 支持在 Web UI 测试中（如使用 Playwright）逐步截图，并将截图以 base64 内嵌到 HTML 报告中，报告仍然是单文件自包含可离线查看。

### 安装依赖

```bash
pip install playwright pytest litereport
playwright install chromium
```

### 截图 API

在 `conftest.py` 中定义 `screenshot()` 函数：

```python
import base64

def screenshot(page, request, label=""):
    """捕获一步截图并附加到测试报告"""
    b64 = base64.b64encode(page.screenshot(full_page=True)).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64}"
    request.node.user_properties.append(("screenshot", {"label": label, "data": data_uri}))
```

### 在测试中使用

```python
from conftest import screenshot

class TestLoginPage:
    def test_login_flow(self, page, base_url, request):
        """完整登录流程多步骤截图"""
        page.goto(f"{base_url}/login")
        screenshot(page, request, "1. 打开登录页")

        page.fill("input[name='username']", "admin")
        page.fill("input[type='password']", "123456")
        screenshot(page, request, "2. 填写用户名密码")

        page.click("button[type='submit']")
        page.wait_for_timeout(1000)
        screenshot(page, request, "3. 点击登录按钮")
```

### 失败自动截图

在 `conftest.py` 中添加 hook，测试失败时自动截图：

```python
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

def pytest_runtest_teardown(item, nextitem):
    rep = getattr(item, "rep_call", None)
    if rep is None or not rep.failed:
        return
    page = item.funcargs.get("page")
    if page is None or page.is_closed():
        return
    try:
        b64 = base64.b64encode(page.screenshot(full_page=True)).decode("utf-8")
        data_uri = f"data:image/png;base64,{b64}"
        item.user_properties.append(("screenshot", {"label": "[Auto] Failure", "data": data_uri}))
    except Exception:
        pass
```

### 报告展示效果

截图在报告中以树状折叠结构展示：

```
📸 截图 (3)
├─ ▶ 📷 1. 打开登录页          ← 点击展开查看截图
├─ ▶ 📷 2. 填写用户名密码      ← 默认折叠
└─ ▶ ⚠️ [Auto] Failure         ← 自动失败截图黄色标记
```

- **全部用例标签页**：点击有截图的行展开步骤树
- **失败详情标签页**：错误 traceback 下方显示截图树
- **模态框大图**：点击缩略图弹出大图，支持左右箭头翻页
- **自动失败截图**：`[Auto]` 前缀 + 警告图标 + 黄色标记，一眼区分截图原因

### 运行方式

```bash
cd web-test
pip install -r requirements.txt
playwright install chromium
pytest --litereport
# 报告输出到 reports/report.html
```


## License

MIT
