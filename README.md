# pro（LangGraph 内容生成流水线）

本项目是一个基于 **LangGraph + LangChain** 的内容生成示例：输入一个主题（`topic`），在图中依次执行研究、写作、事实核查、润色与风格审查，并根据核查/审查结果决定是否回退重写或再次润色。

入口脚本会在控制台输出最终成文（`final_text`）。

## 流水线说明

整体顺序与分支如下：

1. **Research**：产出研究要点与结构建议（`research_summary`）。
2. **Writer**：根据研究摘要写初稿（`draft`）。
3. **Fact checker**：对照研究摘要对初稿做事实核查，模型返回 **JSON**（`status`、`issues`、`revised_text` 等），并解析写入状态。
4. **条件分支**（`after_fact_checker`）  
   - `status == "严重错误"`：**回到 Writer** 重写（打回流水线）。  
   - 其余（`"通过"` / `"需修改"`）：进入 **Editor**（使用事实核查产出的修改稿字段进行润色）。
5. **Editor**：润色后得到 `final_text`。
6. **Reviewer**：风格与合规审查，模型同样返回 **JSON**。
7. **条件分支**（`after_reviewer`）  
   - `status == "通过"`：**结束**。  
   - 否则（`"有条件通过"` / `"不通过"`）：**回到 Editor** 再次润色。

```mermaid
flowchart LR
  START --> research --> writer --> fact_checker
  fact_checker -->|严重错误| writer
  fact_checker -->|通过或需修改| editor
  editor --> reviewer
  reviewer -->|通过| END
  reviewer -->|有条件通过或不通过| editor
```

**提示词**：事实核查与终审节点在 `prompts.py` 中要求 **严格 JSON 输出**；模板里 JSON 示例的花括号在源码中使用 `{{` / `}}` 转义，以便与 Python `str.format()` 的 `{topic}` 等占位符共存，格式化后展示给模型的仍是单层 `{` `}`。

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

### 调试日志

增加 `--debug` 可将日志级别设为 `DEBUG`（默认 `INFO`）：

```bash
python -m src.main --topic "你的主题" --debug
```

运行成功后，终端会打印 **`final_text`**（终审通过后的文本）。

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

### 4) 事实核查或审查阶段 JSON 解析失败

这两个节点要求模型只输出可解析的 JSON。若模型包了 Markdown 代码块，代码会尝试剥掉常见 `` ```json `` 外壳；若仍失败，请检查模型是否遵守格式，或适当收紧 `prompts.py` 中的输出约束。

## 项目结构

- `src/main.py`：命令行入口；参数 `--topic`、`--debug`；调用编译后的图并打印 `final_text`
- `src/graph_builder.py`：构建带条件边的 LangGraph（research → writer → fact_checker → editor → reviewer 及回退边）
- `src/agent_nodes.py`：各节点实现；事实核查与审查节点解析 LLM 返回的 JSON
- `src/state.py`：`AgentState`（含研究摘要、初稿、终稿及核查/审查相关字段）
- `src/prompts.py`：研究 / 写作 / 事实核查 / 编辑 / 审查五段提示词
- `src/llm_client.py`：统一封装 LLM 调用（OpenAI / DeepSeek）及结构化输出用的类型
- `src/logger.py`：节点日志装饰器（若启用）
- `src/config.py`：加载 `.env` 并提供运行配置
