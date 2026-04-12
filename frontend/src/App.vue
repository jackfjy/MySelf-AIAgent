<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  formatApiError,
  listUploads,
  ragIngest,
  ragQuery,
  ragReingest,
  type RagQueryBody,
  type UploadItem,
} from "./api";

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
const reingestClear = ref(false);
const maxChars = ref(800);
const fileInput = ref<HTMLInputElement | null>(null);
const ingestLoading = ref(false);
const reingestLoading = ref(false);
const historyLoading = ref(false);
const uploadHistory = ref<UploadItem[]>([]);
const historySelection = ref<UploadItem[]>([]);
const selectedFiles = ref<File[]>([]);

const fileSummary = computed(() => {
  const n = selectedFiles.value.length;
  if (!n) return "未选择文件";
  const names = selectedFiles.value.map((f) => f.name);
  if (n <= 2) return names.join("、");
  return `${names.slice(0, 2).join("、")} 等 ${n} 个文件`;
});

function formatSize(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function onHistorySelectionChange(rows: UploadItem[]) {
  historySelection.value = rows;
}

async function loadUploads() {
  historyLoading.value = true;
  try {
    const r = await listUploads();
    uploadHistory.value = r.items;
  } catch {
    uploadHistory.value = [];
  } finally {
    historyLoading.value = false;
  }
}

onMounted(() => {
  threadId.value = crypto.randomUUID();
  void loadUploads();
});

function onFilesChange(ev: Event) {
  const el = ev.target as HTMLInputElement;
  selectedFiles.value = el.files ? Array.from(el.files) : [];
}

function pickFiles() {
  fileInput.value?.click();
}

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
    const msg = formatApiError(e);
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

async function copyThreadId() {
  try {
    await navigator.clipboard.writeText(threadId.value);
    ElMessage.success("已复制 thread_id");
  } catch {
    ElMessage.warning("复制失败，请手动选择复制");
  }
}

async function doIngest() {
  const inputEl = fileInput.value;
  const files = inputEl?.files ? Array.from(inputEl.files) : [];
  if (!files.length) {
    ElMessage.warning("请先选择支持的文档文件");
    return;
  }
  ingestLoading.value = true;
  try {
    const res = await ragIngest(files, { clear: ingestClear.value, max_chars: maxChars.value });
    ElMessage.success(`入库完成：新增片段 ${res.chunks_added}，当前库共 ${res.store_size} 条`);
    await loadUploads();
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e));
  } finally {
    ingestLoading.value = false;
    if (inputEl) inputEl.value = "";
    selectedFiles.value = [];
  }
}

async function doReingest() {
  const ids = historySelection.value.map((x) => x.id);
  if (!ids.length) {
    ElMessage.warning("请在表格中勾选要再次入库的文件");
    return;
  }
  reingestLoading.value = true;
  try {
    const res = await ragReingest(ids, { clear: reingestClear.value, max_chars: maxChars.value });
    ElMessage.success(`再次入库完成：新增片段 ${res.chunks_added}，当前库共 ${res.store_size} 条`);
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e));
  } finally {
    reingestLoading.value = false;
  }
}
</script>

