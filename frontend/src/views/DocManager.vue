<template>
  <div class="doc-manager-page">
    <a-row :gutter="16" style="height: 100%">
      <!-- 左侧文档列表 -->
      <a-col :span="6">
        <a-card class="doc-list-card" :body-style="{ padding: '8px 0' }">
          <template #title>
            <div class="list-header">
              <span>📄 文档列表</span>
              <a-button
                type="primary"
                size="small"
                :icon="h(PlusOutlined)"
                @click="showCreateModal"
              >
                新建
              </a-button>
            </div>
          </template>

          <a-spin :spinning="listLoading">
            <div v-if="docs.length === 0 && !listLoading" class="empty-list">
              <a-empty :image="Empty.PRESENTED_IMAGE_SIMPLE" description="暂无文档" />
            </div>

            <div
              v-for="doc in docs"
              :key="doc.id"
              class="doc-item"
              :class="{ active: selectedDocId === doc.id }"
              @click="selectDoc(doc.id)"
            >
              <div class="doc-item-left">
                <file-markdown-outlined class="doc-icon" />
                <div class="doc-info">
                  <div class="doc-name">{{ doc.name }}</div>
                  <div class="doc-meta">{{ formatSize(doc.size) }}</div>
                </div>
              </div>
              <a-popconfirm
                title="确认删除此文档？"
                ok-text="删除"
                cancel-text="取消"
                ok-type="danger"
                @confirm.stop="deleteDocument(doc.id)"
                @click.stop
              >
                <delete-outlined
                  class="doc-delete"
                  @click.stop
                />
              </a-popconfirm>
            </div>
          </a-spin>
        </a-card>
      </a-col>

      <!-- 右侧编辑/预览区 -->
      <a-col :span="18">
        <a-card class="editor-card">
          <template #title>
            <div class="editor-header">
              <span v-if="selectedDocId">📝 {{ selectedDocId }}</span>
              <span v-else>选择或新建文档开始编辑</span>
            </div>
          </template>

          <template #extra>
            <a-space v-if="selectedDocId">
              <a-tag :color="hasUnsaved ? 'orange' : 'green'">
                {{ hasUnsaved ? '未保存' : '已保存' }}
              </a-tag>
              <a-button
                type="primary"
                size="small"
                :icon="h(SaveOutlined)"
                :loading="saving"
                @click="saveDoc"
              >
                保存
              </a-button>
              <a-popconfirm
                title="确认删除此文档？"
                ok-text="删除"
                cancel-text="取消"
                ok-type="danger"
                @confirm="deleteDocument(selectedDocId!)"
              >
                <a-button danger size="small" :icon="h(DeleteOutlined)">
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>

          <!-- 未选中文档 -->
          <div v-if="!selectedDocId" class="no-doc">
            <a-empty description="请从左侧选择文档，或新建文档">
              <a-button type="primary" @click="showCreateModal">
                <plus-outlined /> 新建文档
              </a-button>
            </a-empty>
          </div>

          <!-- 编辑器 + 预览 -->
          <div v-else class="editor-preview">
            <a-tabs v-model:activeKey="editorMode">
              <a-tab-pane key="edit" tab="✏️ 编辑">
                <a-textarea
                  v-model:value="editContent"
                  :rows="30"
                  :disabled="docLoading"
                  class="doc-editor"
                  @input="hasUnsaved = true"
                  placeholder="在此输入 Markdown 内容..."
                />
              </a-tab-pane>
              <a-tab-pane key="preview" tab="👁️ 预览">
                <div class="doc-preview markdown-body" v-html="renderMarkdown(editContent)" />
              </a-tab-pane>
              <a-tab-pane key="split" tab="⚡ 分栏">
                <div class="split-view">
                  <div class="split-editor">
                    <div class="split-label">编辑</div>
                    <a-textarea
                      v-model:value="editContent"
                      :rows="28"
                      :disabled="docLoading"
                      class="doc-editor"
                      @input="hasUnsaved = true"
                      placeholder="在此输入 Markdown 内容..."
                    />
                  </div>
                  <div class="split-preview">
                    <div class="split-label">预览</div>
                    <div class="doc-preview markdown-body" v-html="renderMarkdown(editContent)" />
                  </div>
                </div>
              </a-tab-pane>
            </a-tabs>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 新建文档 Modal -->
    <a-modal
      v-model:open="createModalVisible"
      title="新建文档"
      @ok="createDocument"
      :confirm-loading="creating"
      ok-text="创建"
      cancel-text="取消"
    >
      <a-form layout="vertical">
        <a-form-item label="文档名称" required>
          <a-input
            v-model:value="newDocName"
            placeholder="请输入文档名称（如：compliance_rules_v2）"
            :maxlength="50"
            show-count
            @press-enter="createDocument"
          />
          <div style="font-size: 12px; color: #999; margin-top: 4px">
            文档将以 .md 格式保存，只支持字母、数字、中文、下划线和连字符
          </div>
        </a-form-item>
        <a-form-item label="初始内容（可选）">
          <a-textarea
            v-model:value="newDocContent"
            :rows="6"
            placeholder="# 文档标题&#10;&#10;在此输入文档内容..."
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, h } from 'vue'
import { message, Empty } from 'ant-design-vue'
import {
  PlusOutlined,
  SaveOutlined,
  DeleteOutlined,
  FileMarkdownOutlined
} from '@ant-design/icons-vue'
import { marked } from 'marked'
import { getDocs, createDoc, getDoc, updateDoc, deleteDoc, type Doc } from '@/api'

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

