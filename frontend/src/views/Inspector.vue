<template>
  <div class="inspector-page">
    <a-row :gutter="24" style="height: 100%">
      <!-- 左侧输入区 -->
      <a-col :span="10">
        <a-card class="input-card" title="📝 输入内容">
          <template #extra>
            <a-badge :status="loading ? 'processing' : 'default'" :text="loading ? '质检中...' : '就绪'" />
          </template>

          <a-tabs v-model:activeKey="activeTab" @change="clearResult">
            <!-- 文本输入 Tab -->
            <a-tab-pane key="text" tab="📄 文本输入">
              <a-textarea
                v-model:value="inputText"
                :rows="16"
                placeholder="请输入催收通话文本内容，例如：&#10;&#10;您好，我是某某金融公司的催收专员，工号A001。&#10;请问您是张先生吗？关于您的贷款还款事宜..."
                :disabled="loading"
                class="text-input"
                allow-clear
              />
              <div class="text-stats">
                <span>{{ inputText.length }} 字符</span>
                <span style="margin-left: 16px">{{ inputText.split('\n').filter(l => l.trim()).length }} 行</span>
              </div>
            </a-tab-pane>

            <!-- 音频上传 Tab -->
            <a-tab-pane key="audio" tab="🎤 音频上传">
              <a-upload-dragger
                v-model:fileList="audioFiles"
                :before-upload="beforeAudioUpload"
                accept=".mp3,.wav,.m4a,.ogg"
                :max-count="1"
                :disabled="loading"
                class="audio-upload"
              >
                <p class="ant-upload-drag-icon">
                  <sound-outlined style="font-size: 48px; color: #1890ff" />
                </p>
                <p class="ant-upload-text">点击或拖拽音频文件到此区域</p>
                <p class="ant-upload-hint">支持 MP3、WAV、M4A 格式，系统将自动进行语音转文字</p>
              </a-upload-dragger>

              <!-- 已上传文件预览 -->
              <div v-if="audioFiles.length > 0" class="audio-preview">
                <a-alert
                  type="info"
                  :message="`已选择文件：${audioFiles[0]?.name}`"
                  show-icon
                />
              </div>
            </a-tab-pane>
          </a-tabs>

          <!-- 示例文本按钮 -->
          <div class="example-btns">
            <span style="font-size: 12px; color: #999; margin-right: 8px">示例：</span>
            <a-button size="small" @click="loadExample('good')" :disabled="loading">✅ 合规示例</a-button>
            <a-button size="small" @click="loadExample('bad')" style="margin-left: 8px" :disabled="loading">❌ 违规示例</a-button>
          </div>

          <!-- 开始质检按钮 -->
          <a-button
            type="primary"
            size="large"
            block
            :loading="loading"
            :disabled="!canInspect"
            @click="startInspect"
            class="inspect-btn"
          >
            <template #icon>
              <search-outlined />
            </template>
            {{ loading ? '质检中...' : '开始质检' }}
          </a-button>
        </a-card>
      </a-col>

      <!-- 右侧结果区 -->
      <a-col :span="14">
        <a-card class="result-card" title="📊 质检结果">
          <!-- 空状态 -->
          <div v-if="!result && !loading" class="empty-state">
            <a-empty
              :image="Empty.PRESENTED_IMAGE_SIMPLE"
              description="请在左侧输入文本或上传音频，点击「开始质检」"
            >
              <a-button type="primary" @click="loadExample('bad'); activeTab = 'text'">
                体验示例质检
              </a-button>
            </a-empty>
          </div>

          <!-- 加载状态 -->
          <div v-if="loading" class="loading-state">
            <a-spin size="large" />
            <p class="loading-text">{{ statusMessage || '正在分析通话内容...' }}</p>
            <a-progress :percent="loadingProgress" status="active" />
          </div>

          <!-- 质检结果 -->
          <div v-if="result && !loading" class="result-content">
            <!-- 评分区 -->
            <div class="score-section">
              <a-row align="middle" :gutter="24">
                <a-col :span="8" style="text-align: center">
                  <a-progress
                    type="circle"
                    :percent="result.score"
                    :stroke-color="scoreColor"
                    :format="() => `${result.score}`"
                    :width="120"
                  />
                  <div class="score-label">合规评分</div>
                </a-col>
                <a-col :span="16">
                  <a-statistic-countdown v-if="false" />
                  <div class="violation-stats">
                    <a-statistic-group>
                    </a-statistic-group>
                    <a-row :gutter="16">
                      <a-col :span="8">
                        <a-statistic
                          title="高严重度"
                          :value="violationCount.high"
                          :value-style="{ color: '#ff4d4f', fontSize: '28px' }"
                        />
                      </a-col>
                      <a-col :span="8">
                        <a-statistic
                          title="中严重度"
                          :value="violationCount.mid"
                          :value-style="{ color: '#fa8c16', fontSize: '28px' }"
                        />
                      </a-col>
                      <a-col :span="8">
                        <a-statistic
                          title="低严重度"
                          :value="violationCount.low"
                          :value-style="{ color: '#faad14', fontSize: '28px' }"
                        />
                      </a-col>
                    </a-row>
                  </div>
                  <div class="summary-text">
                    <a-alert :message="result.summary" :type="summaryAlertType" show-icon />
                  </div>
                </a-col>
              </a-row>
            </div>

            <a-divider />

            <!-- ASR 转录内容（如果是音频） -->
            <div v-if="result.asr_transcript" class="asr-section">
              <a-collapse>
                <a-collapse-panel key="asr" header="🎤 语音识别文本">
                  <p class="asr-text">{{ result.asr_transcript }}</p>
                </a-collapse-panel>
              </a-collapse>
              <a-divider />
            </div>

            <!-- 高亮文本区 -->
            <div class="highlight-section">
              <div class="section-title">📋 通话内容分析</div>
              <div class="highlight-container">
                <div
                  class="highlight-text"
                  v-html="highlightedText"
                />
              </div>
            </div>

            <a-divider />

            <!-- 违规详情列表 -->
            <div class="violations-section">
              <div class="section-title">
                🚨 违规详情
                <a-tag v-if="result.violations.length === 0" color="green">无违规</a-tag>
              </div>

              <div v-if="result.violations.length === 0" class="no-violation">
                <a-result status="success" title="通话内容合规" sub-title="未发现违规行为，继续保持！" />
              </div>

              <a-collapse v-else>
                <a-collapse-panel
                  v-for="(v, idx) in result.violations"
                  :key="idx"
                  :header="getPanelHeader(v)"
                >
                  <a-descriptions :column="1" size="small">
                    <a-descriptions-item label="违规句子">
                      <span class="violation-sentence">{{ v.sentence }}</span>
                    </a-descriptions-item>
                    <a-descriptions-item label="违反规则">{{ v.rule }}</a-descriptions-item>
                    <a-descriptions-item label="违规说明">{{ v.explanation }}</a-descriptions-item>
                  </a-descriptions>
                </a-collapse-panel>
              </a-collapse>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Empty, message } from 'ant-design-vue'
