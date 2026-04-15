<template>
  <div class="doc-manager-page">
    <div class="doc-shell">
      <!-- ─── 左：文档列表 ─────────────────────── -->
      <aside class="doc-sidebar">
        <div class="doc-sidebar-header">
          <span class="doc-sidebar-title">📂 文档列表</span>
          <button v-if="isAdmin" class="new-doc-btn" @click="showCreateModal">
            + 新建
          </button>
          <span v-else class="readonly-badge">只读</span>
        </div>

        <div class="doc-list" v-if="!listLoading">
          <div v-if="docs.length === 0" class="doc-empty">
            <span>暂无文档</span>
          </div>
          <div
            v-for="doc in docs"
            :key="doc.id"
            class="doc-item"
            :class="{ active: selectedDocId === doc.id }"
            @click="selectDoc(doc.id)"
          >
            <div class="doc-item-info">
              <div class="doc-name">{{ doc.id }}</div>
              <div class="doc-size">{{ formatSize(doc.size) }}</div>
            </div>
            <button
              v-if="isAdmin"
              class="doc-del-btn"
              @click.stop="confirmDelete(doc.id)"
              title="删除"
            >✕</button>
          </div>
        </div>

        <div v-else class="doc-list-loading">
          <div class="mini-spin" />
        </div>
      </aside>

      <!-- ─── 右：编辑区 ────────────────────────── -->
      <div class="doc-editor-area">
        <!-- 未选中 -->
        <div v-if="!selectedDocId" class="no-doc">
          <div class="no-doc-icon">📄</div>
          <div class="no-doc-text">从左侧选择一篇文档查看</div>
          <button v-if="isAdmin" class="ghost-btn" @click="showCreateModal">+ 新建文档</button>
        </div>

        <template v-else>
          <!-- Editor Topbar -->
          <div class="editor-topbar">
            <span class="editor-filename">📝 {{ selectedDocId }}</span>
            <div class="editor-actions">
              <template v-if="isAdmin">
                <span class="save-status" :class="hasUnsaved ? 'unsaved' : 'saved'">
                  {{ hasUnsaved ? '未保存' : '✓ 已保存' }}
                </span>
                <button class="save-btn" :class="{ loading: saving }" :disabled="saving || !hasUnsaved" @click="saveDoc">
                  <span v-if="saving" class="mini-spin" /> 保存
                </button>
                <button class="del-btn" @click="confirmDelete(selectedDocId!)">删除</button>
              </template>
              <span v-else class="perm-hint">👁 仅查看</span>
            </div>
          </div>

          <!-- Mode Tabs -->
          <div class="mode-tabs">
            <button v-for="m in modes" :key="m.key" class="mode-tab" :class="{ active: editorMode === m.key }" @click="editorMode = m.key">{{ m.label }}</button>
          </div>

          <!-- Edit -->
          <div v-if="editorMode === 'edit'" class="editor-body">
            <textarea
              v-model="editContent"
              class="md-editor"
              :class="{ readonly: !isAdmin }"
              :disabled="docLoading"
              :readonly="!isAdmin"
              placeholder="在此输入 Markdown 内容..."
              @input="isAdmin && (hasUnsaved = true)"
            />
          </div>

          <!-- Preview -->
          <div v-if="editorMode === 'preview'" class="editor-body">
            <div class="md-preview markdown-body" v-html="renderMarkdown(editContent)" />
          </div>

          <!-- Split -->
          <div v-if="editorMode === 'split'" class="editor-body split-body">
            <div class="split-pane">
              <div class="pane-label">编辑</div>
              <textarea
                v-model="editContent"
                class="md-editor"
                :class="{ readonly: !isAdmin }"
                :disabled="docLoading"
                :readonly="!isAdmin"
                @input="isAdmin && (hasUnsaved = true)"
                placeholder="在此输入 Markdown 内容..."
              />
            </div>
            <div class="split-divider" />
            <div class="split-pane">
              <div class="pane-label">预览</div>
              <div class="md-preview markdown-body" v-html="renderMarkdown(editContent)" />
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Create Modal -->
    <div v-if="createModalVisible" class="modal-overlay" @click.self="createModalVisible = false">
      <div class="modal">
        <div class="modal-header">
          <span>新建文档</span>
          <button class="modal-close" @click="createModalVisible = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>文档名称 <span class="required">*</span></label>
            <input v-model="newDocName" class="form-input" placeholder="例如：compliance_rules_v2" maxlength="50" @keydown.enter="createDocument" />
            <span class="form-hint">支持字母、数字、中文、下划线和连字符</span>
          </div>
          <div class="form-item">
            <label>初始内容（可选）</label>
            <textarea v-model="newDocContent" class="form-textarea" rows="6" placeholder="# 文档标题&#10;&#10;在此输入文档内容..." />
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="createModalVisible = false">取消</button>
          <button class="confirm-btn" :class="{ loading: creating }" :disabled="creating" @click="createDocument">
            <span v-if="creating" class="mini-spin" />创建
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { marked } from 'marked'
import { getDocs, createDoc, getDoc, updateDoc, deleteDoc, type Doc } from '@/api'
import { auth } from '@/stores/auth'