<template>
  <div class="shell">
    <div class="shell-inner">
      <header class="hero">
        <div class="hero-text">
          <p class="eyebrow">RAG · 本地知识库</p>
          <h1 class="title">知识库问答</h1>
          <p class="subtitle">支持 Markdown、纯文本、PDF、Word（.doc/.docx）等入库，基于向量检索与对话模型回答问题。</p>
        </div>
        <div class="hero-actions">
          <div class="thread-row">
            <span class="thread-label">会话 ID</span>
            <el-tooltip content="用于多轮对话，与后端 thread_id 一致" placement="bottom">
              <code class="thread-code">{{ threadId }}</code>
            </el-tooltip>
            <el-button size="small" plain @click="copyThreadId">复制</el-button>
            <el-button type="primary" size="small" @click="newSession">新会话</el-button>
          </div>
        </div>
      </header>

      <div class="grid">
        <el-card class="panel upload-panel" shadow="hover">
          <template #header>
            <div class="card-head">
              <span class="card-title">上传知识库</span>
              <el-tag size="small" type="info" effect="plain">md · txt · pdf · doc · docx</el-tag>
            </div>
          </template>
          <p class="hint">
            单次最多 30 个文件，单文件不超过约 12MB（以后端为准）。成功上传的原件会保存在服务器知识库目录，可在下方「历史上传」中再次入库。旧版
            .doc 需本机安装 LibreOffice（soffice）或 Windows 安装 Word 并安装 pywin32。
          </p>

          <input
            ref="fileInput"
            class="file-hidden"
            type="file"
            multiple
            accept=".md,.txt,.markdown,.pdf,.doc,.docx,.MD,.TXT,.PDF,.DOC,.DOCX"
            @change="onFilesChange"
          />

          <div class="drop-zone" @click="pickFiles">
            <div class="drop-icon" aria-hidden="true" />
            <div class="drop-text">
              <strong>点击选择文件</strong>
              <span class="drop-sub">{{ fileSummary }}</span>
            </div>
          </div>

          <div class="form-row">
            <el-checkbox v-model="ingestClear">入库前清空已有索引</el-checkbox>
          </div>
          <div class="form-row align-center">
            <span class="field-label">每段最大字数</span>
            <el-input-number v-model="maxChars" :min="200" :max="4000" :step="50" controls-position="right" />
          </div>
          <el-button
            class="ingest-btn"
            type="primary"
            :loading="ingestLoading"
            :disabled="!selectedFiles.length"
            @click="doIngest"
          >
            上传并入库
          </el-button>

          <el-divider content-position="left">历史上传</el-divider>
          <p class="hint history-hint">以下为已保存到服务器的原件，可勾选后再次解析入库（例如清空索引后重建、或更换分片参数）。</p>
          <div class="history-toolbar">
            <el-button size="small" plain :loading="historyLoading" @click="loadUploads">刷新列表</el-button>
            <el-checkbox v-model="reingestClear">再次入库前清空索引</el-checkbox>
            <el-button
              type="primary"
              size="small"
              :disabled="!historySelection.length"
              :loading="reingestLoading"
              @click="doReingest"
            >
              将选中项再次入库
            </el-button>
          </div>
          <el-table
            class="history-table"
            :data="uploadHistory"
            row-key="id"
            max-height="240"
            size="small"
            border
            @selection-change="onHistorySelectionChange"
          >
            <el-table-column type="selection" width="42" />
            <el-table-column prop="original_name" label="文件名" min-width="100" show-overflow-tooltip />
            <el-table-column prop="suffix" label="类型" width="64" />
            <el-table-column label="大小" width="86">
              <template #default="{ row }">{{ formatSize(row.size) }}</template>
            </el-table-column>
            <el-table-column prop="uploaded_at" label="上传时间 (UTC)" min-width="158" show-overflow-tooltip />
          </el-table>
        </el-card>

        <el-card class="panel chat-panel" shadow="hover">
          <template #header>
            <div class="card-head">
              <span class="card-title">对话</span>
              <el-tag v-if="loading" size="small" type="warning" effect="light">生成中…</el-tag>
            </div>
          </template>

          <div class="msgs-wrap">
            <el-empty
              v-if="!messages.length"
              description="还没有消息，先在上方入库文档，再在此提问"
              :image-size="72"
            />
            <div v-else class="msgs">
              <div
                v-for="(m, i) in messages"
                :key="i"
                :class="['msg-row', m.role === 'user' ? 'is-user' : 'is-bot']"
              >
                <div class="avatar" :data-role="m.role">{{ m.role === "user" ? "我" : "答" }}</div>
                <div class="bubble-wrap">
                  <div :class="['bubble', m.role]">
                    <pre class="text">{{ m.content }}</pre>
                    <pre v-if="m.extra" class="extra">{{ m.extra }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <el-collapse class="adv-collapse">
            <el-collapse-item title="高级检索选项" name="adv">
              <div class="opt-grid">
                <label class="opt-item">
                  <span class="opt-label">top_k</span>
                  <el-input-number v-model="topK" :min="1" :max="50" size="small" />
                </label>
                <label class="opt-item wide">
                  <span class="opt-label">source 包含</span>
                  <el-input v-model="sourceContains" placeholder="如 hr/" clearable size="small" />
                </label>
                <div class="opt-checks">
                  <el-checkbox v-model="rewrite">查询改写</el-checkbox>
                  <el-checkbox v-model="multiQuery">多查询</el-checkbox>
                </div>
                <label class="opt-item">
                  <span class="opt-label">多查询条数</span>
                  <el-input-number v-model="multiQueryN" :min="2" :max="6" size="small" />
                </label>
                <div class="opt-checks">
                  <el-checkbox v-model="rerank">Rerank</el-checkbox>
                </div>
                <label class="opt-item">
                  <span class="opt-label">rerank_keep</span>
                  <el-input-number v-model="rerankKeep" :min="1" :max="20" size="small" />
                </label>
              </div>
            </el-collapse-item>
          </el-collapse>

          <div class="composer">
            <el-input
              v-model="input"
              type="textarea"
              :rows="3"
              resize="none"
              placeholder="输入问题；Enter 发送，Shift+Enter 换行"
              @keydown.enter.exact.prevent="send"
            />
            <el-button class="send-btn" type="primary" :loading="loading" @click="send">发送</el-button>
          </div>
        </el-card>
      </div>

      <footer class="footer">
        <span>开发模式请求经 Vite 代理到后端 <code>/api</code>；生产部署请配置同域或 CORS。</span>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.shell {
  --ink: #0f172a;
  --muted: #64748b;
  --line: #e2e8f0;
  --card: rgba(255, 255, 255, 0.92);
  --accent: #2563eb;
  --accent-soft: #eff6ff;
  --bot-bg: #f8fafc;
  --user-bg: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  --shadow: 0 18px 50px rgba(15, 23, 42, 0.08);

  min-height: 100%;
  padding: 28px 16px 40px;
  background:
    radial-gradient(1200px 500px at 10% -10%, rgba(59, 130, 246, 0.12), transparent 55%),
    radial-gradient(900px 400px at 90% 0%, rgba(99, 102, 241, 0.1), transparent 50%),
    linear-gradient(180deg, #eef2ff 0%, #f8fafc 45%, #f1f5f9 100%);
}

.shell-inner {
  max-width: 960px;
  margin: 0 auto;
}

.hero {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}

.eyebrow {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--accent);
}

.title {
  margin: 0 0 8px;
  font-size: 1.65rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--ink);
}

