<template>
  <div class="inspector-page">
    <div class="inspector-grid">
      <!-- ─── 左：输入区 ─────────────────────────── -->
      <div class="panel input-panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-icon">📝</span> 输入内容
          </div>
          <div class="status-badge" :class="loading ? 'processing' : 'idle'">
            <span class="dot" />
            {{ loading ? '质检中' : '就绪' }}
          </div>
        </div>

        <!-- Tabs -->
        <div class="tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="tab-btn"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key; clearResult()"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- 文本输入 -->
        <div v-if="activeTab === 'text'" class="tab-body">
          <textarea
            v-model="inputText"
            class="text-input"
            :disabled="loading"
            placeholder="请输入催收通话文本内容，例如：

您好，我是某某金融公司的催收专员，工号A001。
请问您是张先生吗？关于您的贷款还款事宜..."
          />
          <div class="text-meta">
            <span>{{ inputText.length }} 字符</span>
            <span>{{ inputText.split('\n').filter(l => l.trim()).length }} 行</span>
          </div>
        </div>

        <!-- 音频上传 -->
        <div v-if="activeTab === 'audio'" class="tab-body">
          <a-upload-dragger
            v-model:fileList="audioFiles"
            :before-upload="beforeAudioUpload"
            accept=".mp3,.wav,.m4a,.ogg"
            :max-count="1"
            :disabled="loading"
            class="audio-upload"
          >
            <p class="ant-upload-drag-icon">
              <sound-outlined style="font-size: 44px; color: var(--accent)" />
            </p>
            <p class="upload-text">点击或拖拽音频文件</p>
            <p class="upload-hint">支持 MP3 / WAV / M4A，将自动进行语音识别</p>
          </a-upload-dragger>
          <div v-if="audioFiles.length > 0" class="audio-info">
            <span>🎵</span>
            <span>{{ audioFiles[0]?.name }}</span>
          </div>
        </div>

        <!-- 示例按钮 -->
        <div class="example-row">
          <span class="example-label">快速示例</span>
          <button class="example-btn safe" @click="loadExample('good')" :disabled="loading">✅ 合规</button>
          <button class="example-btn danger" @click="loadExample('bad')" :disabled="loading">❌ 违规</button>
        </div>

        <!-- 开始质检 -->
        <button
          class="inspect-btn"
          :class="{ loading, disabled: !canInspect }"
          :disabled="!canInspect || loading"
          @click="startInspect"
        >
          <span v-if="loading" class="btn-spinner" />
          <search-outlined v-else />
          {{ loading ? '质检中...' : '开始质检' }}
        </button>
      </div>

      <!-- ─── 右：结果区 ─────────────────────────── -->
      <div class="panel result-panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-icon">📊</span> 质检结果
          </div>
        </div>

        <!-- 空态 -->
        <div v-if="!result && !loading" class="empty-state">
          <div class="empty-icon">🔍</div>
          <p class="empty-text">请输入内容并点击「开始质检」</p>
          <button class="ghost-btn" @click="loadExample('bad'); activeTab = 'text'">体验示例质检</button>
        </div>

        <!-- 加载中 -->
        <div v-if="loading" class="loading-state">
          <div class="loading-ring" />
          <p class="loading-text">{{ statusMessage || '正在分析通话内容...' }}</p>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: loadingProgress + '%' }" />
          </div>
        </div>

        <!-- 结果 -->
        <div v-if="result && !loading" class="result-body">
          <!-- 评分卡 -->
          <div class="score-card">
            <div class="score-ring-wrap">
              <a-progress
                type="circle"
                :percent="result.score"
                :stroke-color="scoreColor"
                :trail-color="'rgba(255,255,255,.08)'"
                :format="() => String(result!.score)"
                :width="110"
              />
              <div class="score-label">合规评分</div>
            </div>
            <div class="score-stats">
              <div class="stat-item high">
                <div class="stat-val">{{ violationCount.high }}</div>
                <div class="stat-name">高严重度</div>
              </div>
              <div class="stat-item mid">
                <div class="stat-val">{{ violationCount.mid }}</div>
                <div class="stat-name">中严重度</div>
              </div>
              <div class="stat-item low">
                <div class="stat-val">{{ violationCount.low }}</div>
                <div class="stat-name">低严重度</div>
              </div>
            </div>
            <div class="summary-alert" :class="summaryAlertType">
              {{ result.summary }}
            </div>
          </div>

          <!-- ASR 转录 -->
          <details v-if="result.asr_transcript" class="asr-block">
            <summary>🎤 语音识别文本</summary>
            <p class="asr-text">{{ result.asr_transcript }}</p>
          </details>

          <!-- 高亮文本 -->
          <div class="section">
            <div class="section-title">📋 通话内容分析</div>
            <div class="highlight-box" v-html="highlightedText" />
          </div>

          <!-- 违规详情 -->
          <div class="section">
            <div class="section-title">
              🚨 违规详情
              <span v-if="result.violations.length === 0" class="tag-safe">无违规</span>
            </div>

            <div v-if="result.violations.length === 0" class="all-clear">
              <span class="all-clear-icon">✅</span>
              <div>
                <div class="all-clear-title">通话内容合规</div>
                <div class="all-clear-sub">未发现违规行为，继续保持！</div>
              </div>
            </div>

            <div v-else class="violation-list">
              <details
                v-for="(v, idx) in result.violations"
                :key="idx"
                class="violation-item"
                :class="'sev-' + severityKey(v.severity)"
              >
                <summary class="violation-summary">
                  <span class="sev-tag">{{ v.severity }}</span>
                  <span class="violation-preview">{{ v.sentence.slice(0, 35) }}{{ v.sentence.length > 35 ? '…' : '' }}</span>
                </summary>
                <div class="violation-detail">
                  <div class="detail-row"><span class="detail-key">违规句子</span><span class="violation-sentence">{{ v.sentence }}</span></div>
                  <div class="detail-row"><span class="detail-key">违反规则</span><span>{{ v.rule }}</span></div>
                  <div class="detail-row"><span class="detail-key">违规说明</span><span>{{ v.explanation }}</span></div>
                </div>
              </details>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import type { UploadFile } from 'ant-design-vue'
