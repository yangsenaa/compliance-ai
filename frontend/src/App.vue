<template>
  <div class="app-shell">
    <!-- 左侧导航栏 -->
    <aside class="sidebar" :class="{ collapsed }">
      <div class="sidebar-logo">
        <div class="logo-icon">⚖</div>
        <Transition name="fade-text">
          <span v-if="!collapsed" class="logo-text">合规双雄</span>
        </Transition>
      </div>

      <nav class="sidebar-nav">
        <div
          v-for="item in navItems"
          :key="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
          @click="router.push(item.path)"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <Transition name="fade-text">
            <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
          </Transition>
          <div class="nav-active-bar" v-if="route.path === item.path" />
        </div>
      </nav>

      <button class="collapse-btn" @click="collapsed = !collapsed">
        <span>{{ collapsed ? '›' : '‹' }}</span>
      </button>
    </aside>

    <!-- 主内容区 -->
    <div class="main-area" :class="{ 'sidebar-collapsed': collapsed }">
      <!-- 顶部 Header -->
      <header class="topbar">
        <div class="topbar-left">
          <h1 class="page-title">
            <span class="title-scale">⚖</span>
            催收合规 <em>AI</em> 双雄
          </h1>
          <span class="beta-badge">BETA</span>
        </div>
        <div class="topbar-right">
          <div class="status-pill" :class="mockMode ? 'mock' : 'live'">
            <span class="status-dot" />
            {{ mockMode ? '演示模式' : '生产模式' }}
          </div>
          <!-- 用户信息 -->
          <div v-if="auth.isLoggedIn.value" class="user-info">
            <span class="user-avatar">{{ auth.isAdmin.value ? '🛡️' : '🔍' }}</span>
            <Transition name="fade-text">
              <span v-if="!collapsed" class="user-label">{{ auth.roleLabel.value }}</span>
            </Transition>
            <button class="logout-btn" title="退出登录" @click="logout">↩</button>
          </div>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content-area">
        <router-view v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" />
          </Transition>
        </router-view>
      </main>

      <footer class="app-footer">
        催收合规 AI 双雄 © 2025 &nbsp;·&nbsp; 智能质检 &nbsp;·&nbsp; 合规答疑 &nbsp;·&nbsp; 文档管理
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { auth } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)
const mockMode = ref(true)

const navItems = [
  { path: '/inspector', icon: '🔍', label: '质检官' },
  { path: '/advisor',   icon: '📋', label: '答疑官' },
  { path: '/docs',      icon: '📂', label: '文档管理' },
]

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style>
/* ─── Reset & Tokens ─────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:          #0d1117;
  --surface:     #161b22;
  --surface-2:   #1e2530;
  --border:      rgba(99,114,135,.25);
  --border-glow: rgba(210,170,90,.3);
  --text:        #e6edf3;
  --text-muted:  #7d8590;
  --text-dim:    #4a5568;
  --accent:      #d2aa5a;
  --accent-soft: rgba(210,170,90,.12);
  --danger:      #f85149;
  --warn:        #e3b341;
  --safe:        #3fb950;
  --info:        #58a6ff;
  --radius:      10px;
  --radius-lg:   16px;
  --sidebar-w:   220px;
  --sidebar-wc:  68px;
  --topbar-h:    60px;
  --transition:  .22s cubic-bezier(.4,0,.2,1);
  font-family: 'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif;
}

html, body, #app { height: 100%; background: var(--bg); color: var(--text); }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-dim); }

/* ─── Ant-Design variable overrides (dark) ─────────── */
:where(.ant-btn-primary) { background: var(--accent) !important; border-color: var(--accent) !important; color: #0d1117 !important; }
:where(.ant-btn-primary:hover) { filter: brightness(1.1); }
:where(.ant-card) { background: var(--surface) !important; border-color: var(--border) !important; color: var(--text) !important; }
:where(.ant-card-head) { background: transparent !important; border-color: var(--border) !important; color: var(--text) !important; }
:where(.ant-tabs-nav) { color: var(--text-muted) !important; }
:where(.ant-tabs-tab-active .ant-tabs-tab-btn) { color: var(--accent) !important; }
:where(.ant-tabs-ink-bar) { background: var(--accent) !important; }
:where(.ant-input), :where(.ant-input-affix-wrapper), :where(textarea.ant-input) {
  background: var(--surface-2) !important; border-color: var(--border) !important;
  color: var(--text) !important;
}
:where(.ant-input::placeholder), :where(textarea.ant-input::placeholder) { color: var(--text-dim) !important; }
:where(.ant-input:focus), :where(.ant-input-focused), :where(textarea.ant-input:focus) {
  border-color: var(--accent) !important; box-shadow: 0 0 0 2px rgba(210,170,90,.2) !important;
}
:where(.ant-upload-drag) { background: var(--surface-2) !important; border-color: var(--border) !important; }
:where(.ant-upload-drag:hover) { border-color: var(--accent) !important; }
:where(.ant-collapse) { background: transparent !important; border-color: var(--border) !important; }
:where(.ant-collapse-item) { border-color: var(--border) !important; }
:where(.ant-collapse-header) { color: var(--text) !important; }
:where(.ant-collapse-content) { background: var(--surface-2) !important; border-color: var(--border) !important; color: var(--text) !important; }
:where(.ant-descriptions-item-label) { color: var(--text-muted) !important; }
:where(.ant-descriptions-item-content) { color: var(--text) !important; }
:where(.ant-modal-content) { background: var(--surface) !important; color: var(--text) !important; }
:where(.ant-modal-header) { background: transparent !important; border-color: var(--border) !important; }
:where(.ant-modal-title) { color: var(--text) !important; }
:where(.ant-form-item-label label) { color: var(--text-muted) !important; }
:where(.ant-popover-inner) { background: var(--surface-2) !important; }
:where(.ant-empty-description) { color: var(--text-muted) !important; }
:where(.ant-result-title) { color: var(--text) !important; }
:where(.ant-result-subtitle) { color: var(--text-muted) !important; }
:where(.ant-statistic-title) { color: var(--text-muted) !important; }
:where(.ant-statistic-content) { color: var(--text) !important; }
:where(.ant-progress-text) { color: var(--text) !important; }
:where(.ant-badge-status-text) { color: var(--text-muted) !important; }
:where(.ant-alert) { background: var(--surface-2) !important; border-color: var(--border) !important; }
:where(.ant-alert-message) { color: var(--text) !important; }
:where(.ant-select-selector) { background: var(--surface-2) !important; border-color: var(--border) !important; color: var(--text) !important; }
</style>

<style scoped>
/* ─── Layout Shell ───────────────────────────────────── */
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ─── Sidebar ────────────────────────────────────────── */
.sidebar {
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  height: 100vh;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  transition: width var(--transition), min-width var(--transition);
  position: relative;
  z-index: 200;
}

.sidebar.collapsed {
  width: var(--sidebar-wc);
  min-width: var(--sidebar-wc);
}

/* Logo */
.sidebar-logo {
  height: var(--topbar-h);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px;
  border-bottom: 1px solid var(--border);
  overflow: hidden;
  white-space: nowrap;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--accent), #a07830);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(210,170,90,.35);
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: .5px;
}

