/**
 * 角色认证 Store（基于 localStorage，无需后端）
 * 角色：admin（管理员）| inspector（质检员）
 */
import { reactive, computed } from 'vue'

export type Role = 'admin' | 'inspector'

interface AuthState {
  role: Role | null
  username: string
}

// 密码配置（生产环境应由后端验证）
const CREDENTIALS: Record<string, { password: string; role: Role; label: string }> = {
  admin: { password: 'admin123', role: 'admin', label: '管理员' },
  inspector: { password: 'check123', role: 'inspector', label: '质检员' },
}

const STORAGE_KEY = 'compliance_ai_auth'

function loadFromStorage(): AuthState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch {}
  return { role: null, username: '' }
}

function saveToStorage(state: AuthState) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

const state = reactive<AuthState>(loadFromStorage())

export const auth = {
  state,

  // 计算属性
  isLoggedIn: computed(() => !!state.role),
  isAdmin: computed(() => state.role === 'admin'),
  isInspector: computed(() => state.role === 'inspector'),
  roleLabel: computed(() =>
    state.role ? (CREDENTIALS[state.username]?.label ?? state.role) : ''
  ),

  /**
   * 登录，返回 true 成功，false 密码错误
   */
  login(username: string, password: string): boolean {
    const cred = CREDENTIALS[username]
    if (!cred || cred.password !== password) return false
    state.role = cred.role
    state.username = username
    saveToStorage(state)
    return true
  },

  logout() {
    state.role = null
    state.username = ''
    localStorage.removeItem(STORAGE_KEY)
  },
}
