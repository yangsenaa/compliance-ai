<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo -->
      <div class="login-logo">
        <div class="logo-icon">⚖️</div>
        <div class="logo-text">催收合规 AI 双雄</div>
      </div>
      <div class="login-subtitle">请选择角色并输入密码登录</div>

      <!-- 角色切换 -->
      <div class="role-tabs">
        <button
          class="role-tab"
          :class="{ active: form.username === 'admin' }"
          @click="selectRole('admin')"
        >
          <span class="role-icon">🛡️</span>
          <span>管理员</span>
          <span class="role-perm">可编辑文档</span>
        </button>
        <button
          class="role-tab"
          :class="{ active: form.username === 'inspector' }"
          @click="selectRole('inspector')"
        >
          <span class="role-icon">🔍</span>
          <span>质检员</span>
          <span class="role-perm">只读文档</span>
        </button>
      </div>

      <!-- 密码输入 -->
      <div class="form-group">
        <label class="form-label">密码</label>
        <div class="input-wrap" :class="{ error: errorMsg }">
          <input
            v-model="form.password"
            :type="showPwd ? 'text' : 'password'"
            class="pwd-input"
            placeholder="请输入密码"
            @keydown.enter="doLogin"
          />
          <button class="eye-btn" @click="showPwd = !showPwd">
            {{ showPwd ? '🙈' : '👁️' }}
          </button>
        </div>
        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
      </div>

      <!-- 登录按钮 -->
      <button class="login-btn" :class="{ loading: logging }" @click="doLogin">
        <span v-if="!logging">登 录</span>
        <span v-else class="btn-spinner"></span>
      </button>

      <!-- 提示 -->
      <div class="hint-row">
        <span class="hint">演示账号：admin / admin123 &nbsp;|&nbsp; inspector / check123</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '@/stores/auth'

const router = useRouter()

const form = reactive({ username: 'inspector', password: '' })
const showPwd = ref(false)
const errorMsg = ref('')
const logging = ref(false)

function selectRole(role: 'admin' | 'inspector') {
  form.username = role
  errorMsg.value = ''
  form.password = ''
}

async function doLogin() {
  errorMsg.value = ''
  if (!form.password) {
    errorMsg.value = '请输入密码'
    return
  }
  logging.value = true
  await new Promise(r => setTimeout(r, 500)) // 模拟延迟
  const ok = auth.login(form.username, form.password)
  logging.value = false
  if (!ok) {
    errorMsg.value = '密码错误，请重试'
    return
  }
  router.push('/')
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 40px 36px 32px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.5);
}

.login-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.logo-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, var(--accent), #a07830);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  box-shadow: 0 4px 12px rgba(210, 170, 90, 0.35);
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: 0.3px;
}

.login-subtitle {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 28px;
}

/* 角色切换 */
.role-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 24px;
}

.role-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 14px 8px;
  background: var(--surface-2);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: border-color var(--transition), background var(--transition);
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 500;
}

.role-tab:hover {
  border-color: var(--accent);
  color: var(--text);
}

.role-tab.active {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent);
}

.role-icon {
  font-size: 24px;
  margin-bottom: 2px;
}

.role-perm {
  font-size: 11px;
  color: var(--text-dim);
  font-weight: 400;
}

.role-tab.active .role-perm {
  color: var(--accent);
  opacity: 0.7;
}

/* 密码输入 */
.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.input-wrap {
  display: flex;
  align-items: center;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  transition: border-color var(--transition), box-shadow var(--transition);
}

.input-wrap:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(210, 170, 90, 0.15);
}

.input-wrap.error {
  border-color: var(--danger);
}

.pwd-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text);
  font-size: 14px;
  padding: 11px 14px;
  outline: none;
  font-family: inherit;
}

.pwd-input::placeholder {
  color: var(--text-dim);
}

.eye-btn {
  background: transparent;
  border: none;
  padding: 0 12px;
  cursor: pointer;
  font-size: 16px;
  opacity: 0.6;
  transition: opacity var(--transition);
}

.eye-btn:hover {
  opacity: 1;
}

.error-msg {
  font-size: 12px;
  color: var(--danger);
  margin-top: 6px;
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  padding: 13px;
  background: linear-gradient(135deg, var(--accent), #a07830);
  border: none;
  border-radius: var(--radius);
  color: #0d1117;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  letter-spacing: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: filter var(--transition), transform 0.1s;
  margin-bottom: 20px;
}

.login-btn:hover:not(.loading) {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.login-btn:active {
  transform: translateY(0);
}

.login-btn.loading {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(0, 0, 0, 0.3);
  border-top-color: #0d1117;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 提示 */
.hint-row {
  text-align: center;
}

.hint {
  font-size: 11px;
  color: var(--text-dim);
}
</style>
