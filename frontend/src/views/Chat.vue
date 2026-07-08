<template>
  <div class="chat-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <h3 v-if="!sidebarCollapsed">虚拟女友知识库</h3>
        <el-button icon="Fold" @click="sidebarCollapsed = !sidebarCollapsed" />
      </div>

      <div class="sidebar-actions" v-if="!sidebarCollapsed">
        <el-button type="primary" @click="createNewSession" icon="Plus">新对话</el-button>
      </div>

      <el-scrollbar class="session-list">
        <div
          v-for="session in sessionStore.sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: sessionStore.currentSessionId === session.id }"
          @click="selectSession(session.id)"
        >
          <el-icon class="chat-icon"><ChatDotRound /></el-icon>
          <span class="session-title" v-if="!sidebarCollapsed">{{ session.title }}</span>
          <el-button
            v-if="!sidebarCollapsed"
            link
            type="danger"
            size="small"
            icon="Delete"
            @click.stop="deleteSession(session.id)"
          />
        </div>
      </el-scrollbar>

      <div class="sidebar-footer" v-if="!sidebarCollapsed">
        <router-link to="/knowledge">
          <el-button icon="Folder">知识库</el-button>
        </router-link>
        <router-link to="/settings">
          <el-button icon="Setting">设置</el-button>
        </router-link>
        <el-button @click="themeStore.toggle" icon="Moon" v-if="!themeStore.isDark" />
        <el-button @click="themeStore.toggle" icon="Sunny" v-else />
        <el-button @click="userStore.logout" icon="SwitchButton">退出</el-button>
      </div>
    </aside>

    <!-- 主聊天区域 -->
    <main class="chat-main">
      <div class="chat-header">
        <h4>{{ currentSessionTitle }}</h4>
        <span class="model-badge" v-if="currentModel">{{ currentModel }}</span>
      </div>

      <el-scrollbar ref="messageScroll" class="messages-container">
        <div v-for="msg in messages" :key="msg.id" class="message" :class="msg.role">
          <div class="message-avatar">
            <el-icon v-if="msg.role === 'user'"><User /></el-icon>
            <el-icon v-else><Star /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-bubble">
              <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
              <!-- 引用卡片 -->
              <div v-if="msg.citations && msg.citations.length" class="citations">
                <el-divider>参考资料</el-divider>
                <div class="citation-list">
                  <el-card
                    v-for="(cit, idx) in msg.citations"
                    :key="idx"
                    class="citation-card"
                    size="small"
                  >
                    <div class="citation-source">
                      <el-icon><Document /></el-icon>
                      <span>{{ cit.source }}</span>
                      <el-tag size="small" type="info">相似度：{{ (cit.score * 100).toFixed(1) }}%</el-tag>
                    </div>
                    <p class="citation-text">{{ cit.text }}</p>
                  </el-card>
                </div>
              </div>
            </div>
            <div class="message-time">{{ formatTime(msg.created_at) }}</div>
          </div>
        </div>
        <!-- 正在输入 -->
        <div v-if="isStreaming" class="message assistant">
          <div class="message-avatar"><el-icon><Star /></el-icon></div>
          <div class="message-content">
            <div class="message-bubble typing">
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
            </div>
          </div>
        </div>
      </el-scrollbar>

      <!-- 输入区域 -->
      <div class="input-area">
        <el-input
          v-model="inputMessage"
          placeholder="输入消息，按 Enter 发送..."
          :disabled="isStreaming"
          @keydown.enter.exact="sendMessage"
          rows="2"
          type="textarea"
          resize="none"
        />
        <el-button type="primary" :loading="isStreaming" @click="sendMessage" icon="Prometheus">
          发送
        </el-button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useSessionStore } from '@/stores/session'
import { useThemeStore } from '@/stores/theme'
import { getMessages, sendMessage as sendChatMessage } from '@/api/chat'
import MarkdownIt from 'markdown-it'

const userStore = useUserStore()
const sessionStore = useSessionStore()
const themeStore = useThemeStore()

const md = new MarkdownIt()
const sidebarCollapsed = ref(false)
const messages = ref([])
const inputMessage = ref('')
const isStreaming = ref(false)
const currentModel = ref(null)
const messageScroll = ref(null)