import type { UploadFile } from 'ant-design-vue'
import { SearchOutlined, SoundOutlined } from '@ant-design/icons-vue'
import { inspectText, inspectAudio, type InspectResult, type Violation } from '@/api'

const activeTab = ref('text')
const inputText = ref('')
const audioFiles = ref<UploadFile[]>([])
const loading = ref(false)
const result = ref<InspectResult | null>(null)
const statusMessage = ref('')
const loadingProgress = ref(0)

// 是否可以质检
const canInspect = computed(() => {
  if (activeTab.value === 'text') return inputText.value.trim().length > 0
  return audioFiles.value.length > 0
})

// 违规统计
const violationCount = computed(() => ({
  high: result.value?.violations.filter(v => v.severity === '高').length || 0,
  mid: result.value?.violations.filter(v => v.severity === '中').length || 0,
  low: result.value?.violations.filter(v => v.severity === '低').length || 0
}))

// 评分颜色
const scoreColor = computed(() => {
  const score = result.value?.score || 0
  if (score >= 80) return '#52c41a'
  if (score >= 60) return '#faad14'
  return '#ff4d4f'
})

// 总结提示类型
const summaryAlertType = computed(() => {
  const score = result.value?.score || 0
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'error'
})

// 高亮文本
const highlightedText = computed(() => {
  if (!result.value) return ''

  const text = result.value.original_text
  const violations = result.value.violations

  if (!violations.length) {
    return `<span style="white-space: pre-wrap">${escapeHtml(text)}</span>`
  }

  // 收集所有需要高亮的区间
  const highlights: Array<{ start: number; end: number; severity: string; rule: string; explanation: string }> = []

  for (const v of violations) {
    const idx = text.indexOf(v.sentence)
    if (idx !== -1) {
      highlights.push({
        start: idx,
        end: idx + v.sentence.length,
        severity: v.severity,
        rule: v.rule,
        explanation: v.explanation
      })
    }
  }

  // 排序，防止重叠
  highlights.sort((a, b) => a.start - b.start)

  let html = ''
  let lastEnd = 0

  for (const h of highlights) {
    if (h.start < lastEnd) continue // 跳过重叠区间

    // 添加普通文本
    html += `<span style="white-space: pre-wrap">${escapeHtml(text.slice(lastEnd, h.start))}</span>`

    // 添加高亮区间
    const color = h.severity === '高' ? '#fff2f0' : h.severity === '中' ? '#fff7e6' : '#fffbe6'
    const borderColor = h.severity === '高' ? '#ff4d4f' : h.severity === '中' ? '#fa8c16' : '#faad14'
    const tooltip = `${h.rule}：${h.explanation}`

    html += `<span
      class="highlight-span"
      style="background: ${color}; border-bottom: 2px solid ${borderColor}; cursor: pointer; padding: 1px 2px; border-radius: 2px"
      title="${escapeHtml(tooltip)}"
    >${escapeHtml(text.slice(h.start, h.end))}</span>`

    lastEnd = h.end
  }

  html += `<span style="white-space: pre-wrap">${escapeHtml(text.slice(lastEnd))}</span>`

  return html
})

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/\n/g, '<br/>')
}

