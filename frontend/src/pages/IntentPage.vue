<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { routerApi } from '../api/router'
import type { Scenario, RouterResponse, StageStatus } from '../api/client'
import StageList from '../components/StageList.vue'

const props = defineProps<{ id: string }>()
const router = useRouter()

const userInput = ref('写第 3 章，回到雾港的夜晚，导师失踪了')
const scenario = ref<Scenario>('auto')
const submitting = ref(false)
const result = ref<RouterResponse | null>(null)
const error = ref<string | null>(null)

// 拆分 router 的 stages：先 intent 阶段，再子图阶段
// 锚点用后端 router 节点唯一 emit 的 'intent_router'（不依赖任何额外 stage）
const splitStages = computed(() => {
  if (!result.value) return { router: [], sub: [] }
  const all = result.value.stages
  const idx = all.findIndex((s) => s.name === 'intent_router')
  if (idx === -1) return { router: [], sub: all }  // 防护：没找到则全部当作子图
  return { router: all.slice(0, idx + 1), sub: all.slice(idx + 1) }
})

const payloadPretty = computed(() => {
  if (!result.value) return null
  const p = result.value.payload
  const interesting: Record<string, unknown> = {}
  for (const k of ['length', 'chapter_no', 'chapter_id', 'final_wordcount', 'platforms', 'scan_topic']) {
    if (p[k] !== undefined) interesting[k] = p[k]
  }
  if (p.prose_draft) interesting['prose_draft'] = String(p.prose_draft).slice(0, 200) + '…'
  if (p.scan_report) interesting['scan_report'] = String(p.scan_report).slice(0, 200) + '…'
  if (p.summary_text) interesting['summary_text'] = p.summary_text
  return interesting
})

async function submit() {
  submitting.value = true
  error.value = null
  result.value = null
  try {
    result.value = await routerApi.invoke({
      project_id: Number(props.id),
      user_input: userInput.value,
      explicit_scenario: scenario.value,
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

const intentLabel: Record<string, string> = {
  write_long: '写长篇章节',
  write_short: '写短篇',
  scan: '扫榜',
  review: '审查（预留）',
  analyze: '拆书（预留）',
  memory_query: '记忆查询（预留）',
  deslop: '去 AI 味（预留）',
  import_book: '导入书（预留）',
  unknown: '未知意图',
}
</script>

<template>
  <div>
    <button class="back" @click="back">← 返回项目列表</button>
    <h2>项目 #{{ id }} · 意图识别 + 主分发</h2>

    <form @submit.prevent="submit" class="form">
      <label>
        user_input（自然语言意图）
        <textarea v-model="userInput" rows="3" required />
      </label>
      <label>
        explicit_scenario
        <select v-model="scenario">
          <option value="auto">auto（自动识别）</option>
          <option value="write_long">write_long（长篇）</option>
          <option value="write_short">write_short（短篇）</option>
          <option value="scan">scan（扫榜）</option>
        </select>
      </label>
      <button type="submit" :disabled="submitting">
        {{ submitting ? '处理中…' : '执行' }}
      </button>
    </form>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="result" class="result">
      <div class="meta">
        <span>intent: <b>{{ intentLabel[result.intent] ?? result.intent }}</b></span>
        <span>graph_invoked: <b>{{ result.graph_invoked }}</b></span>
        <span>supported:
          <b :style="{ color: result.supported ? '#10b981' : '#ef4444' }">
            {{ result.supported ? '✓' : '✗ 预留中' }}
          </b>
        </span>
        <span v-if="result.state_revision">state_revision: <b>{{ result.state_revision }}</b></span>
        <span v-if="result.final_wordcount">final_wordcount: <b>{{ result.final_wordcount }}</b></span>
      </div>

      <p v-if="result.notice" class="notice">{{ result.notice }}</p>

      <section v-if="splitStages.router.length">
        <h3>① Router（意图识别 + 分发）</h3>
        <StageList :stages="splitStages.router as StageStatus[]" />
      </section>

      <section v-if="splitStages.sub.length">
        <h3>② {{ result.graph_invoked }}（子图执行）</h3>
        <StageList :stages="splitStages.sub as StageStatus[]" />
      </section>

      <section v-if="payloadPretty && Object.keys(payloadPretty).length" class="payload">
        <h3>payload</h3>
        <pre>{{ JSON.stringify(payloadPretty, null, 2) }}</pre>
      </section>

      <section v-if="result.errors?.length" class="errors">
        <h3>errors</h3>
        <ul><li v-for="(e, i) in result.errors" :key="i">{{ e }}</li></ul>
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
textarea, input, select {
  margin-top: 0.25rem;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
  font-family: inherit;
}
button[type='submit'] {
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
.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: #f3f4f6;
  border-radius: 4px;
  margin: 1rem 0;
  font-size: 0.875rem;
}
.notice {
  background: #fffbeb;
  border-left: 3px solid #f59e0b;
  padding: 0.75rem 1rem;
  border-radius: 0 4px 4px 0;
  margin: 1rem 0;
}
h3 {
  margin: 1rem 0 0.5rem;
  font-size: 0.95rem;
}
section.payload pre {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  padding: 0.75rem;
  border-radius: 4px;
  font-size: 0.8125rem;
  overflow-x: auto;
}
.errors {
  background: #fef2f2;
  border-left: 3px solid #ef4444;
  padding: 0.75rem 1rem;
  border-radius: 0 4px 4px 0;
  margin-top: 1rem;
}
.errors h3 {
  color: #b91c1c;
  margin: 0 0 0.5rem;
}
</style>