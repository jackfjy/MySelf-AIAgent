import axios from "axios";

const client = axios.create({
  baseURL: "/api/v1",
  timeout: 120_000,
});

/**
 * 将接口/网络错误转成可读文案。
 * 注意：使用 FormData 时不要手动设置 Content-Type，否则缺少 boundary，服务端无法解析 multipart。
 */
export function formatApiError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data;
    if (data != null) {
      if (typeof data === "string" && data.trim()) {
        return data;
      }
      if (typeof data === "object") {
        const d = data as Record<string, unknown>;
        if (typeof d.detail === "string" && d.detail.trim()) {
          return d.detail;
        }
        if (Array.isArray(d.detail)) {
          const parts = d.detail.map((item: unknown) => {
            if (typeof item === "string") return item;
            if (item && typeof item === "object" && "msg" in item) {
              return String((item as { msg: unknown }).msg);
            }
            return JSON.stringify(item);
          });
          const joined = parts.filter(Boolean).join(" ");
          if (joined.trim()) return joined;
        }
        try {
          const s = JSON.stringify(data);
          if (s !== "{}" && s !== "null") return s;
        } catch {
          /* ignore */
        }
      }
    }
    if (err.message?.trim()) {
      return err.message;
    }
  }
  if (err instanceof Error && err.message.trim()) {
    return err.message;
  }
  return "请求失败（无详细说明），请打开浏览器开发者工具 Network 查看响应。";
}

export type RagQueryBody = {
  question: string;
  top_k?: number;
  thread_id?: string;
  source_contains?: string;
  rewrite?: boolean;
  multi_query?: boolean;
  multi_query_n?: number;
  rerank?: boolean;
  rerank_keep?: number;
};

export async function ragQuery(body: RagQueryBody) {
  const { data } = await client.post("/rag/query", body);
  return data as {
    retrieval_queries: string[];
    citations: string;
    answer: string;
  };
}

export async function ragIngest(files: File[], opts: { clear?: boolean; max_chars?: number }) {
  const fd = new FormData();
  for (const f of files) {
    fd.append("files", f);
  }
  fd.append("clear", opts.clear ? "true" : "false");
  fd.append("max_chars", String(opts.max_chars ?? 800));
  // 不传 Content-Type：由浏览器自动带 multipart boundary；手动写会丢 boundary，导致入库 4xx/解析失败
  const { data } = await client.post("/rag/ingest", fd);
  return data as {
    chunks_added: number;
    files_processed: number;
    store_size: number;
    details: { source: string; chunks: number; skipped?: boolean }[];
  };
}

export type UploadItem = {
  id: string;
  original_name: string;
  stored_filename: string;
  size: number;
  suffix: string;
  uploaded_at: string;
};

export async function listUploads() {
  const { data } = await client.get("/rag/uploads");
  return data as { items: UploadItem[]; count: number };
}

export async function ragReingest(ids: string[], opts: { clear?: boolean; max_chars?: number }) {
  const { data } = await client.post("/rag/reingest", {
    ids,
    clear: opts.clear ?? false,
    max_chars: opts.max_chars ?? 800,
  });
  return data as {
    chunks_added: number;
    files_processed: number;
    store_size: number;
    details: { source: string; chunks: number; skipped?: boolean }[];
  };
}
