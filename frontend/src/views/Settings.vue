<template>
  <div class="settings-container">
    <el-card>
      <template #header>
        <h2>设置</h2>
      </template>

      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px" style="max-width: 500px">
        <h3>账号信息</h3>
        <el-form-item label="用户名">
          <el-input :model-value="userStore.user?.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input :model-value="userStore.user?.email" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-tag :type="userStore.isAdmin ? 'danger' : 'info'">
            {{ userStore.isAdmin ? '管理员' : '普通用户' }}
          </el-tag>
        </el-form-item>

        <el-divider />

        <h3>修改密码</h3>
        <el-form-item label="当前密码" prop="oldPassword">
          <el-input v-model="form.oldPassword" type="password" placeholder="请输入当前密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="form.newPassword" type="password" placeholder="请输入新密码（至少 6 位）" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入新密码" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="changing" @click="handleChangePassword">
            确认修改
          </el-button>
        </el-form-item>

        <el-divider />

        <h3>外观设置</h3>
        <el-form-item label="主题模式">
          <el-radio-group v-model="themeStore.isDark" @change="themeStore.toggle">
            <el-radio :label="false">☀️ 白天模式</el-radio>
            <el-radio :label="true">🌙 夜晚模式</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-divider />

        <h3>模型状态</h3>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="Embedding 模型">
            <el-tag>text-embedding-v3</el-tag>
            <span style="margin-left: 8px; color: var(--text-regular)">（自动故障切换）</span>
          </el-descriptions-item>
          <el-descriptions-item label="LLM 模型">
            <el-tag>qwen-plus</el-tag>
            <span style="margin-left: 8px; color: var(--text-regular)">（自动故障切换：qwen-plus → qwen-turbo → qwen-max）</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'

const userStore = useUserStore()
const themeStore = useThemeStore()
const formRef = ref(null)
const changing = ref(false)

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const rules = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function handleChangePassword() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    changing.value = true
    try {
      await userStore.changePassword({
        old_password: form.oldPassword,
        new_password: form.newPassword,
      })
      ElMessage.success('密码修改成功')
      form.oldPassword = ''
      form.newPassword = ''
      form.confirmPassword = ''
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '修改失败')
    } finally {
      changing.value = false
    }
  })
}
</script>

<style scoped>
.settings-container {
  padding: 24px;
  height: 100vh;
  background: var(--bg-secondary);
}

.settings-container h3 {
  margin: 0 0 16px;
  color: var(--text-primary);
  font-size: 16px;
}
</style>
