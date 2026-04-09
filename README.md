# LangGraph 内容生成 + RAG 知识库问答（示例工程）

本项目是一个基于 **Python + LangChain + LangGraph** 的示例工程，包含两条主线：

1. **内容生成流程**：Research（研究摘要）→ Writer（初稿）→ Editor（润色），通过 LangGraph 编排执行。  
2. **企业知识库问答（RAG）**：文档入库 → 混合检索（向量 + BM25）→ 可选 LLM 重排序（rerank）→ 基于引用生成回答，并支持查询改写、多查询扩展、元数据过滤与会话记忆。

---

## 目录结构（概要）

```text
pro/
├── README.md                 # 本说明
├── requirements.txt          # Python 依赖
├── .env.example              # 环境变量模板（复制为 .env）
├── data/
│   ├── docs/                 # 示例知识库文档（Markdown）
│   └── kb/                   # 向量索引落盘目录（入库后生成）
└── src/
    ├── main.py               # 内容生成入口
    ├── config.py             # 配置（从项目根 .env 加载）
    ├── llm_client.py         # LLM 统一封装（OpenAI / Deepseek 兼容）
    ├── http_utils.py         # HTTP 代理 URL 规范化（供 LLM/Embedding 复用）
    ├── prompts.py            # Research / Writer / Editor 提示词
    ├── agent_nodes.py        # 三个业务节点（纯函数）
    ├── state.py              # 内容生成用 AgentState（TypedDict）
    ├── graph_builder.py      # 内容生成 LangGraph 装配
    └── rag/                  # RAG 子系统
        ├── main.py           # 知识库问答 CLI
        ├── ingest.py         # 文档入库 CLI
        ├── state.py          # RagState
        ├── prompts.py        # RAG / rerank / 查询改写提示词
        ├── embeddings.py     # OpenAI 兼容 Embedding 客户端构建
        ├── vector_store.py   # 本地向量库 + BM25（MVP）
        ├── nodes.py          # rewrite_query / retrieve / rerank / answer
        └── graph_builder.py  # RAG LangGraph 装配（含 MemorySaver）
```

---

## 环境准备

1. **Python**：建议 3.10+。  
2. **安装依赖**（在项目根目录执行）：

```bash
pip install -r requirements.txt
```

3. **配置环境变量**：复制 `.env.example` 为 `.env`，按需填写：

| 变量 | 说明 |
|------|------|
| `PROVIDER` | `openai` 或 `deepseek` |
| `OPENAI_API_KEY` | OpenAI 或兼容服务的 Key |
| `OPENAI_BASE_URL` | 第三方/自建 OpenAI 兼容 API 根地址（通常含 `/v1`）；**不要**填进 `OPENAI_HTTP_PROXY` |
| `OPENAI_HTTP_PROXY` | 本机 HTTP 代理（如 `http://127.0.0.1:7890`）；不需要可留空 |
| `MODEL_NAME` | 对话模型名 |
| `KB_DATA_DIR` | RAG 索引目录，默认 `data/kb` |
| `OPENAI_EMBEDDING_MODEL` | 向量模型名，默认 `text-embedding-3-small` |
| `EMBEDDING_OPENAI_API_KEY` / `EMBEDDING_OPENAI_BASE_URL` | 可选；不填则与 `OPENAI_*` 共用 |

`.env` 始终从**项目根目录**加载（见 `src/config.py`），避免从其他工作目录启动时读不到配置。

---

## 核心模块与类说明

### 通用

- **`src/config.py`**  
  - `Settings` / `get_settings()`：读取环境变量，提供 provider、模型、Key、代理、OpenAI Base URL 等。

- **`src/llm_client.py` — `LLMClient`**  
  - 统一 `invoke(LLMInput)`；内部使用 LangChain `ChatOpenAI`。  
  - `PROVIDER=openai`：支持 `OPENAI_BASE_URL` 与 `OPENAI_HTTP_PROXY`（本机代理）。  
  - `PROVIDER=deepseek`：使用 `DEEPSEEK_API_KEY` + `DEEPSEEK_BASE_URL`。

- **`src/http_utils.py`**  
  - `normalize_http_proxy_url()`：将误写的 `https://127.0.0.1:...` 规范为 `http://...`，减少 CONNECT 失败。

### 内容生成（Research → Writer → Editor）

- **`src/state.py` — `AgentState`**  
  - 图中共享字段：`topic`、`research_summary`、`draft`、`final_text`。

- **`src/agent_nodes.py`**  
  - `research_node` / `writer_node` / `editor_node`：拼装提示词并调用 `LLMClient`。

- **`src/graph_builder.py` — `build_content_graph(llm)`**  
  - `StateGraph`：`START → research → writer → editor → END`；`compile()` 返回可 `invoke` 的图。

- **`src/main.py`**  
  - 入口：`python -m src.main --topic "..."`；支持从项目根以模块方式运行（也支持直接运行 `src/main.py` 时自动补全 `sys.path`）。

### RAG 知识库

- **`src/rag/state.py` — `RagState`**  
  - 包含：`question`、`history`（会话记忆）、`source_contains`（按 source 子串过滤）、`rewrite_enabled` / `multi_query_enabled` / `retrieval_queries`、`rerank_enabled` / `rerank_keep`、`candidates`、`retrieved_context`、`reranked_context`、`citations`、`answer`。

- **`src/rag/vector_store.py` — `SimpleVectorStore`**  
  - 持久化：`data/kb/chunks.jsonl` + `embeddings.npy`。  
  - `similarity_search()`：向量检索；**可选** `source_contains` 元数据过滤。  
  - `bm25_search()`：BM25 关键词检索（依赖 `rank-bm25`）。