const isAdmin = auth.isAdmin

const docs = ref<Doc[]>([])
const selectedDocId = ref<string | null>(null)
const editContent = ref('')
const originalContent = ref('')
const listLoading = ref(false)
const docLoading = ref(false)
const saving = ref(false)
const creating = ref(false)
const editorMode = ref('split')
const createModalVisible = ref(false)
const newDocName = ref('')
const newDocContent = ref('')

const modes = [
  { key: 'edit', label: '✏️ 编辑' },
  { key: 'preview', label: '👁 预览' },
  { key: 'split', label: '⚡ 分栏' },
]

const hasUnsaved = computed(() => editContent.value !== originalContent.value)

function renderMarkdown(text: string) {
  try { return marked(text) as string } catch { return text }
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

async function loadDocs() {
  listLoading.value = true
  try { docs.value = await getDocs() }
  catch (e: any) { message.error(`加载失败：${e.message}`) }
  finally { listLoading.value = false }
}

async function selectDoc(id: string) {
  selectedDocId.value = id; docLoading.value = true
  try {
    const doc = await getDoc(id)
    editContent.value = doc.content; originalContent.value = doc.content
  } catch (e: any) { message.error(`加载文档失败：${e.message}`) }
  finally { docLoading.value = false }
}

function showCreateModal() {
  newDocName.value = ''; newDocContent.value = '# 新文档\n\n在此输入内容...\n'
  createModalVisible.value = true
}

async function createDocument() {
  if (!newDocName.value.trim()) { message.warning('请输入文档名称'); return }
  creating.value = true
  try {
    await createDoc(newDocName.value.trim(), newDocContent.value)
    message.success('文档创建成功'); createModalVisible.value = false
    await loadDocs()
    await selectDoc(newDocName.value.trim().replace(/\s+/g, '_'))
  } catch (e: any) { message.error(`创建失败：${e.message}`) }
  finally { creating.value = false }
}

async function saveDoc() {
  if (!selectedDocId.value) return
  saving.value = true
  try {
    await updateDoc(selectedDocId.value, editContent.value)
    originalContent.value = editContent.value
    message.success('保存成功'); await loadDocs()
  } catch (e: any) { message.error(`保存失败：${e.message}`) }
  finally { saving.value = false }
}

async function confirmDelete(id: string) {
  if (!confirm(`确定删除文档「${id}」吗？`)) return
  try {
    await deleteDoc(id); message.success('文档已删除')
    if (selectedDocId.value === id) { selectedDocId.value = null; editContent.value = ''; originalContent.value = '' }
    await loadDocs()
  } catch (e: any) { message.error(`删除失败：${e.message}`) }
}

function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); saveDoc() }
}

onMounted(() => { loadDocs(); document.addEventListener('keydown', handleKeydown) })
</script>

