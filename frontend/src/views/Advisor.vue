<template>
  <div class="advisor-page">
    <a-card class="chat-card" :body-style="{ padding: 0, display: 'flex', flexDirection: 'column', height: '100%' }">
      <!-- 顶部标题栏 -->
      <div class="chat-header">
        <div class="chat-title">
          <a-avatar :size="40" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
            📋
          </a-avatar>
          <div class="chat-title-text">
            <div class="chat-name">制度答疑官</div>
            <div class="chat-desc">基于合规规则文档，为您解答催收合规问题</div>
          </div>
        </div>
        <div class="chat-actions">
          <a-tooltip title="清空对话">
            <a-button type="text" danger :icon="h(DeleteOutlined)" @click="clearHistory">
              清空
            </a-button>
          </a-tooltip>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesRef">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-section">
          <div class="welcome-avatar">📋</div>
          <div class="welcome-title">您好！我是制度答疑官</div>
          <div class="welcome-desc">我可以为您解答催收合规相关问题，请问您有什么想了解的？</div>
          
          <div class="quick-questions">
            <div class="quick-title">💡 常见问题</div>
            <div class="quick-list">
              <a-button
                v-for="q in quickQuestions"
                :key="q"
                size="small"
                class="quick-btn"
                @click="sendQuickQuestion(q)"
              >
                {{ q }}
              </a-button>
            </div>
          </div>
        </div>

        <!-- 消息气泡 -->
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="message-item"
          :class="msg.role === 'user' ? 'user-message' : 'ai-message'"
        >
          <!-- AI 消息 -->
          <template v-if="msg.role === 'assistant'">
            <a-avatar :size="36" class="msg-avatar" style="background: linear-gradient(135deg, #667eea, #764ba2)">
              📋
            </a-avatar>
            <div class="msg-bubble ai-bubble">
              <div class="msg-content markdown-body" v-html="renderMarkdown(msg.content)" />
              <div class="msg-time">{{ msg.time }}</div>
            </div>
          </template>

          <!-- 用户消息 -->
          <template v-else>
            <div class="msg-bubble user-bubble">
              <div class="msg-content">{{ msg.content }}</div>
              <div class="msg-time">{{ msg.time }}</div>
            </div>
            <a-avatar :size="36" class="msg-avatar" style="background: #1890ff">
              👤
            </a-avatar>
          </template>
        </div>

        <!-- 加载中 (打字动画) -->
        <div v-if="isTyping" class="message-item ai-message">
          <a-avatar :size="36" class="msg-avatar" style="background: linear-gradient(135deg, #667eea, #764ba2)">
            📋
          </a-avatar>
          <div class="msg-bubble ai-bubble typing-bubble">
            <div class="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部输入区 -->
      <div class="chat-input-area">
        <div class="input-wrapper">
          <a-textarea
            v-model:value="inputText"
            :placeholder="'请输入您的问题，例如：联系借款人的时间限制是什么？'"
            :rows="3"
            :disabled="isTyping"
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.enter.shift.exact="() => {}"
            class="chat-input"
            allow-clear
          />
          <div class="input-actions">
            <span class="input-hint">Enter 发送，Shift+Enter 换行</span>
            <a-button
              type="primary"
              :loading="isTyping"
              :disabled="!inputText.trim()"
              @click="sendMessage"
              class="send-btn"
            >
              <template #icon>
                <send-outlined />
              </template>
              发送
            </a-button>
          </div>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, h } from 'vue'
import { message } from 'ant-design-vue'
import { DeleteOutlined, SendOutlined } from '@ant-design/icons-vue'
import { marked } from 'marked'
import type { Message } from '@/api'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  time: string
}

const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const isTyping = ref(false)
const messagesRef = ref<HTMLElement>()

const quickQuestions = [
  '催收联系时段有什么规定？',
  '什么行为属于威胁恐吓？',
  '侮辱性语言有哪些？',
  '通话开场白应该怎么说？',
  '借款人拒还款怎么处理？',
  '如何提供分期还款方案？'
]