import { SearchOutlined, SoundOutlined } from '@ant-design/icons-vue'
import { inspectText, inspectAudio, type InspectResult, type Violation } from '@/api'

const tabs = [
  { key: 'text',  label: '📄 文本输入' },
  { key: 'audio', label: '🎤 音频上传' },
]

const activeTab = ref('text')
const inputText = ref('')
const audioFiles = ref<UploadFile[]>([])
const loading = ref(false)
const result = ref<InspectResult | null>(null)
const statusMessage = ref('')
const loadingProgress = ref(0)

const canInspect = computed(() =>
  activeTab.value === 'text' ? inputText.value.trim().length > 0 : audioFiles.value.length > 0
)

const violationCount = computed(() => ({
  high: result.value?.violations.filter(v => v.severity === '高').length || 0,
  mid:  result.value?.violations.filter(v => v.severity === '中').length || 0,
  low:  result.value?.violations.filter(v => v.severity === '低').length || 0,
}))

const scoreColor = computed(() => {
  const s = result.value?.score || 0
  if (s >= 80) return '#3fb950'
  if (s >= 60) return '#e3b341'
  return '#f85149'
})

const summaryAlertType = computed(() => {
  const s = result.value?.score || 0
  if (s >= 80) return 'safe'
  if (s >= 60) return 'warn'
  return 'danger'
})