<style scoped>
.doc-manager-page {
  height: calc(100vh - 60px - 40px - 40px);
  display: flex;
}

.doc-shell {
  flex: 1;
  display: flex;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface);
}

/* ─── Sidebar ────────────────────────────────────── */
.doc-sidebar {
  width: 220px;
  min-width: 220px;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  background: var(--surface);
}

.doc-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.doc-sidebar-title { font-size: 13px; font-weight: 600; color: var(--text); }

.new-doc-btn {
  padding: 3px 10px;
  background: var(--accent-soft);
  border: 1px solid var(--border-glow);
  border-radius: 6px;
  color: var(--accent);
  font-size: 12px;
  cursor: pointer;
  transition: background var(--transition);
}
.new-doc-btn:hover { background: rgba(210,170,90,.2); }

.readonly-badge {
  font-size: 11px;
  color: var(--info);
  background: rgba(88,166,255,.1);
  border: 1px solid rgba(88,166,255,.25);
  padding: 2px 8px;
  border-radius: 10px;
}

.perm-hint {
  font-size: 12px;
  color: var(--info);
  opacity: 0.8;
}

.md-editor.readonly {
  opacity: 0.75;
  cursor: default;
}

.doc-list { flex: 1; overflow-y: auto; padding: 8px 0; }

.doc-empty { padding: 20px; text-align: center; font-size: 13px; color: var(--text-dim); }

.doc-item {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: background var(--transition), border-color var(--transition);
}
.doc-item:hover { background: var(--surface-2); }
.doc-item.active { background: var(--accent-soft); border-left-color: var(--accent); }

.doc-item-info { flex: 1; min-width: 0; }
.doc-name { font-size: 13px; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.doc-size { font-size: 11px; color: var(--text-dim); margin-top: 2px; }

.doc-del-btn {
  opacity: 0;
  background: transparent;
  border: none;
  color: var(--danger);
  font-size: 12px;
  cursor: pointer;
  padding: 2px 5px;
  border-radius: 4px;
  transition: opacity var(--transition), background var(--transition);
  flex-shrink: 0;
}
.doc-item:hover .doc-del-btn { opacity: 1; }
.doc-del-btn:hover { background: rgba(248,81,73,.15); }

.doc-list-loading { flex: 1; display: flex; align-items: center; justify-content: center; }

/* ─── Editor Area ────────────────────────────────── */
.doc-editor-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg);
}

.no-doc {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
.no-doc-icon { font-size: 52px; opacity: .3; }
.no-doc-text { font-size: 14px; color: var(--text-muted); }

.ghost-btn {
  padding: 7px 18px;
  background: transparent;
  border: 1px solid var(--border-glow);
  border-radius: 20px;
  color: var(--accent);
  font-size: 13px;
  cursor: pointer;
}
.ghost-btn:hover { background: var(--accent-soft); }

/* Editor topbar */
.editor-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
}

.editor-filename { font-size: 13px; color: var(--text-muted); font-family: 'SF Mono', monospace; }

.editor-actions { display: flex; align-items: center; gap: 8px; }

.save-status { font-size: 12px; }
.save-status.saved  { color: var(--safe); }
.save-status.unsaved { color: var(--warn); }

.save-btn, .del-btn {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  border: 1px solid;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: filter var(--transition);
}
.save-btn {
  background: var(--accent);
  border-color: var(--accent);
  color: #0d1117;
  font-weight: 600;
}
.save-btn:disabled { opacity: .4; cursor: not-allowed; }
.save-btn:hover:not(:disabled) { filter: brightness(1.1); }

.del-btn {
  background: transparent;
  border-color: rgba(248,81,73,.4);
  color: var(--danger);
}
.del-btn:hover { background: rgba(248,81,73,.1); }

/* Mode tabs */
.mode-tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
}
.mode-tab {
  padding: 8px 16px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color var(--transition), border-color var(--transition);
}
.mode-tab:hover { color: var(--text); }
.mode-tab.active { color: var(--accent); border-bottom-color: var(--accent); }