- **`src/rag/embeddings.py` — `build_openai_embeddings()`**  
  - 构建 `OpenAIEmbeddings`，可与 Chat 共用 Key/Base/代理，或通过 `EMBEDDING_OPENAI_*` 单独指定。

- **`src/rag/nodes.py`**  
  - `rewrite_query_node`：`--rewrite` 单条改写、`--multi-query` 多条 query。  
  - `retrieve_node`：对每个检索 query 做「向量 + BM25」，多路合并去重。  
  - `rerank_node`：可选 LLM 从候选里挑选片段 id，生成 `reranked_context`。  
  - `answer_node`：基于 `reranked_context`（或回退 `retrieved_context`）与 `history` 生成回答。

- **`src/rag/graph_builder.py` — `build_rag_graph(...)`**  
  - 流程：`START → rewrite_query → retrieve → rerank → generate_answer → END`；默认带 `MemorySaver` checkpointer，用 `thread_id` 区分会话。

- **`src/rag/ingest.py`**  
  - 扫描目录下 `.md/.txt`，切块后写入 `SimpleVectorStore`。

- **`src/rag/main.py`**  
  - 知识库问答 CLI：`python -m src.rag.main`，见下文参数表。

---

## 使用方法

### 1. 内容生成（Research / Writer / Editor）

在项目根目录：

```bash
python -m src.main --topic "你的主题"
```

### 2. RAG：入库

首次或更新文档后建议全量重建索引（会清空旧索引）：

```bash
python -m src.rag.ingest --path data/docs --clear
```

仅追加、不清空：去掉 `--clear`。

### 3. RAG：问答

```bash
python -m src.rag.main -q "你的问题"
```

**常用参数**：

| 参数 | 含义 |
|------|------|
| `-q` / `--question` | 用户问题（必填） |
| `--top-k` | 每个检索 query 取 TopK 片段（向量与 BM25 各取 k，再合并） |
| `--thread-id` | 会话 ID，相同 ID 共享 `history`（多轮追问） |
| `--source-contains` | 只检索 `metadata["source"]` 含该子串的片段（如 `hr/`、`sample.md`） |
| `--rewrite` | 查询改写（与 `--multi-query` 互斥） |
| `--multi-query` | 多查询扩展（与 `--rewrite` 互斥） |
| `--multi-query-n` | 多查询条数，2～6，默认 3 |
| `--rerank` | LLM 对候选片段重排序 |
| `--rerank-keep` | rerank 后保留条数 |

---

## 示例数据与测试用例

示例文档位于 `data/docs/`，包含：

- `sample.md`：基础休假示例  
- `hr/leave_policy.md`、`hr/recruitment.md`：人事制度与招聘  
- `it/security_access.md`：VPN、密码、权限  
- `finance/expense_reimburse.md`：报销与差旅  
- `legal/data_compliance.md`：数据合规说明  

入库后建议按下面顺序做**回归**（均在项目根执行）。

### 1. 基线：直接问（默认混合检索）

```bash
python -m src.rag.main -q "年假至少多少天？"
python -m src.rag.main -q "报销要在多少天内提交？"
python -m src.rag.main -q "VPN 账号丢了怎么办？"
```

**预期**：回答与文档内容一致；`--- 引用 ---` 中出现合理 `id` / `source`。

### 2. 元数据过滤 `--source-contains`

只搜 HR 目录：

```bash
python -m src.rag.main -q "试用期" --source-contains "hr/"
```

只搜某一篇文件名：

```bash
python -m src.rag.main -q "密码长度" --source-contains "security_access"
```

**预期**：引用来源应落在对应路径/文档范围内。

### 3. 查询改写 `--rewrite`

```bash
python -m src.rag.main -q "报销拖了很久还能报吗？" --rewrite
```

**预期**：终端会打印 `--- 检索 query ---`（改写后的检索句）；回答更贴近「60 个自然日内」等表述（具体以模型为准）。

### 4. 多查询 `--multi-query`

```bash
python -m src.rag.main -q "年假和事假有什么区别？" --multi-query --multi-query-n 3
```

**预期**：`--- 检索 query ---` 下出现 3 条不同角度的检索句。

### 5. 重排序 `--rerank`

```bash
python -m src.rag.main -q "公司网络怎么连？" --top-k 6 --rerank --rerank-keep 3
```

**预期**：`--- 引用 ---` 里片段更聚焦；会多一次 LLM 调用（rerank）。

### 6. 会话记忆 `--thread-id`

```bash
python -m src.rag.main --thread-id demo -q "年假至少几天？"
python -m src.rag.main --thread-id demo -q "那申请流程呢？"
```

**预期**：第二轮能承接上文指代（「那」）。

### 7. 组合场景

```bash
python -m src.rag.main --thread-id t1 --source-contains "hr/" -q "紧急事假怎么补单？" --rewrite --rerank
```

---

## 说明与排错

- **代理**：`OPENAI_HTTP_PROXY` 只填本机 HTTP 代理；API 地址填 `OPENAI_BASE_URL`，不要把 API 网址当 proxy。  
- **相对导入**：推荐 `python -m src.main` / `python -m src.rag.main`；`src/main.py` 已支持从项目根补全路径以便 IDE 直接运行。  
- **依赖版本**：见 `requirements.txt`；若 `langgraph==0.3.0` 安装失败，可改为同系列未撤包的 `0.3.x` 补丁版本。  

---

## 许可证

示例代码以 MIT 风格使用为宜；部署到生产前请补充日志、鉴权、限流、评测集与合规审计等企业级能力。
