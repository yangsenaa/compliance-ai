import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

// ==================== 类型定义 ====================

export interface Violation {
  sentence: string
  start: number
  end: number
  rule: string
  severity: '高' | '中' | '低'
  explanation: string
}

export interface InspectResult {
  original_text: string
  violations: Violation[]
  score: number
  summary: string
  asr_transcript?: string
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export interface Doc {
  id: string
  name: string
  filename: string
  size: number
  updated_at: number
}

// ==================== 质检官 API ====================

export async function inspectText(text: string): Promise<InspectResult> {
  return api.post('/inspect/text', { text })
}

export async function inspectAudio(file: File): Promise<InspectResult> {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/inspect/audio', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// ==================== 答疑官 API ====================

export async function chatWithAdvisor(question: string, history: Message[] = []): Promise<string> {
  const result: any = await api.post('/advisor/chat', { question, history })
  return result.answer
}

// ==================== 文档管理 API ====================

export async function getDocs(): Promise<Doc[]> {
  const result: any = await api.get('/docs')
  return result.docs
}

export async function createDoc(name: string, content: string = ''): Promise<Doc> {
  return api.post('/docs', { name, content })
}

export async function getDoc(id: string): Promise<{ id: string; name: string; content: string }> {
  return api.get(`/docs/${id}`)
}

export async function updateDoc(id: string, content: string): Promise<void> {
  return api.put(`/docs/${id}`, { content })
}

export async function deleteDoc(id: string): Promise<void> {
  return api.delete(`/docs/${id}`)
}
