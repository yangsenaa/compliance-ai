<template>
  <a-layout class="app-layout">
    <!-- 左侧导航栏 -->
    <a-layout-sider
      v-model:collapsed="collapsed"
      :trigger="null"
      collapsible
      class="sider"
      :style="{ overflow: 'auto', height: '100vh', position: 'fixed', left: 0, top: 0, bottom: 0 }"
    >
      <!-- Logo 区域 -->
      <div class="logo">
        <span v-if="!collapsed" class="logo-text">⚖️ 合规双雄</span>
        <span v-else>⚖️</span>
      </div>

      <!-- 导航菜单 -->
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        @click="handleMenuClick"
      >
        <a-menu-item key="/inspector">
          <template #icon>
            <search-outlined />
          </template>
          <span>质检官</span>
        </a-menu-item>
        <a-menu-item key="/advisor">
          <template #icon>
            <message-outlined />
          </template>
          <span>答疑官</span>
        </a-menu-item>
        <a-menu-item key="/docs">
          <template #icon>
            <file-text-outlined />
          </template>
          <span>文档管理</span>
        </a-menu-item>
      </a-menu>

      <!-- 折叠按钮 -->
      <div class="collapse-btn" @click="collapsed = !collapsed">
        <menu-fold-outlined v-if="!collapsed" />
        <menu-unfold-outlined v-else />
      </div>
    </a-layout-sider>

    <!-- 主内容区 -->
    <a-layout :style="{ marginLeft: collapsed ? '80px' : '200px', transition: 'all 0.2s' }">
      <!-- 顶部 Header -->
      <a-layout-header class="header">
        <div class="header-content">
          <div class="header-title">
            <span class="title-icon">⚖️</span>
            <span class="title-text">催收合规 AI 双雄</span>
            <a-tag color="blue" style="margin-left: 12px">Beta</a-tag>
          </div>
          <div class="header-right">
            <a-tag :color="mockMode ? 'orange' : 'green'">
              {{ mockMode ? '🎭 演示模式' : '🔴 生产模式' }}
            </a-tag>
          </div>
        </div>
      </a-layout-header>

      <!-- 内容区 -->
      <a-layout-content class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </a-layout-content>

      <!-- Footer -->
      <a-layout-footer class="footer">
        催收合规 AI 双雄 © 2024 | 智能质检 · 合规答疑 · 文档管理
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  SearchOutlined,
  MessageOutlined,
  FileTextOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()

const collapsed = ref(false)
const mockMode = ref(true) // 实际应从后端获取

const selectedKeys = ref<string[]>([route.path])

watch(
  () => route.path,
  (path) => {
    selectedKeys.value = [path]
  }
)

function handleMenuClick({ key }: { key: string }) {
  router.push(key)
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}

.sider {
  background: #001529;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0 16px;
  white-space: nowrap;
  overflow: hidden;
}

.logo-text {
  font-size: 15px;
}

.collapse-btn {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.65);
  font-size: 18px;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: color 0.3s;
}

.collapse-btn:hover {
  color: white;
}

.header {
  background: #fff;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 24px;
}

.title-text {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.content {
  margin: 24px;
  min-height: calc(100vh - 64px - 70px - 48px);
}

.footer {
  text-align: center;
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
}

/* 路由切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f0f0f0;
}

::-webkit-scrollbar-thumb {
  background: #bbb;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #999;
}
</style>
