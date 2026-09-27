<script setup lang="ts">
import type { StageStatus } from '../api/client'

defineProps<{ stages: StageStatus[] }>()

const statusIcon: Record<string, string> = {
  pending: '⏳',
  running: '🔄',
  done: '✅',
  skipped: '⏭️',
  failed: '❌',
}
const statusColor: Record<string, string> = {
  pending: '#999',
  running: '#3b82f6',
  done: '#10b981',
  skipped: '#9ca3af',
  failed: '#ef4444',
}
</script>

<template>
  <div class="stage-list">
    <h3>Stages</h3>
    <ol>
      <li v-for="(s, i) in stages" :key="i">
        <span class="icon">{{ statusIcon[s.status] || '·' }}</span>
        <span class="name">{{ s.name }}</span>
        <span class="status" :style="{ color: statusColor[s.status] }">
          {{ s.status }}
        </span>
        <span v-if="s.notes" class="notes">— {{ s.notes }}</span>
      </li>
    </ol>
  </div>
</template>

<style scoped>
.stage-list {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem 1.25rem;
}
.stage-list h3 {
  margin: 0 0 0.75rem;
  font-size: 0.95rem;
  color: #374151;
}
ol {
  margin: 0;
  padding-left: 1.5rem;
}
li {
  margin: 0.25rem 0;
  font-size: 0.875rem;
}
.icon {
  display: inline-block;
  width: 1.5rem;
}
.name {
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-weight: 500;
  margin-right: 0.5rem;
}
.status {
  font-size: 0.75rem;
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.05em;
  margin-right: 0.5rem;
}
.notes {
  color: #6b7280;
  font-size: 0.8125rem;
}
</style>