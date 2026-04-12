# 前端（Vue 3 + Vite + Element Plus）

## 环境要求

- **Node.js**：建议 **18、20 或 ≥22**（与 Vite 6 的 `engines` 一致；若用 Node 21 可能仅有 engine 警告，一般仍可构建）。
- **npm**：随 Node 安装即可。

## 前提：后端已启动

在项目**仓库根目录**（与 `src/` 同级），先启动 API：

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

在新电脑上需已完成：`pip install -r requirements.txt`、配置根目录 `.env`。详见根目录 **[用户手册.md](../用户手册.md)**。

## 安装与开发

```bash
cd frontend
npm install
npm run dev
```

浏览器访问：**http://127.0.0.1:5173**

开发模式下，**Vite 将 `/api` 代理到 `http://127.0.0.1:8000`**（见 `vite.config.ts`），前端使用相对路径请求 `/api/v1/...`，无需改后端地址。

**注意**：`multipart` 上传**不要**在前端手动设置 `Content-Type: multipart/form-data`（需由浏览器自动带 `boundary`），否则入库会失败。

## 功能（与后端接口对应）

| 功能 | 接口 |
|------|------|
| 上传并入库（md/txt/pdf/doc/docx 等） | `POST /api/v1/rag/ingest` |
| 历史上传列表 | `GET /api/v1/rag/uploads` |
| 勾选历史文件再次入库 | `POST /api/v1/rag/reingest` |
| 对话 / 高级检索选项 | `POST /api/v1/rag/query` |

完整字段说明以服务端 **http://127.0.0.1:8000/docs** 为准。

## 构建与生产部署

```bash
npm run build
```

产物在 **`frontend/dist/`**。交给 Nginx、Caddy 等托管静态资源时，需要：

- **同源**：前端与 API 同域名，将 `/api` 反代到后端（例如 `8000`）；或  
- **跨域**：后端设置环境变量 **`CORS_ORIGINS`** 为前端页面所在 origin（多个用英文逗号分隔），详见 **[用户手册.md](../用户手册.md)**。

生产环境一般不会跑 Vite 开发服务器，因此需在网关或构建时配置 API 基地址（若前后端不同域）。

## 接口文档（给联调/运维）

后端启动后：

- **Swagger UI**：`http://<后端主机>:8000/docs`
- **ReDoc**：`http://<后端主机>:8000/redoc`
- **OpenAPI JSON**：`http://<后端主机>:8000/openapi.json`（可导入 Postman、Apifox 等）
