<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { ragIngest, ragQuery, type RagQueryBody } from "./api";

type Msg = { role: "user" | "assistant"; content: string; extra?: string };

const threadId = ref("");
const input = ref("");
const loading = ref(false);
const messages = ref<Msg[]>([]);

const topK = ref(4);
const sourceContains = ref("");
const rewrite = ref(false);
const multiQuery = ref(false);
const multiQueryN = ref(3);
const rerank = ref(false);
const rerankKeep = ref(4);

const ingestClear = ref(false);
const maxChars = ref(800);
const fileInput = ref<HTMLInputElement | null>(null);
const ingestLoading = ref(false);

onMounted(() => {
  threadId.value = crypto.randomUUID();
});

async function send() {
  const q = input.value.trim();
  if (!q) {
    ElMessage.warning("请输入问题");
    return;
  }
  if (rewrite.value && multiQuery.value) {
    ElMessage.error("改写与多查询不能同时开启");
    return;
  }
  loading.value = true;
  messages.value.push({ role: "user", content: q });
  input.value = "";
  try {
    const body: RagQueryBody = {
      question: q,
      top_k: topK.value,
      thread_id: threadId.value,
      source_contains: sourceContains.value || undefined,
      rewrite: rewrite.value,
      multi_query: multiQuery.value,
      multi_query_n: multiQueryN.value,
      rerank: rerank.value,
      rerank_keep: rerankKeep.value,
    };
    const res = await ragQuery(body);
    let extra = "";
    if (res.retrieval_queries?.length) {
      extra += "【检索 query】\n" + res.retrieval_queries.map((s, i) => `${i + 1}. ${s}`).join("\n") + "\n\n";
    }
    if (res.citations) {
      extra += "【引用】\n" + res.citations;
    }
    messages.value.push({ role: "assistant", content: res.answer, extra: extra.trim() || undefined });
  } catch (e: unknown) {
    const err = e as { response?: { data?: unknown }; message?: string };
    const msg = JSON.stringify(err.response?.data ?? err.message ?? e);
    messages.value.push({ role: "assistant", content: "请求失败：" + msg });
    ElMessage.error("请求失败，请确认后端已启动且已 pip install 依赖");
  } finally {
    loading.value = false;
  }
}

function newSession() {
  threadId.value = crypto.randomUUID();
  messages.value = [];
  ElMessage.success("已新建会话");
}

async function doIngest() {
  const inputEl = fileInput.value;
  const files = inputEl?.files ? Array.from(inputEl.files) : [];
  if (!files.length) {
    ElMessage.warning("请先选择 .md / .txt 文件");
    return;
  }
  ingestLoading.value = true;
  try {
    const res = await ragIngest(files, { clear: ingestClear.value, max_chars: maxChars.value });
    ElMessage.success(`入库完成：新增片段 ${res.chunks_added}，当前库共 ${res.store_size} 条`);
  } catch (e: unknown) {
    const err = e as { response?: { data?: unknown }; message?: string };
    ElMessage.error(JSON.stringify(err.response?.data ?? err.message ?? e));
  } finally {
    ingestLoading.value = false;
    if (inputEl) inputEl.value = "";
  }
}
</script>

<template>
  <div class="page">
    <header class="header">
      <h1>知识库问答</h1>
      <div class="meta">
        <span class="label">thread_id</span>
        <code class="tid">{{ threadId }}</code>
        <el-button size="small" @click="newSession">新会话</el-button>
      </div>
    </header>

    <section class="upload card">
      <h2>上传知识库文档</h2>
      <p class="hint">支持 .md、.txt、.markdown；单次最多 30 个文件，单文件不超过 5MB（以后端限制为准）。</p>
      <div class="row">
        <input
          ref="fileInput"
          type="file"
          multiple
          accept=".md,.txt,.markdown,.MD,.TXT"
        />
        <el-checkbox v-model="ingestClear">入库前清空已有索引</el-checkbox>
      </div>
      <div class="row">
        <span class="label">每段最大字数</span>
        <el-input-number v-model="maxChars" :min="200" :max="4000" :step="50" />
      </div>
      <el-button type="primary" :loading="ingestLoading" @click="doIngest">上传并入库</el-button>
    </section>

    <section class="chat card">
      <h2>对话</h2>
      <div class="msgs">
        <div v-for="(m, i) in messages" :key="i" :class="['bubble', m.role]">
          <div class="role">{{ m.role === "user" ? "你" : "助手" }}</div>
          <pre class="text">{{ m.content }}</pre>
          <pre v-if="m.extra" class="extra">{{ m.extra }}</pre>
        </div>
      </div>
      <div class="opts">
        <el-collapse>
          <el-collapse-item title="高级检索选项" name="1">
            <div class="grid">
              <label>top_k <el-input-number v-model="topK" :min="1" :max="50" /></label>
              <label>source 包含 <el-input v-model="sourceContains" placeholder="如 hr/" clearable /></label>
              <el-checkbox v-model="rewrite">查询改写</el-checkbox>
              <el-checkbox v-model="multiQuery">多查询</el-checkbox>
              <label>多查询条数 <el-input-number v-model="multiQueryN" :min="2" :max="6" /></label>
              <el-checkbox v-model="rerank">Rerank</el-checkbox>
              <label>rerank_keep <el-input-number v-model="rerankKeep" :min="1" :max="20" /></label>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
      <div class="composer">
        <el-input
          v-model="input"
          type="textarea"
          :rows="3"
          placeholder="输入问题，Enter 发送（可结合 thread_id 多轮）"
          @keydown.enter.exact.prevent="send"
        />
        <el-button type="primary" :loading="loading" @click="send">发送</el-button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page {
  max-width: 880px;
  margin: 0 auto;
  padding: 16px;
  font-family: system-ui, sans-serif;
}
.header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.header h1 {
  margin: 0;
  font-size: 1.25rem;
}
.meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.tid {
  font-size: 12px;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.label {
  color: #666;
  font-size: 13px;
}
.card {
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}
.card h2 {
  margin: 0 0 8px;
  font-size: 1rem;
}
.hint {
  color: #666;
  font-size: 13px;
  margin: 0 0 12px;
}
.row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.msgs {
  min-height: 120px;
  margin-bottom: 12px;
}
.bubble {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 8px;
}
.bubble.user {
  background: #ecf5ff;
}
.bubble.assistant {
  background: #f5f7fa;
}
.role {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}
.text,
.extra {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 14px;
}
.extra {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #dcdfe6;
  font-size: 12px;
  color: #606266;
}
.grid {
  display: grid;
  gap: 8px;
}
.composer {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.composer .el-input {
  flex: 1;
}
</style>
