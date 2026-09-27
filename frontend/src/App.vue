<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="app">
    <header class="app-header">
      <h1>📖 auto_novels</h1>
      <p class="subtitle">多 agent 网文写作 · demo</p>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
    <footer class="app-footer">
      <span>nginx · vue · fastapi · langgraph · pg</span>
    </footer>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Hiragino Sans GB', sans-serif;
}
.app-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #eee;
  background: #fafafa;
}
.app-header h1 {
  margin: 0;
  font-size: 1.5rem;
}
.subtitle {
  margin: 0.25rem 0 0;
  color: #888;
  font-size: 0.875rem;
}
.app-main {
  flex: 1;
  padding: 2rem;
  max-width: 960px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}
.app-footer {
  padding: 1rem 2rem;
  border-top: 1px solid #eee;
  font-size: 0.75rem;
  color: #aaa;
  text-align: center;
}
</style>