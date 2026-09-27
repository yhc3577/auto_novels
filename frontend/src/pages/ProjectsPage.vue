<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, type Project } from '../api/client'

const projects = ref<Project[]>([])
const health = ref<{ ok: boolean; db: boolean } | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const form = ref({ slug: '', title: '', genre: '', platform: '' })

async function refresh() {
  loading.value = true
  error.value = null
  try {
    health.value = await api.healthz()
    projects.value = await api.listProjects()
  } catch (e: any) {
    error.value = e.message ?? String(e)
  } finally {
    loading.value = false
  }
}

async function submit() {
  error.value = null
  try {
    await api.createProject({
      slug: form.value.slug,
      title: form.value.title,
      genre: form.value.genre || undefined,
      platform: form.value.platform || undefined,
    })
    form.value = { slug: '', title: '', genre: '', platform: '' }
    await refresh()
  } catch (e: any) {
    error.value = e.message ?? String(e)
  }
}

onMounted(refresh)
</script>

<template>
  <div>
    <section class="health">
      <span v-if="health">
        <b :style="{ color: health.db ? '#10b981' : '#ef4444' }">
          ● {{ health.db ? 'db ok' : 'db down' }}
        </b>
      </span>
      <button @click="refresh" :disabled="loading">{{ loading ? '刷新中…' : '刷新' }}</button>
    </section>

    <section class="form">
      <h2>新建项目</h2>
      <form @submit.prevent="submit">
        <label>
          slug <small>(小写字母/数字/-)</small>
          <input v-model="form.slug" required pattern="[a-z0-9-]+" />
        </label>
        <label>
          title
          <input v-model="form.title" required />
        </label>
        <label>
          genre
          <input v-model="form.genre" placeholder="都市悬疑" />
        </label>
        <label>
          platform
          <input v-model="form.platform" placeholder="fanqie" />
        </label>
        <button type="submit">创建</button>
        <p v-if="error" class="error">{{ error }}</p>
      </form>
    </section>

    <section>
      <h2>项目列表</h2>
      <p v-if="!projects.length && !loading">还没有项目，先建一个。</p>
      <table v-else>
        <thead>
          <tr>
            <th>id</th>
            <th>slug</th>
            <th>title</th>
            <th>genre</th>
            <th>已写章节</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in projects" :key="p.id">
            <td>{{ p.id }}</td>
            <td><code>{{ p.slug }}</code></td>
            <td>{{ p.title }}</td>
            <td>{{ p.genre ?? '—' }}</td>
            <td>{{ p.chapter_count }}</td>
            <td class="actions">
              <RouterLink :to="{ name: 'write', params: { id: p.id } }">写长篇 →</RouterLink>
              <RouterLink :to="{ name: 'intent', params: { id: p.id } }">意图识别 →</RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
section {
  margin-bottom: 2rem;
}
h2 {
  margin: 0 0 1rem;
  font-size: 1.125rem;
}
.health {
  display: flex;
  gap: 1rem;
  align-items: center;
  font-size: 0.875rem;
  color: #6b7280;
}
form {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem 1rem;
  max-width: 640px;
}
label {
  display: flex;
  flex-direction: column;
  font-size: 0.875rem;
  color: #374151;
}
label small {
  color: #9ca3af;
  font-weight: normal;
}
input {
  margin-top: 0.25rem;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
}
button {
  padding: 0.5rem 1rem;
  background: #2563eb;
  color: white;
  border: 0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}
button:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}
.error {
  color: #ef4444;
  grid-column: 1 / -1;
  margin: 0;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
th, td {
  text-align: left;
  padding: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}
.actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}
th {
  background: #f9fafb;
  color: #6b7280;
  font-weight: 600;
}
code {
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  background: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 3px;
  font-size: 0.8125rem;
}
</style>