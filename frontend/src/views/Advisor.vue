<template>
  <div class="advisor-page">
    <div class="chat-shell">
      <!-- Header -->
      <div class="chat-header">
        <div class="advisor-identity">
          <div class="advisor-avatar">📋</div>
          <div>
            <div class="advisor-name">制度答疑官</div>
            <div class="advisor-desc">基于合规规则文档，实时解答催收合规问题</div>
          </div>
        </div>
        <button class="clear-btn" @click="clearHistory" title="清空对话">
          🗑 清空
        </button>
      </div>

      <!-- Messages -->
      <div class="messages" ref="messagesRef">
        <!-- Welcome -->
        <div v-if="messages.length === 0" class="welcome">
          <div class="welcome-avatar">📋</div>
          <div class="welcome-title">您好！我是制度答疑官</div>
          <div class="welcome-sub">我可以为您解答催收合规相关问题，请问有什么想了解的？</div>
          <div class="quick-panel">
            <div class="quick-label">💡 常见问题</div>
            <div class="quick-grid">
              <button
                v-for="q in quickQuestions"
                :key="q"
                class="quick-chip"
                @click="sendQuickQuestion(q)"
              >{{ q }}</button>
            </div>
          </div>
        </div>

        <!-- Message bubbles -->
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="msg-row"
          :class="msg.role"
        >
          <div v-if="msg.role === 'assistant'" class="msg-avatar ai-avatar">📋</div>
          <div class="msg-bubble" :class="msg.role">
            <div class="msg-content markdown-body" v-html="renderMarkdown(msg.content)" />
            <div class="msg-time">{{ msg.time }}</div>
          </div>
          <div v-if="msg.role === 'user'" class="msg-avatar user-avatar">👤</div>
        </div>

        <!-- Typing indicator -->
        <div v-if="isTyping" class="msg-row assistant">
          <div class="msg-avatar ai-avatar">📋</div>
          <div class="msg-bubble assistant typing-bubble">
            <div class="dots">
              <span /><span /><span />
            </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="input-bar">
        <textarea
          v-model="inputText"
          class="chat-input"
          placeholder="请输入您的问题，例如：联系借款人的时间限制是什么？"
          :disabled="isTyping"
          rows="3"
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.enter.shift.exact="() => {}"
        />
        <div class="input-footer">
          <span class="input-hint">Enter 发送 · Shift+Enter 换行</span>
          <button
            class="send-btn"
            :class="{ loading: isTyping }"
            :disabled="!inputText.trim() || isTyping"
            @click="sendMessage"
          >
            <span v-if="isTyping" class="spin-icon" />
            <span v-else>发送 ›</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import { marked } from 'marked'
import type { Message } from '@/api'

interface ChatMessage { role: 'user' | 'assistant'; content: string; time: string }

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
  '如何提供分期还款方案？',
]

function getTime() { return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }

function renderMarkdown(text: string) {
  try { return marked(text) as string } catch { return text }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
}

function sendQuickQuestion(q: string) { inputText.value = q; sendMessage() }
function clearHistory() { messages.value = [] }

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isTyping.value) return

  messages.value.push({ role: 'user', content: text, time: getTime() })
  inputText.value = ''
  isTyping.value = true
  await scrollToBottom()

  const history: Message[] = messages.value.slice(0, -1).map(m => ({ role: m.role, content: m.content }))
  const aiIdx = messages.value.length
  messages.value.push({ role: 'assistant', content: '', time: getTime() })

  try {
    const ws = new WebSocket(`ws://${location.host}/ws/advisor`)
    ws.onopen = () => ws.send(JSON.stringify({ question: text, history }))
    ws.onmessage = async (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'chunk') { messages.value[aiIdx].content += data.content; await scrollToBottom() }
      else if (data.type === 'done') { ws.close(); isTyping.value = false; await scrollToBottom() }
      else if (data.type === 'error') { message.error(`错误：${data.message}`); ws.close(); isTyping.value = false }
    }
    ws.onerror = async () => {
      try {
        const { chatWithAdvisor } = await import('@/api')
        messages.value[aiIdx].content = await chatWithAdvisor(text, history)
      } catch (e: any) { messages.value[aiIdx].content = `请求失败：${e.message}` }
      isTyping.value = false; await scrollToBottom()
    }
    ws.onclose = () => { if (isTyping.value) isTyping.value = false }
  } catch (e: any) {
    messages.value[aiIdx].content = `请求失败：${e.message}`
    isTyping.value = false; await scrollToBottom()
  }
}
</script>

<style scoped>
.advisor-page {
  height: calc(100vh - 60px - 40px - 40px);
  display: flex;
}

.chat-shell {
  flex: 1;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ─── Header ─────────────────────────────────────── */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(to right, rgba(210,170,90,.06), transparent);
  flex-shrink: 0;
}

.advisor-identity {
  display: flex;
  align-items: center;
  gap: 12px;
}

