<template>
  <div class="knowledge-container">
    <el-card>
      <template #header>
        <div class="header">
          <h2>知识库管理</h2>
          <el-upload
            :http-request="handleUpload"
            :show-file-list="false"
            :disabled="uploading"
            accept=".txt,.md,.markdown,.pdf,.doc,.docx"
          >
            <el-button type="primary" :loading="uploading" icon="Upload">
              上传文档
            </el-button>
          </el-upload>
        </div>
      </template>

      <!-- 统计信息 -->
      <div class="stats" v-if="stats">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="文档总数">{{ stats.total }}</el-descriptions-item>
          <el-descriptions-item label="文本分块数">{{ stats.total_chunks }}</el-descriptions-item>
          <el-descriptions-item label="向量数量">{{ stats.total_vectors }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 文档列表 -->
      <el-table :data="documents" v-loading="loading" style="margin-top: 16px">
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="file_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.file_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="分块数" width="80" />
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'failed'"
              type="warning"
              size="small"
              @click="showError(row.error_message)"
            >
              查看错误
            </el-button>
            <el-button
              type="danger"
              size="small"
              icon="Delete"
              @click="handleDelete(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getDocuments, uploadDocument, deleteDocument, getKnowledgeStats } from '@/api/knowledge'

const router = useRouter()
const loading = ref(false)
const uploading = ref(false)
const documents = ref([])
const stats = ref(null)

async function loadDocuments() {
  loading.value = true
  try {
    const { data } = await getDocuments()
    documents.value = data.documents
    stats.value = { total: data.total }

    // Get vector store stats
    try {
      const { data: statsData } = await getKnowledgeStats()
      stats.value = { ...stats.value, ...statsData }
    } catch {
      // Ignore stats error
    }
  } catch (error) {
    ElMessage.error('加载文档列表失败')
  } finally {
    loading.value = false
  }
}

async function handleUpload(options) {
  uploading.value = true
  try {
    await uploadDocument(options.file)
    ElMessage.success('文档上传成功，正在处理...')
    loadDocuments()
  } catch (error) {
    ElMessage.error('上传失败：' + (error.response?.data?.detail || error.message))
  } finally {
    uploading.value = false
  }
}

async function handleDelete(id) {
  try {
    await deleteDocument(id)
    ElMessage.success('文档已删除')
    loadDocuments()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

function showError(msg) {
  ElMessage.warning(msg || '未知错误')
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function getStatusType(status) {
  const types = {
    uploading: 'info',
    parsing: 'warning',
    chunking: 'warning',
    embedding: 'warning',
    ready: 'success',
    failed: 'danger',
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    uploading: '上传中',
    parsing: '解析中',
    chunking: '分块中',
    embedding: '向量化',
    ready: '就绪',
    failed: '失败',
  }
  return texts[status] || status
}

function formatDate(isoString) {
  return new Date(isoString).toLocaleString('zh-CN')
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.knowledge-container {
  padding: 24px;
  height: 100vh;
  background: var(--bg-secondary);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h2 {
  margin: 0;
}

.stats {
  margin-bottom: 16px;
}
</style>
