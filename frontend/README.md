# 前端（Vue 3 + Vite + Element Plus）

## 前提

后端已在项目根启动：

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## 安装与开发

```bash
cd frontend
npm install
npm run dev
```

浏览器访问：**http://127.0.0.1:5173**

开发时 Vite 将 `/api` 代理到 `http://127.0.0.1:8000`，因此前端请求使用相对路径 `/api/v1/...` 即可。

## 功能

- **上传并入库**：选择多个 `.md` / `.txt`，调用 `POST /api/v1/rag/ingest`
- **对话**：调用 `POST /api/v1/rag/query`，支持 `thread_id` 多轮与折叠面板中的高级选项

## 构建

```bash
npm run build
```

将 `dist/` 交给 Nginx 等静态托管；生产环境请配置与后端同域或正确设置 `CORS_ORIGINS`。