/* Editor Body */
.editor-body { flex: 1; overflow: hidden; display: flex; min-height: 0; }

.md-editor {
  width: 100%;
  height: 100%;
  background: var(--bg);
  border: none;
  color: var(--text);
  font-size: 13.5px;
  font-family: 'SF Mono', 'Courier New', monospace;
  line-height: 1.8;
  padding: 20px;
  resize: none;
  outline: none;
}

.md-preview {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: 20px 24px;
  background: var(--bg);
  font-size: 14px;
  line-height: 1.8;
}

.split-body { display: flex; }
.split-pane { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.split-divider { width: 1px; background: var(--border); flex-shrink: 0; }
.pane-label { font-size: 11px; color: var(--text-dim); padding: 6px 16px; border-bottom: 1px solid var(--border); background: var(--surface); }

/* ─── Modal ──────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  width: 440px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,.5);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.modal-close {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}
.modal-close:hover { color: var(--text); background: var(--surface-2); }

.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 16px; }

.form-item { display: flex; flex-direction: column; gap: 6px; }
.form-item label { font-size: 13px; color: var(--text-muted); }
.required { color: var(--danger); }

.form-input, .form-textarea {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-size: 13px;
  padding: 8px 12px;
  outline: none;
  font-family: inherit;
  transition: border-color var(--transition);
}
.form-input:focus, .form-textarea:focus { border-color: var(--accent); }
.form-input::placeholder, .form-textarea::placeholder { color: var(--text-dim); }
.form-textarea { resize: vertical; }
.form-hint { font-size: 11px; color: var(--text-dim); }

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 14px 20px;
  border-top: 1px solid var(--border);
}

.cancel-btn {
  padding: 7px 16px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
}
.cancel-btn:hover { color: var(--text); border-color: var(--text-muted); }

.confirm-btn {
  padding: 7px 20px;
  background: linear-gradient(135deg, var(--accent), #a07830);
  border: none;
  border-radius: 8px;
  color: #0d1117;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.confirm-btn:hover:not(:disabled) { filter: brightness(1.1); }
.confirm-btn:disabled { opacity: .5; cursor: not-allowed; }

/* ─── Shared ──────────────────────────────────────── */
.mini-spin {
  width: 12px; height: 12px;
  border: 2px solid rgba(0,0,0,.3);
  border-top-color: #0d1117;
  border-radius: 50%;
  animation: spin .7s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ─── Markdown preview styles ───────────────────── */
:deep(.markdown-body) { color: var(--text); }
:deep(.markdown-body h1) { font-size: 22px; border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 16px; color: var(--text); }
:deep(.markdown-body h2) { font-size: 18px; border-bottom: 1px solid var(--border); padding-bottom: 6px; margin: 20px 0 12px; color: var(--text); }
:deep(.markdown-body h3) { font-size: 15px; margin: 16px 0 8px; color: var(--text); }
:deep(.markdown-body p) { margin: 8px 0; color: var(--text); }
:deep(.markdown-body ul) { padding-left: 24px; }
:deep(.markdown-body li) { margin: 4px 0; color: var(--text); }
:deep(.markdown-body code) { background: var(--surface-2); padding: 2px 6px; border-radius: 4px; font-size: 12px; color: var(--accent); }
:deep(.markdown-body pre) { background: var(--surface-2); padding: 16px; border-radius: var(--radius); overflow-x: auto; border: 1px solid var(--border); }
:deep(.markdown-body blockquote) { border-left: 3px solid var(--accent); padding-left: 16px; color: var(--text-muted); margin: 12px 0; }
:deep(.markdown-body table) { border-collapse: collapse; width: 100%; margin: 12px 0; }
:deep(.markdown-body th), :deep(.markdown-body td) { border: 1px solid var(--border); padding: 8px 12px; color: var(--text); }
:deep(.markdown-body th) { background: var(--surface-2); color: var(--text-muted); font-weight: 600; }
:deep(.markdown-body strong) { color: var(--text); font-weight: 600; }
</style>
