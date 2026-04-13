# pro（LangGraph 内容生成流水线）

本项目是一个基于 **LangGraph + LangChain** 的内容生成示例：输入一个主题（topic），依次执行：

- **Research**：产出研究要点/结构建议
- **Writer**：根据研究摘要写初稿
- **Editor**：润色并输出最终文本

入口脚本会在控制台输出最终成文（`final_text`）。

## 安装

### 1) 准备 Python 环境

建议使用 **Python 3.10+**。

Windows 提示：

- 安装 Python 后，请确保勾选/配置了 **Add Python to PATH**，以便终端里能直接使用 `python`（或 `py`）。
- 如果你的环境里 `python` / `py` 命令不可用，可以直接使用虚拟环境里的解释器：`.venv\Scripts\python.exe`。

### 2) 创建并激活虚拟环境（推荐）

PowerShell：

```bash
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

如果你的系统没有 `py` 启动器，也可以用：

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

如果你的 PowerShell 不允许运行脚本，可改用：

```bash
.\.venv\Scripts\python.exe -m pip install -U pip
```

### 3) 安装依赖

```bash
pip install -r requirements.txt
```

## 配置（.env）

项目会**始终从项目根目录加载** `.env`（见 `src/config.py`），推荐按以下方式配置：

1. 复制示例文件：

```bash
copy .env.example .env
```

2. 编辑 `.env`，根据你使用的模型服务提供方填写。

### 使用 OpenAI（或 OpenAI 兼容服务）

至少需要：

- `OPENAI_API_KEY`
- `PROVIDER=openai`
- `MODEL_NAME`（例如 `gpt-4o-mini`）

可选：

- `OPENAI_BASE_URL`：**第三方/自建的 OpenAI 兼容 API Base**（通常带 `/v1`），例如 `https://api.openai.com/v1`
- `OPENAI_HTTP_PROXY`：**本地 HTTP 代理**（Clash/v2rayN 的 HTTP 端口），形如 `http://127.0.0.1:7890`

注意：

- `OPENAI_BASE_URL` 和 `OPENAI_HTTP_PROXY` 是两回事：前者是“请求发往哪里”，后者是“怎么走代理隧道”。
- 如果你不需要本地代理，请把 `OPENAI_HTTP_PROXY` 留空。

### 使用 DeepSeek（OpenAI 兼容方式）

需要：

- `PROVIDER=deepseek`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`（示例：`https://api.deepseek.com`）
- `MODEL_NAME`（按你的账号可用模型填写）

## 使用

### 方式 A（推荐）：模块方式启动

在项目根目录运行：

```bash
python -m src.main --topic "AI 在教育中的应用"
```

### 方式 B：直接运行脚本

```bash
python src/main.py --topic "AI 在教育中的应用"
```

运行后，终端会打印最终润色后的文章文本。

## 常见问题

### 1) 报错：`OPENAI_API_KEY is required when PROVIDER=openai`

你当前使用的是 `PROVIDER=openai`，但 `.env` 里没有设置 `OPENAI_API_KEY`。请补齐后重试。

### 2) 代理相关连接失败

如果你配置了 `OPENAI_HTTP_PROXY`：

- 确保它是本地 HTTP 代理地址（如 `http://127.0.0.1:7890`），不要填成 API 的 `base_url`
- 如果误写成 `https://127.0.0.1:xxxx`，项目会尝试自动纠正为 `http://...`，但仍建议手动改正确

### 3) 依赖安装失败

建议先升级 pip：

```bash
python -m pip install -U pip
```

然后重新安装：

```bash
pip install -r requirements.txt
```

## 项目结构

- `src/main.py`：命令行入口，接受 `--topic`
- `src/graph_builder.py`：构建 `Research -> Writer -> Editor` 的 LangGraph
- `src/llm_client.py`：统一封装 LLM 调用（OpenAI / DeepSeek）
- `src/config.py`：加载 `.env` 并提供运行配置
- `src/prompts.py`：三段提示词（研究/写作/编辑）