.subtitle {
  margin: 0;
  max-width: 520px;
  font-size: 14px;
  line-height: 1.55;
  color: var(--muted);
}

.hero-actions {
  flex: 1;
  min-width: 260px;
  display: flex;
  justify-content: flex-end;
}

.thread-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  padding: 12px 14px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  box-shadow: var(--shadow);
}

.thread-label {
  font-size: 12px;
  color: var(--muted);
}

.thread-code {
  flex: 1;
  min-width: 120px;
  max-width: min(360px, 100%);
  padding: 4px 8px;
  font-size: 11px;
  line-height: 1.4;
  word-break: break-all;
  color: #334155;
  background: #f1f5f9;
  border-radius: 6px;
  border: 1px solid var(--line);
}

.grid {
  display: grid;
  gap: 18px;
}

@media (min-width: 960px) {
  .grid {
    grid-template-columns: 1fr 1.15fr;
    align-items: start;
  }
}

.panel {
  border-radius: 14px !important;
  border: 1px solid rgba(226, 232, 240, 0.9) !important;
  background: var(--card) !important;
  backdrop-filter: blur(8px);
}

.panel :deep(.el-card__header) {
  padding: 14px 18px;
  border-bottom: 1px solid var(--line);
}

.panel :deep(.el-card__body) {
  padding: 18px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
}

.hint {
  margin: 0 0 14px;
  font-size: 13px;
  line-height: 1.55;
  color: var(--muted);
}