// 获取当前时间
function getTime() {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// Markdown 渲染
function renderMarkdown(text: string): string {
  try {
    return marked(text) as string
  } catch {
    return text
  }
}

// 滚动到底部
async function scrollToBottom() {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

// 发送快捷问题
function sendQuickQuestion(q: string) {
  inputText.value = q
  sendMessage()
}

// 清空对话
function clearHistory() {
  messages.value = []
}

// 发送消息
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isTyping.value) return

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: text,
    time: getTime()
  })

  inputText.value = ''
  isTyping.value = true
  await scrollToBottom()

  // 构建历史记录
  const history: Message[] = messages.value
    .slice(0, -1)
    .map(m => ({ role: m.role, content: m.content }))

  // 添加 AI 消息占位
  const aiMsgIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    time: getTime()
  })

  try {
    // 使用 WebSocket 流式输出
    const ws = new WebSocket(`ws://${location.host}/ws/advisor`)

    ws.onopen = () => {
      ws.send(JSON.stringify({ question: text, history }))
    }

    ws.onmessage = async (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'chunk') {
        messages.value[aiMsgIndex].content += data.content
        await scrollToBottom()
      } else if (data.type === 'done') {
        ws.close()
        isTyping.value = false
        await scrollToBottom()
      } else if (data.type === 'error') {
        message.error(`错误：${data.message}`)
        ws.close()
        isTyping.value = false
      }
    }

    ws.onerror = async () => {
      // 降级到 REST API
      try {
        const { chatWithAdvisor } = await import('@/api')
        const answer = await chatWithAdvisor(text, history)
        messages.value[aiMsgIndex].content = answer
      } catch (err: any) {
        messages.value[aiMsgIndex].content = `请求失败：${err.message}`
      }
      isTyping.value = false
      await scrollToBottom()
    }

    ws.onclose = () => {
      if (isTyping.value) {
        isTyping.value = false
      }
    }

  } catch (err: any) {
    messages.value[aiMsgIndex].content = `请求失败：${err.message}`
    isTyping.value = false
    await scrollToBottom()
  }
}
</script>

<style scoped>
.advisor-page {
  height: calc(100vh - 64px - 70px - 48px);
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.ant-card-body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0 !important;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-title-text {
  display: flex;
  flex-direction: column;
}

.chat-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.chat-desc {
  font-size: 12px;
  color: #888;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f5f5;
}

.welcome-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  text-align: center;
}

.welcome-avatar {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.welcome-desc {
  font-size: 14px;
  color: #888;
  margin-bottom: 32px;
}

.quick-questions {
  width: 100%;
  max-width: 600px;
}

.quick-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
  text-align: left;
}

.quick-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-btn {
  background: white;
  border-radius: 16px;
  cursor: pointer;
}

.message-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 10px;
}

.user-message {
  flex-direction: row-reverse;
}

.msg-avatar {
  flex-shrink: 0;
  font-size: 18px;
  line-height: 1;
}

.msg-bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 12px;
  position: relative;
}

.ai-bubble {
  background: white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  border-radius: 0 12px 12px 12px;
}

.user-bubble {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-radius: 12px 0 12px 12px;
}

.msg-content {
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.msg-time {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.3);
  margin-top: 6px;
  text-align: right;
}

.user-bubble .msg-time {
  color: rgba(255, 255, 255, 0.6);
}

/* 打字动画 */
.typing-bubble {
  padding: 16px;
}

.typing-dots {
  display: flex;
  gap: 6px;
  align-items: center;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9ca3af;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(1) { animation-delay: 0s; }
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.4; }
  40% { transform: scale(1.2); opacity: 1; }
}

/* 输入区 */
.chat-input-area {
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
  background: white;
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-input {
  resize: none;
  border-radius: 8px;
}

.input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.input-hint {
  font-size: 12px;
  color: #bbb;
}

.send-btn {
  border-radius: 8px;
}

/* Markdown 样式 */
:deep(.markdown-body) {
  font-size: 14px;
  line-height: 1.7;
}

:deep(.markdown-body h1),
:deep(.markdown-body h2),
:deep(.markdown-body h3) {
  font-size: 15px;
  margin: 8px 0 4px;
  font-weight: 600;
}

:deep(.markdown-body p) {
  margin: 4px 0;
}

:deep(.markdown-body ul),
:deep(.markdown-body ol) {
  padding-left: 20px;
  margin: 4px 0;
}

:deep(.markdown-body li) {
  margin: 2px 0;
}

:deep(.markdown-body code) {
  background: #f5f5f5;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 13px;
}

:deep(.markdown-body pre) {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

:deep(.markdown-body blockquote) {
  border-left: 4px solid #ddd;
  padding-left: 12px;
  color: #666;
  margin: 8px 0;
}

:deep(.markdown-body strong) {
  font-weight: 600;
  color: #333;
}

:deep(.markdown-body hr) {
  border: none;
  border-top: 1px solid #eee;
  margin: 12px 0;
}

:deep(.markdown-body table) {
  border-collapse: collapse;
  width: 100%;
  font-size: 13px;
}

:deep(.markdown-body th),
:deep(.markdown-body td) {
  border: 1px solid #ddd;
  padding: 6px 12px;
}

:deep(.markdown-body th) {
  background: #f5f5f5;
}
</style>
