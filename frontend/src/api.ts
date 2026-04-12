import axios from "axios";

const client = axios.create({
  baseURL: "/api/v1",
  timeout: 120_000,
});

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
  const { data } = await client.post("/rag/ingest", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data as {
    chunks_added: number;
    files_processed: number;
    store_size: number;
    details: { source: string; chunks: number; skipped?: boolean }[];
  };
}