/* Nav */
.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  white-space: nowrap;
  transition: background var(--transition), color var(--transition);
  color: var(--text-muted);
  user-select: none;
}

.nav-item:hover {
  background: var(--surface-2);
  color: var(--text);
}

.nav-item.active {
  background: var(--accent-soft);
  color: var(--accent);
}

.nav-icon {
  font-size: 18px;
  flex-shrink: 0;
  width: 24px;
  text-align: center;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
}

.nav-active-bar {
  position: absolute;
  right: 0;
  top: 20%;
  height: 60%;
  width: 3px;
  background: var(--accent);
  border-radius: 2px;
}

/* Collapse Button */
.collapse-btn {
  height: 44px;
  background: transparent;
  border: none;
  border-top: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 20px;
  cursor: pointer;
  transition: color var(--transition), background var(--transition);
  display: flex;
  align-items: center;
  justify-content: center;
}
.collapse-btn:hover {
  color: var(--text);
  background: var(--surface-2);
}

/* ─── Main Area ─────────────────────────────────────── */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg);
}

/* Topbar */
.topbar {
  height: var(--topbar-h);
  min-height: var(--topbar-h);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -.3px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-title em {
  font-style: normal;
  background: linear-gradient(135deg, var(--accent), #f0c060);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-scale {
  font-size: 22px;
}

.beta-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 2px 8px;
  border-radius: 20px;
  background: var(--accent-soft);
  color: var(--accent);
  border: 1px solid var(--border-glow);
}

.status-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid var(--border);
}

.status-pill.mock { color: var(--warn); background: rgba(227,179,65,.1); border-color: rgba(227,179,65,.3); }
.status-pill.live { color: var(--safe); background: rgba(63,185,80,.1); border-color: rgba(63,185,80,.3); }

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,100% { opacity: 1; }
  50% { opacity: .4; }
}

/* Content */
.content-area {
  flex: 1;
  overflow: hidden;
  padding: 20px;
}

/* Footer */
.app-footer {
  text-align: center;
  padding: 10px;
  font-size: 12px;
  color: var(--text-dim);
  border-top: 1px solid var(--border);
}

/* ─── Transitions ───────────────────────────────────── */
.fade-text-enter-active, .fade-text-leave-active { transition: opacity .15s, transform .15s; }
.fade-text-enter-from, .fade-text-leave-to { opacity: 0; transform: translateX(-6px); }

.page-enter-active, .page-leave-active { transition: opacity .18s, transform .18s; }
.page-enter-from, .page-leave-to { opacity: 0; transform: translateY(6px); }

/* topbar right 区域 */
.topbar-right { display: flex; align-items: center; gap: 12px; }

/* 用户信息 */
.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px 4px 8px;
  border-radius: 20px;
  background: var(--surface-2);
  border: 1px solid var(--border);
}
.user-avatar { font-size: 15px; }
.user-label { font-size: 12px; color: var(--text-muted); font-weight: 500; }
.logout-btn {
  background: transparent;
  border: none;
  color: var(--text-dim);
  font-size: 14px;
  cursor: pointer;
  padding: 1px 3px;
  border-radius: 4px;
  transition: color var(--transition), background var(--transition);
  line-height: 1;
}
.logout-btn:hover { color: var(--danger); background: rgba(248,81,73,.1); }
</style>
