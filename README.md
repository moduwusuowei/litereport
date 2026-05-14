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



## License

MIT