const hasUnsaved = computed(() => editContent.value !== originalContent.value)

function renderMarkdown(text: string): string {
  try {
    return marked(text) as string
  } catch {
    return text
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

async function loadDocs() {
  listLoading.value = true
  try {
    docs.value = await getDocs()
  } catch (err: any) {
    message.error(`加载文档列表失败：${err.message}`)
  } finally {
    listLoading.value = false
  }
}

async function selectDoc(id: string) {
  if (hasUnsaved.value && selectedDocId.value) {
    // 可以提示保存，这里简单处理
  }

  selectedDocId.value = id
  docLoading.value = true

  try {
    const doc = await getDoc(id)
    editContent.value = doc.content
    originalContent.value = doc.content
  } catch (err: any) {
    message.error(`加载文档失败：${err.message}`)
  } finally {
    docLoading.value = false
  }
}

function showCreateModal() {
  newDocName.value = ''
  newDocContent.value = `# 新文档\n\n在此输入内容...\n`
  createModalVisible.value = true
}

async function createDocument() {
  if (!newDocName.value.trim()) {
    message.warning('请输入文档名称')
    return
  }

  creating.value = true

  try {
    await createDoc(newDocName.value.trim(), newDocContent.value)
    message.success('文档创建成功')
    createModalVisible.value = false
    await loadDocs()

    // 自动选中新文档
    const safeId = newDocName.value.trim().replace(/\s+/g, '_')
    await selectDoc(safeId)
  } catch (err: any) {
    message.error(`创建失败：${err.message}`)
  } finally {
    creating.value = false
  }
}

async function saveDoc() {
  if (!selectedDocId.value) return

  saving.value = true

  try {
    await updateDoc(selectedDocId.value, editContent.value)
    originalContent.value = editContent.value
    message.success('保存成功')
    await loadDocs() // 更新文件大小
  } catch (err: any) {
    message.error(`保存失败：${err.message}`)
  } finally {
    saving.value = false
  }
}

async function deleteDocument(id: string) {
  try {
    await deleteDoc(id)
    message.success('文档已删除')

    if (selectedDocId.value === id) {
      selectedDocId.value = null
      editContent.value = ''
      originalContent.value = ''
    }

    await loadDocs()
  } catch (err: any) {
    message.error(`删除失败：${err.message}`)
  }
}

// 键盘快捷键保存
function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    saveDoc()
  }
}

onMounted(() => {
  loadDocs()
  document.addEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.doc-manager-page {
  height: calc(100vh - 64px - 70px - 48px);
}

.doc-list-card,
.editor-card {
  height: 100%;
  overflow: auto;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.empty-list {
  padding: 24px;
}

.doc-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.2s;
  border-left: 3px solid transparent;
}

.doc-item:hover {
  background: #f5f5f5;
}

.doc-item.active {
  background: #e6f7ff;
  border-left-color: #1890ff;
}

.doc-item-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.doc-icon {
  color: #1890ff;
  font-size: 18px;
  flex-shrink: 0;
}

.doc-info {
  min-width: 0;
}

.doc-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-meta {
  font-size: 11px;
  color: #999;
}

.doc-delete {
  color: #d4380d;
  opacity: 0;
  transition: opacity 0.2s;
  flex-shrink: 0;
}

.doc-item:hover .doc-delete {
  opacity: 1;
}

.no-doc {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.editor-header {
  font-size: 14px;
  font-weight: 500;
}

.doc-editor {
  font-family: 'Courier New', 'Monaco', monospace;
  font-size: 14px;
  line-height: 1.7;
  resize: none;
}

.doc-preview {
  padding: 16px;
  min-height: 500px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  background: white;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.8;
}

.split-view {
  display: flex;
  gap: 16px;
}

.split-editor,
.split-preview {
  flex: 1;
  min-width: 0;
}

.split-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 6px;
  font-weight: 500;
}

/* Markdown 样式 */
:deep(.markdown-body h1) { font-size: 24px; border-bottom: 1px solid #eee; padding-bottom: 8px; }
:deep(.markdown-body h2) { font-size: 20px; border-bottom: 1px solid #f0f0f0; padding-bottom: 6px; margin-top: 20px; }
:deep(.markdown-body h3) { font-size: 16px; margin-top: 16px; }
:deep(.markdown-body p) { margin: 8px 0; color: #444; }
:deep(.markdown-body ul) { padding-left: 24px; }
:deep(.markdown-body li) { margin: 4px 0; }
:deep(.markdown-body code) { background: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
:deep(.markdown-body pre) { background: #f8f8f8; padding: 16px; border-radius: 6px; overflow-x: auto; }
:deep(.markdown-body blockquote) { border-left: 4px solid #ddd; padding-left: 16px; color: #666; margin: 12px 0; }
:deep(.markdown-body table) { border-collapse: collapse; width: 100%; margin: 12px 0; }
:deep(.markdown-body th), :deep(.markdown-body td) { border: 1px solid #ddd; padding: 8px 12px; }
:deep(.markdown-body th) { background: #f5f5f5; font-weight: 600; }
</style>