const highlightedText = computed(() => {
  if (!result.value) return ''
  const text = result.value.original_text
  const violations = result.value.violations
  if (!violations.length) return `<span>${escapeHtml(text)}</span>`

  const highlights = violations
    .map(v => { const i = text.indexOf(v.sentence); return i !== -1 ? { start: i, end: i + v.sentence.length, severity: v.severity, rule: v.rule, explanation: v.explanation } : null })
    .filter(Boolean)
    .sort((a, b) => a!.start - b!.start) as { start: number; end: number; severity: string; rule: string; explanation: string }[]

  let html = '', lastEnd = 0
  for (const h of highlights) {
    if (h.start < lastEnd) continue
    html += `<span>${escapeHtml(text.slice(lastEnd, h.start))}</span>`
    const cls = h.severity === '高' ? 'hl-high' : h.severity === '中' ? 'hl-mid' : 'hl-low'
    html += `<span class="hl ${cls}" title="${escapeHtml(h.rule + '：' + h.explanation)}">${escapeHtml(text.slice(h.start, h.end))}</span>`
    lastEnd = h.end
  }
  html += `<span>${escapeHtml(text.slice(lastEnd))}</span>`
  return html
})

function escapeHtml(t: string) {
  return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;').replace(/\n/g,'<br/>')
}

function severityKey(s: string) {
  return s === '高' ? 'high' : s === '中' ? 'mid' : 'low'
}

function clearResult() { result.value = null }

function beforeAudioUpload(file: File) {
  audioFiles.value = [{ uid: '-1', name: file.name, originFileObj: file } as UploadFile]
  return false
}

function loadExample(type: 'good' | 'bad') {
  inputText.value = type === 'good'
    ? `您好，我是某某金融公司的催收专员，工号A001。\n请问您是张先生吗？我联系您是关于您2024年1月15日的5000元贷款还款事宜。\n您的贷款已经逾期30天了，请问您什么时候方便还款？\n我们可以为您提供分期还款方案，您有什么困难可以告诉我们，我们一起想办法解决。\n另外，如果您有任何疑问，也可以拨打我们的客服热线400-xxx-xxxx进行投诉或咨询。`
    : `喂，你是张三吗？你欠了我们的钱，你知不知道？\n你再不还款，我就让你坐牢！你这个骗子！\n我要打电话给你们公司领导，让你在单位抬不起头！\n你现在必须立刻还款，否则后果自负！\n你这个废物，借钱不还，真是无赖！我们会派人上门找你！`
  activeTab.value = 'text'
  result.value = null
}

async function startInspect() {
  loading.value = true; result.value = null
  statusMessage.value = '正在加载质检规则...'; loadingProgress.value = 20
  try {
    if (activeTab.value === 'text') {
      statusMessage.value = '正在分析文本内容...'; loadingProgress.value = 50
      const res = await inspectText(inputText.value)
      loadingProgress.value = 90
      statusMessage.value = `检测到 ${res.violations.length} 处违规...`
      await new Promise(r => setTimeout(r, 300))
      result.value = res
    } else {
      if (!audioFiles.value[0]?.originFileObj) { message.error('请先选择音频文件'); return }
      statusMessage.value = '正在进行语音识别...'; loadingProgress.value = 30
      const res = await inspectAudio(audioFiles.value[0].originFileObj as File)
      loadingProgress.value = 90
      statusMessage.value = `检测到 ${res.violations.length} 处违规...`
      await new Promise(r => setTimeout(r, 300))
      result.value = res
    }
    loadingProgress.value = 100
    result.value!.violations.length === 0
      ? message.success('✅ 质检通过，未发现违规行为！')
      : message.warning(`⚠️ 发现 ${result.value!.violations.length} 处违规`)
  } catch (err: any) {
    message.error(`质检失败：${err.message}`)
  } finally {
    loading.value = false; statusMessage.value = ''; loadingProgress.value = 0
  }
}
</script>

<style scoped>
/* ─── Layout ─────────────────────────────────────── */
.inspector-page { height: 100%; }

.inspector-grid {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 16px;
  height: calc(100vh - 60px - 40px - 40px);
}

/* ─── Panel ──────────────────────────────────────── */
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-icon { font-size: 16px; }