.advisor-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2d3748, #1a202c);
  border: 1px solid var(--border-glow);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 2px 8px rgba(210,170,90,.15);
}

.advisor-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.advisor-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.clear-btn {
  padding: 5px 12px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  transition: color var(--transition), border-color var(--transition);
}
.clear-btn:hover { color: var(--danger); border-color: rgba(248,81,73,.4); }

/* ─── Messages ───────────────────────────────────── */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: var(--bg);
}

/* Welcome */
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 32px 20px;
  gap: 8px;
}

.welcome-avatar { font-size: 56px; margin-bottom: 8px; }

.welcome-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}

.welcome-sub {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 20px;
}

.quick-panel { width: 100%; max-width: 560px; }

.quick-label {
  font-size: 13px;
  color: var(--text-dim);
  margin-bottom: 10px;
  text-align: left;
}

.quick-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-chip {
  padding: 6px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  transition: border-color var(--transition), color var(--transition);
}
.quick-chip:hover { border-color: var(--accent); color: var(--accent); }

/* Bubbles */
.msg-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.msg-row.user { flex-direction: row-reverse; }

.msg-avatar {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.ai-avatar   { background: var(--surface); border: 1px solid var(--border-glow); }
.user-avatar { background: var(--surface-2); border: 1px solid var(--border); }

.msg-bubble {
  max-width: 72%;
  padding: 12px 16px;
  border-radius: 12px;
}

.msg-bubble.assistant {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 0 12px 12px 12px;
}

.msg-bubble.user {
  background: linear-gradient(135deg, rgba(210,170,90,.25), rgba(160,120,48,.25));
  border: 1px solid var(--border-glow);
  border-radius: 12px 0 12px 12px;
}

.msg-content { font-size: 14px; line-height: 1.7; word-break: break-word; }

.msg-time {
  font-size: 11px;
  color: var(--text-dim);
  margin-top: 6px;
  text-align: right;
}

/* Typing */
.typing-bubble { padding: 14px 16px; }
.dots { display: flex; gap: 5px; align-items: center; }
.dots span {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--text-dim);
  animation: bounce 1.4s infinite ease-in-out;
}
.dots span:nth-child(1) { animation-delay: 0s; }
.dots span:nth-child(2) { animation-delay: .2s; }
.dots span:nth-child(3) { animation-delay: .4s; }
@keyframes bounce {
  0%,80%,100% { transform: scale(.7); opacity: .4; }
  40% { transform: scale(1.1); opacity: 1; }
}

/* ─── Input ──────────────────────────────────────── */
.input-bar {
  padding: 12px 16px;
  border-top: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
}

.chat-input {
  width: 100%;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-size: 14px;
  line-height: 1.6;
  padding: 10px 14px;
  resize: none;
  outline: none;
  font-family: inherit;
  transition: border-color var(--transition);
}
.chat-input:focus { border-color: var(--accent); }
.chat-input::placeholder { color: var(--text-dim); }

.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.input-hint { font-size: 11px; color: var(--text-dim); }

.send-btn {
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
  transition: filter var(--transition);
}
.send-btn:hover:not(:disabled) { filter: brightness(1.1); }
.send-btn:disabled { opacity: .4; cursor: not-allowed; }

.spin-icon {
  width: 14px; height: 14px;
  border: 2px solid rgba(0,0,0,.3);
  border-top-color: #0d1117;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ─── Markdown ───────────────────────────────────── */
:deep(.markdown-body) { font-size: 14px; line-height: 1.7; }
:deep(.markdown-body h1),:deep(.markdown-body h2),:deep(.markdown-body h3) { font-size: 15px; margin: 8px 0 4px; font-weight: 600; color: var(--text); }
:deep(.markdown-body p) { margin: 4px 0; }
:deep(.markdown-body ul),:deep(.markdown-body ol) { padding-left: 20px; margin: 4px 0; }
:deep(.markdown-body li) { margin: 2px 0; }
:deep(.markdown-body code) { background: var(--surface-2); padding: 1px 5px; border-radius: 3px; font-size: 12px; color: var(--accent); }
:deep(.markdown-body pre) { background: var(--surface-2); padding: 12px; border-radius: 6px; overflow-x: auto; border: 1px solid var(--border); }
:deep(.markdown-body blockquote) { border-left: 3px solid var(--accent); padding-left: 12px; color: var(--text-muted); margin: 8px 0; }
:deep(.markdown-body strong) { font-weight: 600; color: var(--text); }
:deep(.markdown-body hr) { border: none; border-top: 1px solid var(--border); margin: 12px 0; }
:deep(.markdown-body table) { border-collapse: collapse; width: 100%; font-size: 13px; }
:deep(.markdown-body th),:deep(.markdown-body td) { border: 1px solid var(--border); padding: 6px 12px; }
:deep(.markdown-body th) { background: var(--surface-2); color: var(--text-muted); }
</style>
