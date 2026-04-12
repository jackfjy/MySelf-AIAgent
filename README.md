# LangGraph 内容生成 + RAG 知识库问答（示例工程）

基于 **Python + LangChain + LangGraph**：支持「研究 → 写作 → 编辑」内容流水线，以及「文档入库 + 混合检索 + 可选重排序」的知识库问答；提供 **FastAPI** 与可选 **Vue 3 + Vite** 前端。

## 文档导航

| 文档 | 说明 |
|------|------|
| **[用户手册.md](./用户手册.md)** | **在新电脑部署安装**、环境变量、CLI、HTTP API 一览、curl 示例、测试用例 |
| **[开发文档.md](./开发文档.md)** | 目录结构、模块职责、扩展与排错（面向开发者） |
| **[frontend/README.md](./frontend/README.md)** | 前端安装、开发、构建与生产注意事项 |

## 在新电脑上的最小流程

1. **克隆或拷贝**本仓库到目标机器。
2. **Python 3.10+**，在项目根执行：`pip install -r requirements.txt`。
3. 复制 **`copy .env.example .env`**（Linux/macOS：`cp .env.example .env`），按 **[用户手册 §4](./用户手册.md)** 填写 API Key、模型等。
4. **启动后端**（必须在项目根目录）：

   ```bash
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **接口文档（必读）**：后端启动后在本机浏览器打开 **http://127.0.0.1:8000/docs**（Swagger，可在线试调）；只读版 **http://127.0.0.1:8000/redoc**；机器可读规范：**http://127.0.0.1:8000/openapi.json**（部署到服务器时将 `127.0.0.1` 换成该机 IP 或域名）。
6. **可选前端**：`cd frontend && npm install && npm run dev`，浏览器 **http://127.0.0.1:5173**（开发时 Vite 将 `/api` 代理到后端）。

完整接口列表、入库格式说明、跨域与生产部署见 **[用户手册.md](./用户手册.md)**。

## 一分钟启动（CLI）

```bash
pip install -r requirements.txt
copy .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY 等

# 知识库入库后问答
python -m src.rag.ingest --path data/docs --clear
python -m src.rag.main -q "年假至少多少天？"

# 仅内容生成（不写知识库）
python -m src.main --topic "你的主题"
```

详细参数见 **[用户手册.md](./用户手册.md)**。

## HTTP API 速查

| 用途 | 方法 | 路径 |
|------|------|------|
| 交互式文档 | GET | `/docs` |
| 只读文档 | GET | `/redoc` |
| OpenAPI JSON | GET | `/openapi.json` |
| 健康检查 | GET | `/health` |
| 内容生成 | POST | `/api/v1/content/generate` |
| RAG 问答 | POST | `/api/v1/rag/query` |
| 文件入库 | POST | `/api/v1/rag/ingest` |
| 历史上传列表 | GET | `/api/v1/rag/uploads` |
| 从历史再次入库 | POST | `/api/v1/rag/reingest` |

请求体、表单字段以 **Swagger `/docs`** 为准。
