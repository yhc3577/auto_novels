<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, type WriteResponse } from '../api/client'
import StageList from '../components/StageList.vue'

const props = defineProps<{ id: string }>()
const router = useRouter()

const userInput = ref('回到雾港的夜晚，导师失踪了')
const targetWordcount = ref(1500)
const submitting = ref(false)
const result = ref<WriteResponse | null>(null)
const error = ref<string | null>(null)

async function submit() {
  submitting.value = true
  error.value = null
  result.value = null
  try {
    result.value = await api.write({
      project_id: Number(props.id),
      user_input: userInput.value,
      target_wordcount: targetWordcount.value,
    })
  } catch (e: any) {
    error.value = e.message ?? String(e)
  } finally {
    submitting.value = false
  }
}

function back() {
  router.push({ name: 'projects' })
}
</script>

<template>
  <div>
    <button class="back" @click="back">← 返回项目列表</button>
    <h2>项目 #{{ id }} · 写章节</h2>

    <form @submit.prevent="submit" class="form">
      <label>
        user_input
        <textarea v-model="userInput" rows="3" required />
      </label>
      <label>
        target_wordcount
        <input type="number" v-model.number="targetWordcount" min="100" max="50000" />
      </label>
      <button type="submit" :disabled="submitting">
        {{ submitting ? '写作中…' : '触发写章节流' }}
      </button>
    </form>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="result" class="result">
      <div class="meta">
        <span>chapter_no: <b>{{ result.chapter_no }}</b></span>
        <span>state_revision: <b>{{ result.state_revision }}</b></span>
        <span>final_wordcount: <b>{{ result.final_wordcount ?? '—' }}</b></span>
        <span v-if="result.chapter_id">chapter_id: <b>{{ result.chapter_id }}</b></span>
      </div>

      <StageList :stages="result.stages" />

      <section v-if="result.chapter_hook" class="hook">
        <h3>chapter_hook</h3>
        <p>{{ result.chapter_hook }}</p>
      </section>

      <section v-if="result.summary_text" class="summary">
        <h3>summary</h3>
        <p>{{ result.summary_text }}</p>
      </section>

      <section v-if="result.errors?.length" class="errors">
        <h3>errors</h3>
        <ul>
          <li v-for="(e, i) in result.errors" :key="i">{{ e }}</li>
        </ul>
      </section>
    </div>
  </div>
</template>

<style scoped>
.back {
  background: transparent;
  border: 0;
  color: #6b7280;
  cursor: pointer;
  margin-bottom: 1rem;
  padding: 0;
  font-size: 0.875rem;
}
.form {
  display: grid;
  gap: 0.75rem;
  max-width: 640px;
  margin-bottom: 1.5rem;
}
label {
  display: flex;
  flex-direction: column;
  font-size: 0.875rem;
  color: #374151;
}
input, textarea {
  margin-top: 0.25rem;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
  font-family: inherit;
}
button[type="submit"] {
  padding: 0.625rem 1rem;
  background: #2563eb;
  color: white;
  border: 0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  justify-self: start;
}
button:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}
.error {
  color: #ef4444;
  background: #fef2f2;
  padding: 0.75rem;
  border-radius: 4px;
}
.result {
  margin-top: 1.5rem;
}
.meta {
  display: flex;
  gap: 1.5rem;
  padding: 0.75rem 1rem;
  background: #f3f4f6;
  border-radius: 4px;
  margin: 1rem 0;
  font-size: 0.875rem;
}
.hook, .summary, .errors {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: #fffbeb;
  border-left: 3px solid #f59e0b;
  border-radius: 0 4px 4px 0;
}
.hook h3, .summary h3, .errors h3 {
  margin: 0 0 0.5rem;
  font-size: 0.875rem;
  color: #92400e;
}
.errors {
  background: #fef2f2;
  border-left-color: #ef4444;
}
.errors h3 {
  color: #b91c1c;
}
</style>