.status-badge {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 12px;
}
.status-badge .dot {
  width: 6px; height: 6px; border-radius: 50%;
}
.status-badge.idle { color: var(--text-muted); background: var(--surface-2); }
.status-badge.idle .dot { background: var(--text-dim); }
.status-badge.processing { color: var(--info); background: rgba(88,166,255,.1); }
.status-badge.processing .dot { background: var(--info); animation: pulse 1s infinite; }

/* ─── Tabs ───────────────────────────────────────── */
.tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color var(--transition), border-color var(--transition);
}
.tab-btn:hover { color: var(--text); }
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }

/* ─── Tab Body ───────────────────────────────────── */
.tab-body {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.text-input {
  flex: 1;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-size: 13.5px;
  font-family: 'SF Mono', 'Courier New', monospace;
  line-height: 1.7;
  padding: 12px;
  resize: none;
  outline: none;
  transition: border-color var(--transition), box-shadow var(--transition);
  min-height: 0;
}
.text-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(210,170,90,.15);
}
.text-input::placeholder { color: var(--text-dim); }

.text-meta {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  font-size: 11px;
  color: var(--text-dim);
  margin-top: 6px;
}

.audio-upload { margin-bottom: 10px; }

.upload-text { color: var(--text); font-size: 14px; margin: 6px 0 4px; }
.upload-hint { color: var(--text-muted); font-size: 12px; }

.audio-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--surface-2);
  border-radius: var(--radius);
  font-size: 13px;
  color: var(--text-muted);
}

/* ─── Example / Inspect Buttons ──────────────────── */
.example-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px 10px;
  flex-shrink: 0;
}

.example-label { font-size: 12px; color: var(--text-dim); }

.example-btn {
  padding: 3px 12px;
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
  border: 1px solid;
  transition: filter var(--transition);
  background: transparent;
}
.example-btn:hover { filter: brightness(1.2); }
.example-btn:disabled { opacity: .4; cursor: not-allowed; }
.example-btn.safe  { color: var(--safe); border-color: rgba(63,185,80,.4); }
.example-btn.danger { color: var(--danger); border-color: rgba(248,81,73,.4); }

.inspect-btn {
  margin: 0 16px 16px;
  padding: 12px;
  background: linear-gradient(135deg, var(--accent), #a07830);
  border: none;
  border-radius: var(--radius);
  color: #0d1117;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: filter var(--transition), transform .1s;
  flex-shrink: 0;
  letter-spacing: .3px;
}
.inspect-btn:hover:not(.disabled) { filter: brightness(1.1); transform: translateY(-1px); }
.inspect-btn:active:not(.disabled) { transform: translateY(0); }
.inspect-btn.disabled { background: var(--surface-2); color: var(--text-dim); cursor: not-allowed; }

.btn-spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(0,0,0,.3);
  border-top-color: #0d1117;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ─── Result Panel ───────────────────────────────── */
.result-panel { overflow-y: auto; }

.empty-state, .loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 12px;
  padding: 40px;
}

.empty-icon { font-size: 52px; opacity: .3; }
.empty-text { color: var(--text-muted); font-size: 14px; }

.ghost-btn {
  padding: 6px 16px;
  border: 1px solid var(--border-glow);
  border-radius: 20px;
  background: transparent;
  color: var(--accent);
  font-size: 13px;
  cursor: pointer;
  transition: background var(--transition);
}
.ghost-btn:hover { background: var(--accent-soft); }

.loading-ring {
  width: 44px; height: 44px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin .8s linear infinite;
}

.loading-text { color: var(--text-muted); font-size: 14px; }

.progress-bar {
  width: 200px; height: 4px;
  background: var(--surface-2);
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #f0c060);
  border-radius: 2px;
  transition: width .3s;
}