.file-hidden {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

.drop-zone {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 16px;
  margin-bottom: 14px;
  border: 1.5px dashed #cbd5e1;
  border-radius: 12px;
  background: linear-gradient(180deg, #fafbff 0%, #f8fafc 100%);
  cursor: pointer;
  transition:
    border-color 0.2s,
    background 0.2s,
    box-shadow 0.2s;
}

.drop-zone:hover {
  border-color: #93c5fd;
  background: var(--accent-soft);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

.drop-icon {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  border-radius: 12px;
  background: linear-gradient(145deg, #dbeafe, #eff6ff);
  border: 1px solid #bfdbfe;
  position: relative;
}

.drop-icon::after {
  content: "";
  position: absolute;
  inset: 10px;
  border-radius: 6px;
  border: 2px solid #3b82f6;
  border-top: none;
  border-right: none;
}

.drop-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.drop-text strong {
  font-size: 14px;
  color: var(--ink);
}

.drop-sub {
  font-size: 12px;
  color: var(--muted);
  word-break: break-all;
}

.form-row {
  margin-bottom: 12px;
}

.form-row.align-center {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.field-label {
  font-size: 13px;
  color: var(--muted);
}

.ingest-btn {
  width: 100%;
  margin-top: 4px;
  height: 40px;
  border-radius: 10px;
  font-weight: 600;
}

.panel :deep(.el-divider__text) {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.history-hint {
  margin-top: 0;
  margin-bottom: 10px;
}

.history-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
  margin-bottom: 10px;
}

.history-table {
  width: 100%;
  border-radius: 10px;
}

.msgs-wrap {
  min-height: 220px;
  margin-bottom: 12px;
}

.msgs {
  max-height: 380px;
  overflow-y: auto;
  padding-right: 4px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.msgs::-webkit-scrollbar {
  width: 6px;
}
.msgs::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.msg-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.msg-row.is-user {
  flex-direction: row-reverse;
}

.avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(145deg, #64748b, #475569);
}

.avatar[data-role="user"] {
  background: linear-gradient(145deg, #3b82f6, #1d4ed8);
}

.bubble-wrap {
  max-width: min(100%, 560px);
  flex: 1;
  min-width: 0;
}

.bubble {
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: var(--bot-bg);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}

.bubble.user {
  border-color: transparent;
  background: var(--user-bg);
  color: #fff;
  border-radius: 14px 14px 4px 14px;
}

.bubble.assistant {
  border-radius: 14px 14px 14px 4px;
}

.text,
.extra {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.55;
}

.bubble.user .text {
  color: #fff;
}

.extra {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed rgba(148, 163, 184, 0.6);
  font-size: 12px;
  color: #475569;
}

.bubble.user .extra {
  border-top-color: rgba(255, 255, 255, 0.35);
  color: rgba(255, 255, 255, 0.92);
}

.adv-collapse {
  margin-bottom: 12px;
  border: none;
  --el-collapse-header-height: 44px;
}

.adv-collapse :deep(.el-collapse-item__header) {
  font-size: 13px;
  font-weight: 500;
  color: #334155;
  background: #f8fafc;
  border-radius: 10px;
  padding: 0 12px;
  border: 1px solid var(--line);
}

.adv-collapse :deep(.el-collapse-item__wrap) {
  border: none;
}

.adv-collapse :deep(.el-collapse-item__content) {
  padding: 12px 0 0;
}

.opt-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px 14px;
}

.opt-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.opt-item.wide {
  grid-column: 1 / -1;
}

.opt-label {
  font-size: 12px;
  color: var(--muted);
}

.opt-checks {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  align-items: center;
  min-height: 32px;
}

.composer {
  display: flex;
  gap: 10px;
  align-items: stretch;
  padding-top: 4px;
}

.composer :deep(.el-textarea__inner) {
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.5;
}

.send-btn {
  align-self: stretch;
  min-width: 88px;
  border-radius: 12px;
  font-weight: 600;
}

.footer {
  margin-top: 22px;
  text-align: center;
  font-size: 12px;
  line-height: 1.5;
  color: #94a3b8;
}

.footer code {
  font-size: 11px;
  padding: 2px 6px;
  background: rgba(241, 245, 249, 0.9);
  border-radius: 4px;
  color: #64748b;
}
</style>