const currentSessionTitle = computed(() => {
  const session = sessionStore.sessions.find(s => s.id === sessionStore.currentSessionId)
  return session?.title || '新对话'
})

async function selectSession(id) {
  sessionStore.setCurrentSession(id)
  await loadMessages(id)
}

async function loadMessages(sessionId) {
  try {
    const { data } = await getMessages(sessionId)
    messages.value = data
    await nextTick()
    scrollToBottom()
  } catch (error) {
    ElMessage.error('加载消息失败')
  }
}

async function createNewSession() {
  try {
    const session = await sessionStore.createNewSession('新对话')
    sessionStore.setCurrentSession(session.id)
    messages.value = []
  } catch (error) {
    ElMessage.error('创建会话失败')
  }
}

async function deleteSession(id) {
  try {
    await sessionStore.deleteSession(id)
    if (!sessionStore.currentSessionId) {
      messages.value = []
    }
    ElMessage.success('会话已删除')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

async function sendMessage() {
  if (!inputMessage.value.trim() || isStreaming.value) return
  if (!sessionStore.currentSessionId) {
    await createNewSession()
  }

  const content = inputMessage.value.trim()
  inputMessage.value = ''

  // Add user message optimistically
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content,
    created_at: new Date().toISOString(),
  })
  await nextTick()
  scrollToBottom()

  isStreaming.value = true
  currentModel.value = null

  let assistantMsg = {
    id: Date.now() + 1,
    role: 'assistant',
    content: '',
    citations: null,
    created_at: new Date().toISOString(),
  }
  messages.value.push(assistantMsg)

  try {
    await sendChatMessage(sessionStore.currentSessionId, content, (event) => {
      if (event.type === 'citations') {
        assistantMsg.citations = event.data
      } else if (event.type === 'model') {
        currentModel.value = event.data
      } else if (event.type === 'token') {
        assistantMsg.content += event.data
        nextTick(() => scrollToBottom())
      } else if (event.type === 'done') {
        isStreaming.value = false
        currentModel.value = event.data?.model || null
        // Reload to get persisted message
        loadMessages(sessionStore.currentSessionId)
      } else if (event.type === 'error') {
        ElMessage.error(event.data)
        isStreaming.value = false
      }
    })
  } catch (error) {
    ElMessage.error('发送失败：' + error.message)
    isStreaming.value = false
  }
}

function scrollToBottom() {
  const container = messageScroll.value?.wrapRef
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

function renderMarkdown(text) {
  return md.render(text)
}

function formatTime(isoString) {
  const date = new Date(isoString)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  await userStore.fetchUser()
  await sessionStore.fetchSessions()
  if (sessionStore.sessions.length > 0) {
    sessionStore.setCurrentSession(sessionStore.sessions[0].id)
    await loadMessages(sessionStore.sessions[0].id)
  }
})
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100vh;
  background: var(--bg-secondary);
}

.sidebar {
  width: 260px;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--text-primary);
}

.sidebar-actions {
  padding: 16px;
}

.session-list {
  flex: 1;
  overflow-y: auto;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
  gap: 8px;
}

.session-item:hover {
  background: var(--bg-tertiary);
}

.session-item.active {
  background: var(--accent-color);
  color: white;
}

.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sidebar-footer a {
  text-decoration: none;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-header h4 {
  margin: 0;
  color: var(--text-primary);
}

.model-badge {
  background: var(--accent-color);
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.messages-container {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  background: var(--chat-assistant-bg);
  color: var(--text-primary);
}

.message.user .message-bubble {
  background: var(--chat-user-bg);
}

.message-bubble.typing {
  display: flex;
  gap: 4px;
  padding: 16px 20px;
}

.typing-dot {
  width: 8px;
  height: 8px;
  background: var(--text-regular);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 100% { transform: scale(0.4); opacity: 0.4; }
  50% { transform: scale(1); opacity: 1; }
}

.citations {
  margin-top: 16px;
}

.citation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.citation-card {
  background: var(--bg-tertiary);
}

.citation-source {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--text-secondary);
}

.citation-text {
  font-size: 13px;
  color: var(--text-regular);
  line-height: 1.6;
}

.message-time {
  font-size: 12px;
  color: var(--text-regular);
  text-align: right;
}

.input-area {
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
  display: flex;
  gap: 12px;
}

.input-area textarea {
  resize: none;
}
</style>