/* ─── Score Card ─────────────────────────────────── */
.result-body {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.score-card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.score-ring-wrap {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.score-label { font-size: 12px; color: var(--text-muted); margin-top: 6px; text-align: center; }

.score-stats {
  display: flex;
  gap: 24px;
  flex: 1;
}

.stat-item { text-align: center; }
.stat-val { font-size: 28px; font-weight: 700; line-height: 1; margin-bottom: 4px; }
.stat-name { font-size: 11px; color: var(--text-muted); }
.stat-item.high .stat-val { color: var(--danger); }
.stat-item.mid  .stat-val { color: var(--warn); }
.stat-item.low  .stat-val { color: var(--accent); }

.summary-alert {
  padding: 10px 14px;
  border-radius: var(--radius);
  font-size: 13px;
  border: 1px solid;
}
.summary-alert.safe   { background: rgba(63,185,80,.1);  border-color: rgba(63,185,80,.3);  color: var(--safe); }
.summary-alert.warn   { background: rgba(227,179,65,.1); border-color: rgba(227,179,65,.3); color: var(--warn); }
.summary-alert.danger { background: rgba(248,81,73,.1);  border-color: rgba(248,81,73,.3);  color: var(--danger); }

/* ─── ASR ────────────────────────────────────────── */
.asr-block {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.asr-block summary {
  padding: 10px 16px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-muted);
  list-style: none;
  user-select: none;
}
.asr-block summary:hover { color: var(--text); }
.asr-text {
  padding: 12px 16px;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: var(--text-muted);
  white-space: pre-wrap;
  border-top: 1px solid var(--border);
}

/* ─── Sections ───────────────────────────────────── */
.section { display: flex; flex-direction: column; gap: 10px; }

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag-safe {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(63,185,80,.15);
  color: var(--safe);
  border-radius: 10px;
  font-weight: 400;
}

.highlight-box {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 16px;
  font-size: 13.5px;
  line-height: 1.9;
  max-height: 180px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

:deep(.hl) { cursor: pointer; padding: 1px 2px; border-radius: 3px; border-bottom: 2px solid; }
:deep(.hl-high) { background: rgba(248,81,73,.15); border-color: var(--danger); }
:deep(.hl-mid)  { background: rgba(227,179,65,.15); border-color: var(--warn); }
:deep(.hl-low)  { background: rgba(210,170,90,.15); border-color: var(--accent); }

/* ─── All Clear ──────────────────────────────────── */
.all-clear {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: rgba(63,185,80,.08);
  border: 1px solid rgba(63,185,80,.25);
  border-radius: var(--radius);
}
.all-clear-icon { font-size: 32px; }
.all-clear-title { font-size: 15px; font-weight: 600; color: var(--safe); }
.all-clear-sub { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

/* ─── Violation List ─────────────────────────────── */
.violation-list { display: flex; flex-direction: column; gap: 8px; }

.violation-item {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.violation-item.sev-high { border-left: 3px solid var(--danger); }
.violation-item.sev-mid  { border-left: 3px solid var(--warn); }
.violation-item.sev-low  { border-left: 3px solid var(--accent); }

.violation-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  list-style: none;
  user-select: none;
}
.violation-summary:hover { background: rgba(255,255,255,.03); }

.sev-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
  flex-shrink: 0;
}
.sev-high .sev-tag { background: rgba(248,81,73,.2); color: var(--danger); }
.sev-mid  .sev-tag { background: rgba(227,179,65,.2); color: var(--warn); }
.sev-low  .sev-tag { background: rgba(210,170,90,.2); color: var(--accent); }

.violation-preview { font-size: 13px; color: var(--text-muted); }

.violation-detail {
  padding: 10px 14px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-top: 1px solid var(--border);
}

.detail-row {
  display: flex;
  gap: 10px;
  font-size: 13px;
}
.detail-key {
  color: var(--text-dim);
  flex-shrink: 0;
  width: 64px;
}

.violation-sentence {
  color: var(--danger);
  font-style: italic;
  background: rgba(248,81,73,.08);
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