function getPanelHeader(v: Violation) {
  const tagColor = v.severity === '高' ? 'red' : v.severity === '中' ? 'orange' : 'gold'
  return v.sentence.slice(0, 30) + (v.sentence.length > 30 ? '...' : '')
}

function clearResult() {
  result.value = null
}

function beforeAudioUpload(file: File) {
  audioFiles.value = [{ uid: '-1', name: file.name, originFileObj: file } as UploadFile]
  return false // 阻止自动上传
}

// 加载示例文本
function loadExample(type: 'good' | 'bad') {
  if (type === 'good') {
    inputText.value = `您好，我是某某金融公司的催收专员，工号A001。
请问您是张先生吗？我联系您是关于您2024年1月15日的5000元贷款还款事宜。
您的贷款已经逾期30天了，请问您什么时候方便还款？
我们可以为您提供分期还款方案，您有什么困难可以告诉我们，我们一起想办法解决。
另外，如果您有任何疑问，也可以拨打我们的客服热线400-xxx-xxxx进行投诉或咨询。`
  } else {
    inputText.value = `喂，你是张三吗？你欠了我们的钱，你知不知道？
你再不还款，我就让你坐牢！你这个骗子！
我要打电话给你们公司领导，让你在单位抬不起头！
你现在必须立刻还款，否则后果自负！
你这个废物，借钱不还，真是无赖！我们会派人上门找你！`
  }
  activeTab.value = 'text'
  result.value = null
}

// 开始质检
async function startInspect() {
  loading.value = true
  result.value = null
  statusMessage.value = '正在加载质检规则...'
  loadingProgress.value = 20

  try {
    if (activeTab.value === 'text') {
      statusMessage.value = '正在分析文本内容...'
      loadingProgress.value = 50

      const res = await inspectText(inputText.value)
      loadingProgress.value = 90
      statusMessage.value = `检测到 ${res.violations.length} 处违规...`

      await new Promise(r => setTimeout(r, 300))
      result.value = res
    } else {
      if (!audioFiles.value[0]?.originFileObj) {
        message.error('请先选择音频文件')
        return
      }

      statusMessage.value = '正在进行语音识别...'
      loadingProgress.value = 30

      const res = await inspectAudio(audioFiles.value[0].originFileObj as File)
      loadingProgress.value = 90
      statusMessage.value = `检测到 ${res.violations.length} 处违规...`

      await new Promise(r => setTimeout(r, 300))
      result.value = res
    }

    loadingProgress.value = 100

    if (result.value.violations.length === 0) {
      message.success('✅ 质检通过，未发现违规行为！')
    } else {
      message.warning(`⚠️ 发现 ${result.value.violations.length} 处违规，请查看详情`)
    }
  } catch (err: any) {
    message.error(`质检失败：${err.message}`)
  } finally {
    loading.value = false
    statusMessage.value = ''
    loadingProgress.value = 0
  }
}
</script>

<style scoped>
.inspector-page {
  height: 100%;
}

.input-card,
.result-card {
  height: calc(100vh - 64px - 70px - 48px);
  overflow: auto;
}

.text-input {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  resize: none;
}

.text-stats {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
  text-align: right;
}

.audio-upload {
  margin-bottom: 16px;
}

.audio-preview {
  margin-top: 12px;
}

.example-btns {
  margin: 12px 0;
  display: flex;
  align-items: center;
}

.inspect-btn {
  margin-top: 16px;
  height: 44px;
  font-size: 16px;
}

.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  gap: 16px;
}

.loading-text {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.score-section {
  padding: 8px 0;
}

.score-label {
  margin-top: 8px;
  color: #666;
  font-size: 13px;
}

.violation-stats {
  margin-bottom: 16px;
}

.summary-text {
  margin-top: 8px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.highlight-container {
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 16px;
  max-height: 200px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.8;
}

.highlight-text {
  white-space: pre-wrap;
  word-break: break-all;
}

.violations-section {
  margin-top: 4px;
}

.violation-sentence {
  font-style: italic;
  color: #d4380d;
  background: #fff2f0;
  padding: 2px 6px;
  border-radius: 4px;
}

.no-violation {
  margin: 16px 0;
}

.asr-text {
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #666;
}
</style>
