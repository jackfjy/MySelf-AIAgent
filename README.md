# LangGraph 内容生成 + RAG 知识库问答（示例工程）

基于 **Python + LangChain + LangGraph**：支持「研究 → 写作 → 编辑」内容流水线，以及「文档入库 + 混合检索 + 可选重排序」的知识库问答。

## 文档导航

| 文档 | 说明 |
|------|------|
| **[用户手册.md](./用户手册.md)** | 安装、环境变量、命令行用法、示例数据与测试用例 |
| **[开发文档.md](./开发文档.md)** | 目录结构、模块与类职责、扩展与排错（面向开发者） |

## 一分钟启动

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

详细参数与测试步骤见 **[用户手册.md](./用户手册.md)**。

启动 HTTP API：`uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000`，文档见 http://127.0.0.1:8000/docs 。
