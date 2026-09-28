<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">新建小说</h1>
    </div>

    <div class="create-layout">
      <!-- 左侧表单 -->
      <div class="create-form-area">
        <!-- 基本信息 -->
        <div class="section-card">
          <div class="section-title">基本信息</div>
          <el-form :model="form" label-position="top" size="large">
            <el-form-item label="小说标题" required>
              <el-input v-model="form.title" placeholder="给你的小说起个名字" maxlength="50" show-word-limit />
            </el-form-item>
            <el-form-item label="大纲方式">
              <el-radio-group v-model="outlineMode">
                <el-radio-button value="generate">AI 生成大纲</el-radio-button>
                <el-radio-button value="import">使用已有大纲</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="题材" required>
                  <el-select v-model="form.genre" placeholder="选择或输入题材" filterable allow-create style="width: 100%">
                    <el-option v-for="g in genres" :key="g" :label="g" :value="g" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="文风" required>
                  <el-select v-model="form.style" placeholder="选择或输入文风" filterable allow-create style="width: 100%">
                    <el-option v-for="s in styles" :key="s" :label="s" :value="s" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="版权查重阈值">
                  <el-slider v-model="copyrightThreshold" :min="5" :max="40" :step="5" :format-tooltip="(v: number) => `${v}%`" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <!-- 扫榜选标题（可选，仅 generate 模式显示） -->
        <div class="section-card" v-if="outlineMode === 'generate'">
          <div class="section-title">
            扫榜选标题
            <span class="scan-subtitle">基于平台榜单推荐选题（可选）</span>
          </div>

          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="平台">
                <el-select v-model="scanPlatform" style="width: 100%" @change="onScanPlatformChange">
                  <el-option v-for="p in scanPlatforms" :key="p.key" :label="p.label" :value="p.key">
                    <span>{{ p.label }}</span>
                    <el-tag
                      v-if="p.method === 'best-effort'"
                      size="small"
                      type="warning"
                      effect="plain"
                      style="margin-left: 6px"
                    >
                      尽力抓取
                    </el-tag>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="榜单">
                <el-select v-model="scanBoard" style="width: 100%" :disabled="!scanBoards.length">
                  <el-option v-for="b in scanBoards" :key="b.key" :label="b.label" :value="b.key" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4">
              <el-form-item label="样本数">
                <el-select v-model="scanLimit" style="width: 100%">
                  <el-option v-for="n in [30, 40, 60]" :key="n" :label="`Top ${n}`" :value="n" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="我的擅长 / 想写方向">
                <el-input v-model="authorDirection" placeholder="如：都市爽文、熟历史" clearable />
              </el-form-item>
            </el-col>
          </el-row>

          <div class="scan-actions">
            <el-button type="primary" plain :loading="scanFetching" :icon="Search" @click="handleScanFetch">
              {{ scanFetching ? '正在抓取样本，可能较慢...' : '抓取榜单' }}
            </el-button>
            <el-button
              v-if="scanQuality && scanQuality.level === 'failed'"
              type="warning"
              plain
              @click="handleScanRecommend(true)"
            >
              改用内置趋势知识推荐
            </el-button>
            <el-button
              type="primary"
              :loading="recommending"
              :disabled="!scanRows.length && !scanQuality"
              :icon="MagicStick"
              @click="handleScanRecommend(false)"
            >
              {{ recommending ? 'AI 选题分析中...' : 'AI 选题·推荐' }}
            </el-button>
          </div>
          <div v-if="scanMethodLabel" class="config-hint">
            平台抓取方式：{{ scanMethodLabel }}
          </div>

          <!-- 抓取结果样本 -->
          <template v-if="scanRows.length">
            <el-divider class="world-divider" />
            <div class="scan-result-head">
              <span class="config-hint">
                抓到 <strong>{{ scanRows.length }}</strong> 条样本（
                <span v-if="scanQuality">
                  <el-tag :type="qualityTagType(scanQuality.level)" size="small" effect="plain">
                    {{ qualityLabel(scanQuality.level) }}
                  </el-tag>
                  <span v-if="scanQuality.parse_rate != null" class="config-hint" style="margin-left: 6px">
                    标题解析率 {{ (scanQuality.parse_rate * 100).toFixed(0) }}%
                  </span>
                </span>
                ）
              </span>
              <span v-if="scanIssues.length" class="scan-issues">
                {{ scanIssues.join('；') }}
              </span>
            </div>
            <el-table :data="scanRows" size="small" max-height="260" style="width: 100%">
              <el-table-column prop="rank" label="#" width="46" />
              <el-table-column prop="title" label="书名" min-width="150" show-overflow-tooltip />
              <el-table-column prop="genre" label="题材" width="120" show-overflow-tooltip />
              <el-table-column label="核心指标" min-width="110">
                <template #default="{ row }">
                  {{ row.metric_label }}{{ row.metric }}
                </template>
              </el-table-column>
              <el-table-column prop="author" label="作者" width="110" show-overflow-tooltip />
              <el-table-column prop="words" label="字数" width="96" show-overflow-tooltip />
            </el-table>
          </template>

          <!-- AI 选题弹窗：点击「AI 选题·推荐」即弹出 → 分析进度 → 候选结果（可采纳回填） -->
          <el-dialog
            v-model="recDialogVisible"
            :title="recommending ? 'AI 选题分析中…' : (recError ? 'AI 选题失败' : 'AI 选题·候选推荐')"
            width="760px"
            top="6vh"
            append-to-body
            :close-on-click-modal="false"
          >
            <!-- 1) 分析进度 -->
            <div v-if="recommending" class="rec-dialog-loading">
              <el-icon class="is-loading rec-dialog-loading__icon"><Loading /></el-icon>
              <p>AI 正在分析市场趋势并生成候选选题，通常需要 30~90 秒…</p>
              <p class="config-hint">流程：先做趋势报告，再依据榜单样本产出候选方案</p>
            </div>

            <!-- 2) 失败 -->
            <div v-else-if="recError">
              <el-alert :title="recError" type="error" :closable="false" show-icon />
              <div class="rec-dialog-actions">
                <el-button @click="recDialogVisible = false">关闭</el-button>
                <el-button type="primary" @click="handleScanRecommend(lastRecBuiltin)">重试</el-button>
              </div>
            </div>

            <!-- 3) 空结果 -->
            <div v-else-if="!recommendations.length">
              <el-empty description="未生成可用选题，可调整方向后重试">
                <el-button @click="recDialogVisible = false">关闭</el-button>
                <el-button type="primary" @click="handleScanRecommend(lastRecBuiltin)">重新生成</el-button>
              </el-empty>
            </div>

            <!-- 4) 候选列表 -->
            <template v-else>
              <div class="scan-result-head" style="margin-bottom: 8px">
                <span v-if="recommendMode === 'builtin'" class="scan-mode-note">
                  ⚠️ 基于内置知识推荐，无榜单验证，仅供参考
                </span>
                <span v-else class="config-hint">已基于本次榜单快照分析</span>
              </div>
              <div v-for="(rec, idx) in recommendations" :key="idx" class="rec-card">
                <div class="rec-card__main">
                  <div class="rec-card__title">
                    {{ rec.title }}
                    <el-tag :type="feasibilityTag(rec.feasibility)" size="small">
                      可行性 {{ rec.feasibility }}
                    </el-tag>
                  </div>
                  <div class="rec-card__alts" v-if="rec.alt_titles && rec.alt_titles.length">
                    <span class="rec-label">备选：</span>
                    <el-tag v-for="a in rec.alt_titles" :key="a" size="small" effect="plain" type="info" class="rec-alt">
                      {{ a }}
                    </el-tag>
                  </div>
                  <div v-if="rec.selling_point" class="rec-selling">「{{ rec.selling_point }}」</div>
                  <div class="rec-tags">
                    <el-tag v-if="rec.genre_combo" size="small" effect="plain">题材：{{ rec.genre_combo }}</el-tag>
                    <el-tag v-if="rec.style_suggestion" size="small" effect="plain" type="success">
                      文风：{{ rec.style_suggestion }}
                    </el-tag>
                    <el-tooltip
                      v-if="rec.gold_finger"
                      :content="rec.gold_finger"
                      placement="top"
                      :show-after="200"
                      :disabled="rec.gold_finger.length <= 60"
                    >
                      <div class="rec-gold-finger">金手指：{{ rec.gold_finger }}</div>
                    </el-tooltip>
                  </div>
                </div>
                <div class="rec-card__aside">
                  <el-button type="primary" plain size="small" @click="adoptRec(rec)">采纳此选题</el-button>
                  <el-button text size="small" @click="toggleRec(idx)">
                    {{ openRec.has(idx) ? '收起论证' : '为什么能爆' }}
                  </el-button>
                </div>
                <div v-if="openRec.has(idx)" class="rec-card__detail">
                  <p v-if="rec.why_explode"><span class="rec-label">为什么能爆（待拆文验证）：</span>{{ rec.why_explode }}</p>
                  <p v-if="rec.differentiation"><span class="rec-label">差异化：</span>{{ rec.differentiation }}</p>
                  <p v-if="rec.risk"><span class="rec-label">失败风险：</span>{{ rec.risk }}</p>
                  <p v-if="rec.verify_action"><span class="rec-label">验证动作：</span>{{ rec.verify_action }}</p>
                  <p v-if="rec.feasibility_reason"><span class="rec-label">可行性判据：</span>{{ rec.feasibility_reason }}</p>
                </div>
              </div>
              <div v-if="scanWarnings.length" class="config-hint scan-issues">
                {{ scanWarnings.join('；') }}
              </div>
            </template>

            <template #footer>
              <div class="rec-dialog-footer">
                <span class="config-hint">点击「采纳此选题」会回填标题/题材/文风到表单，可继续修改</span>
                <el-button v-if="!recommending" type="primary" plain @click="recDialogVisible = false">完成</el-button>
              </div>
            </template>
          </el-dialog>
        </div>

        <!-- 世界观设定 -->
        <div class="section-card">
          <div class="section-title">世界观设定</div>

          <div class="world-setting-input">
            <el-input
              v-model="form.world_setting"
              type="textarea"
              :rows="5"
              placeholder="一句话创意或世界观草稿：描述时代背景、社会生态、核心冲突...（可让 AI 扩写为完整设定）"
              maxlength="2000"
              show-word-limit
            />
            <el-button
              v-if="outlineMode === 'generate'"
              type="primary"
              plain
              :loading="worldLoading"
              :icon="MagicStick"
              @click="handleGenerateWorld"
            >
              {{ worldLoading ? '世界观生成中...' : 'AI 生成世界观' }}
            </el-button>
          </div>
          <div class="config-hint">
            点击「AI 生成世界观」将根据标题、题材、文风与上面输入的内容，生成完整世界观叙述，并同步推导出
            力量规则 / 金手指 / 势力格局 / 题材正文提示卡（可在下方扩展设定中查看与修改）。
          </div>

          <el-divider class="world-divider" />

          <!-- 扩展设定（可折叠） -->
          <div class="world-advanced-toggle" @click="advancedOpen = !advancedOpen">
            <span>扩展设定：力量规则 / 金手指 / 势力 / 题材卡</span>
            <el-icon class="world-advanced-arrow">
              <component :is="advancedOpen ? ArrowUp : ArrowDown" />
            </el-icon>
          </div>
          <template v-if="advancedOpen">
            <div v-for="f in worldExtFields" :key="f.key" class="world-ext-field">
              <div class="world-ext-label">{{ f.label }}</div>
              <el-input
                v-model="form[f.key]"
                type="textarea"
                :rows="f.rows"
                :placeholder="f.hint"
              />
            </div>
          </template>
        </div>

        <!-- 已有大纲输入 -->
        <div class="section-card" v-if="outlineMode === 'import'">
          <div class="section-title">粘贴大纲</div>
          <el-input
            v-model="existingOutline"
            type="textarea"
            :rows="15"
            placeholder="粘贴你的小说大纲，系统会自动解析题材、文风、章节数等信息..."
          />
          <div class="config-hint">系统将自动从大纲中提取题材、文风、章节数等配置信息</div>
        </div>

        <!-- 章节配置 -->
        <div class="section-card" v-if="outlineMode === 'generate'">
          <div class="section-title">章节配置</div>
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="总章节数">
                <el-input-number v-model="form.chapter_count" :min="50" :max="500" :step="10" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="每章目标字数">
                <el-input-number v-model="form.words_per_chapter" :min="2000" :max="5000" :step="500" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          <div class="config-hint">
            预计总字数：<strong>{{ ((form.chapter_count * form.words_per_chapter) / 10000).toFixed(1) }} 万字</strong>
          </div>
        </div>

        <!-- 角色设定 -->
        <div class="section-card" v-if="outlineMode === 'generate'">
          <div class="section-title">
            角色设定
            <el-button type="primary" text :icon="Plus" @click="addCharacter" style="margin-left: auto">
              添加角色
            </el-button>
          </div>

          <div v-for="(char, index) in form.characters" :key="index" class="character-card">
            <div class="character-card__header">
              <span class="character-index">#{{ index + 1 }}</span>
              <el-tag :type="roleTagType(char.role_type)" size="small" effect="plain">
                {{ roleLabels[char.role_type] }}
              </el-tag>
              <el-button
                v-if="form.characters.length > 1"
                text
                type="danger"
                size="small"
                :icon="Delete"
                @click="form.characters.splice(index, 1)"
              />
            </div>
            <el-row :gutter="12">
              <el-col :span="6">
                <el-input v-model="char.name" placeholder="角色名" />
              </el-col>
              <el-col :span="6">
                <el-select v-model="char.role_type" placeholder="角色类型" style="width: 100%">
                  <el-option label="主角" value="protagonist" />
                  <el-option label="反派" value="antagonist" />
                  <el-option label="配角" value="supporting" />
                </el-select>
              </el-col>
              <el-col :span="6">
                <el-input v-model="char.personality" placeholder="性格特征" />
              </el-col>
              <el-col :span="6">
                <el-input v-model="char.background" placeholder="身世背景" />
              </el-col>
            </el-row>
          </div>
        </div>
      </div>

      <!-- 右侧预览 -->
      <div class="create-preview">
        <div class="section-card sticky-card">
          <div class="section-title">配置预览</div>
          <div class="preview-item">
            <span class="preview-label">标题</span>
            <span class="preview-value">{{ form.title || '未填写' }}</span>
          </div>
          <div class="preview-item">
            <span class="preview-label">题材</span>
            <span class="preview-value">{{ form.genre }}</span>
          </div>
          <div class="preview-item">
            <span class="preview-label">文风</span>
            <span class="preview-value">{{ form.style }}</span>
          </div>
          <div class="preview-item">
            <span class="preview-label">规模</span>
            <span class="preview-value">{{ form.chapter_count }} 章 / {{ form.words_per_chapter }} 字/章</span>
          </div>
          <div class="preview-item">
            <span class="preview-label">角色</span>
            <span class="preview-value">{{ form.characters.filter(c => c.name).map(c => c.name).join('、') || '未填写' }}</span>
          </div>
          <div class="preview-item">
            <span class="preview-label">查重阈值</span>
            <span class="preview-value">{{ copyrightThreshold }}%</span>
          </div>

          <el-divider />

          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleCreate"
            style="width: 100%"
          >
            {{ outlineMode === 'import' ? '创建项目并导入大纲' : '创建项目并生成大纲' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNovelStore } from '@/stores/novel'
import { ElMessage } from 'element-plus'
import { Plus, Delete, MagicStick, ArrowUp, ArrowDown, Search, Loading } from '@element-plus/icons-vue'
import api from '@/services/api'

const router = useRouter()
const novelStore = useNovelStore()
const loading = ref(false)
const worldLoading = ref(false)
const copyrightThreshold = ref(20)
const outlineMode = ref<'generate' | 'import'>('generate')
const existingOutline = ref('')
const advancedOpen = ref(false)

// 世界观结构化扩展字段（对应后端 novel_projects 上的可选设定字段）
const worldExtFields = [
  { key: 'world_rules', label: '力量体系 / 世界规则', rows: 3, hint: '修炼/力量体系、等级、规则与代价（AI 生成，可手改）' },
  { key: 'gold_finger', label: '金手指', rows: 3, hint: '主角金手指的机制、成长、代价与风险' },
  { key: 'factions', label: '势力格局', rows: 3, hint: '主要势力、阵营关系与立场' },
  { key: 'genre_card', label: '题材正文提示卡', rows: 3, hint: '本题材行文要求，写作正文时必须遵守' },
] as const

const genres = ['玄幻', '都市', '科幻', '仙侠', '历史', '悬疑', '言情', '武侠']
const styles = ['热血', '轻松', '严肃', '幽默', '暗黑', '沉稳', '唯美']
const roleLabels: Record<string, string> = { protagonist: '主角', antagonist: '反派', supporting: '配角' }

const form = reactive({
  title: '',
  genre: '玄幻',
  style: '热血',
  world_setting: '',
  world_rules: '',
  gold_finger: '',
  factions: '',
  genre_card: '',
  chapter_count: 100,
  words_per_chapter: 3000,
  characters: [
    { name: '', role_type: 'protagonist', personality: '', background: '', relationships: [] }
  ]
})

/* ===== 扫榜选标题 ===== */
interface ScanPlatform { key: string; label: string; method: string; boards: ScanBoard[] }
interface ScanBoard { key: string; label: string; [k: string]: any }
interface ScanRow { rank?: number; title: string; genre: string; metric: string; metric_label: string; author: string; words: string }
interface ScanQuality { level: 'ok' | 'sparse' | 'failed'; valid_count: number; parse_rate: number | null; issues: string[] }
interface Rec {
  title: string
  alt_titles: string[]
  selling_point: string
  genre_combo: string
  style_suggestion: string
  gold_finger: string
  why_explode: string
  differentiation: string
  risk: string
  verify_action: string
  feasibility: string
  feasibility_reason: string
}

const scanPlatforms = ref<ScanPlatform[]>([])
const scanPlatform = ref('qidian')
const scanBoard = ref('')
const scanLimit = ref(30)
const authorDirection = ref('')
const scanFetching = ref(false)
const scanRows = ref<ScanRow[]>([])
const scanQuality = ref<ScanQuality | null>(null)
const scanSnapshotId = ref('')
const scanIssues = ref<string[]>([])
const recommending = ref(false)
const recommendations = ref<Rec[]>([])
const recommendMode = ref<'real' | 'builtin'>('real')
const scanWarnings = ref<string[]>([])
// AI 选题弹窗
const recDialogVisible = ref(false)
const recError = ref('')
const lastRecBuiltin = ref(false)
const openRec = ref(new Set<number>())

const scanBoards = computed(() => scanPlatforms.value.find((p) => p.key === scanPlatform.value)?.boards || [])
const currentPlatform = computed(() => scanPlatforms.value.find((p) => p.key === scanPlatform.value))
const scanMethodLabel = computed(() => {
  const p = currentPlatform.value
  if (!p) return ''
  return p.method === 'pure-http'
    ? `${p.label}（纯 HTTP 抓取）`
    : `${p.label}（尽力抓取：纯 HTTP 优先，失败自动走浏览器/降级）`
})

function qualityLabel(level: string) {
  return { ok: '数据良好', sparse: '样本稀疏', failed: '抓取失败' }[level] || level
}
function qualityTagType(level: string) {
  return { ok: 'success', sparse: 'warning', failed: 'danger' }[level] || 'info'
}
function feasibilityTag(f: string) {
  return { 高: 'success', 中: 'warning', 低: 'danger' }[f] || 'info'
}

async function loadScanPlatforms() {
  try {
    const res = await api.get('/novel/scan/platforms')
    const list: ScanPlatform[] = res.data?.platforms || []
    scanPlatforms.value = list
    if (list.length) {
      scanPlatform.value = list[0].key
      onScanPlatformChange()
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '扫榜平台配置加载失败')
  }
}
function onScanPlatformChange() {
  const p = currentPlatform.value
  scanBoard.value = p?.boards?.[0]?.key || ''
}
async function handleScanFetch() {
  if (!scanPlatform.value || !scanBoard.value) {
    ElMessage.warning('请选择平台与榜单')
    return
  }
  scanFetching.value = true
  scanWarnings.value = []
  recommendations.value = []
  try {
    const res = await api.post('/novel/scan/fetch', {
      platform: scanPlatform.value,
      board: scanBoard.value,
      limit: scanLimit.value,
    })
    const data: any = res.data
    scanRows.value = data.entries || []
    scanQuality.value = data.quality
    scanSnapshotId.value = data.snapshot_id || ''
    scanIssues.value = data.quality?.issues || []
    if (data.quality?.level === 'failed') {
      ElMessage.warning('该榜单抓取失败或无有效样本，可改用「内置趋势知识推荐」')
    } else {
      ElMessage.success(`已抓到 ${scanRows.value.length} 条${currentPlatform.value?.label || ''}样本`)
    }
  } catch (e: any) {
    scanRows.value = []
    scanSnapshotId.value = ''
    ElMessage.error(e.response?.data?.detail || '榜单抓取失败，请稍后重试')
  } finally {
    scanFetching.value = false
  }
}
async function handleScanRecommend(builtin: boolean) {
  lastRecBuiltin.value = builtin
  recError.value = ''
  recommendations.value = []
  recommendMode.value = 'real'
  scanWarnings.value = []
  recDialogVisible.value = true // 点击即弹：先展示分析进度
  recommending.value = true
  try {
    const res = await api.post('/novel/scan/recommend', {
      snapshot_id: builtin ? null : (scanSnapshotId.value || null),
      builtin_mode: builtin,
      author_context: { preferred_genre: authorDirection.value, strengths: '', constraints: '' },
    })
    const data: any = res.data
    recommendations.value = data.recommendations || []
    recommendMode.value = data.mode
    scanWarnings.value = data.warnings || []
  } catch (e: any) {
    recError.value = e.response?.data?.detail || 'AI 选题失败，请稍后重试'
  } finally {
    recommending.value = false
  }
}
function toggleRec(idx: number) {
  const s = new Set(openRec.value)
  if (s.has(idx)) s.delete(idx)
  else s.add(idx)
  openRec.value = s
}
function adoptRec(rec: Rec) {
  if (!rec.title) return
  form.title = rec.title
  if (rec.genre_combo) form.genre = rec.genre_combo
  if (rec.style_suggestion) form.style = rec.style_suggestion
  const block = rec.selling_point ? `【推荐卖点】${rec.selling_point}` : ''
  const base = form.world_setting.replace(/^【推荐卖点】[^\n]*\n*/, '').trim()
  form.world_setting = block ? (base ? `${block}\n\n${base}` : block) : base || form.world_setting
  recDialogVisible.value = false // 采纳后关闭弹窗，回到表单继续编辑
  ElMessage.success('已采纳：标题/题材/文风已预填，卖点已置于世界观设定最前')
}
onMounted(loadScanPlatforms)

function addCharacter() {
  form.characters.push({ name: '', role_type: 'supporting', personality: '', background: '', relationships: [] })
}

function roleTagType(type: string) {
  return { protagonist: 'danger', antagonist: 'warning', supporting: 'info' }[type] || 'info'
}

async function handleGenerateWorld() {
  if (!form.title.trim()) {
    ElMessage.warning('请先填写小说标题')
    return
  }
  if (!form.genre) {
    ElMessage.warning('请先选择题材')
    return
  }
  worldLoading.value = true
  try {
    const res = await api.post('/novel/settings/generate-world', {
      title: form.title.trim(),
      genre: form.genre,
      style: form.style,
      seed: form.world_setting,
    })
    const data: any = res.data || {}
    let generated = 0
    if (data.world_setting) {
      form.world_setting = data.world_setting
      generated++
    }
    for (const f of worldExtFields) {
      if (data[f.key]) {
        ;(form as any)[f.key] = data[f.key]
        generated++
      }
    }
    if (generated > 0) {
      advancedOpen.value = true
      ElMessage.success(`世界观生成完成：已填充 ${generated} 项设定，请在下方扩展设定中审阅修改`)
    } else {
      ElMessage.warning('生成结果为空，请调整题材/文风后重试')
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '世界观生成失败，请稍后重试')
  } finally {
    worldLoading.value = false
  }
}

async function handleCreate() {
  if (!form.title) {
    ElMessage.warning('请填写标题')
    return
  }
  if (outlineMode.value === 'import') {
    if (!existingOutline.value.trim()) {
      ElMessage.warning('请粘贴大纲内容')
      return
    }
  } else {
    if (!form.world_setting) {
      ElMessage.warning('请填写世界观设定')
      return
    }
  }
  loading.value = true
  try {
    const payload: any = { ...form }
    if (outlineMode.value === 'import') {
      payload.existing_outline = existingOutline.value
    }
    const result = await novelStore.createNovel(payload)
    if (result?.error || !result?.project_id) {
      ElMessage.error(result?.error || '创建失败，请稍后重试')
      return
    }
    ElMessage.success(outlineMode.value === 'import' ? '项目创建成功，大纲已导入' : '项目创建成功，大纲生成中...')
    router.push(`/novel/${result.project_id}`)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.create-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: var(--space-lg);
  align-items: start;
}

.section-card + .section-card {
  margin-top: var(--space-md);
}

.character-card {
  background: var(--color-bg-page);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  margin-bottom: var(--space-sm);
}

.character-card__header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.character-index {
  font-size: var(--font-size-xs);
  color: var(--color-text-placeholder);
  font-weight: 600;
}

.config-hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--space-sm);
}

.config-hint strong {
  color: var(--color-primary);
}

.world-setting-input {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
}

.world-setting-input .el-input {
  flex: 1;
}

.world-setting-input .el-button {
  margin-top: 4px;
  flex-shrink: 0;
}

.world-divider {
  margin: var(--space-md) 0 var(--space-sm);
}

.world-advanced-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: var(--space-sm) 0;
  user-select: none;
}

.world-advanced-toggle:hover {
  color: var(--color-primary);
}

.world-advanced-arrow {
  transition: transform 0.2s;
}

.world-ext-field {
  margin-bottom: var(--space-sm);
}

.world-ext-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: 4px;
  font-weight: 500;
}

.sticky-card {
  position: sticky;
  top: calc(var(--topbar-height) + var(--space-lg));
}

.preview-item {
  display: flex;
  justify-content: space-between;
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--color-border-light);
}

.preview-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.preview-value {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  font-weight: 500;
  text-align: right;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ---- 扫榜选标题 ---- */
.scan-subtitle {
  font-size: var(--font-size-xs);
  color: var(--color-text-placeholder);
  font-weight: 400;
  margin-left: var(--space-sm);
}

.scan-actions {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-top: var(--space-xs);
}

.scan-result-head {
  display: flex;
  align-items: baseline;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: var(--space-sm);
}

.scan-mode-note {
  font-size: var(--font-size-sm);
  color: var(--color-warning);
  font-weight: 500;
}

.scan-issues {
  color: var(--color-warning);
}

.rec-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  margin-bottom: var(--space-sm);
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.rec-card__main {
  flex: 1 1 360px;
  min-width: 0;
}

.rec-card__title {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-primary);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: var(--space-xs);
}

.rec-card__alts {
  margin-bottom: var(--space-xs);
}

.rec-alt {
  margin-right: 4px;
}

.rec-selling {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-xs);
}

.rec-tags {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
  align-items: flex-start;
}

.rec-gold-finger {
  /* 模仿 el-tag warning small 的视觉：圆角 + 浅色底 + 警告色边框文字 */
  max-width: 100%;
  align-self: flex-start; /* flex 容器中不要被拉伸到全宽 */
  padding: 1px 10px;
  font-size: 12px;
  line-height: 20px;
  border-radius: 4px;
  background-color: var(--el-color-warning-light-9, #fdf6ec);
  color: var(--el-color-warning-dark-2, #b88230);
  border: 1px solid var(--el-color-warning-light-7, #faecd8);
  word-break: break-word;
  overflow-wrap: anywhere;
  text-align: left;
  cursor: help;
  box-sizing: border-box;
  /* 多行截断：最多 2 行 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rec-card__aside {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  align-items: flex-end;
  flex-shrink: 0;
}

.rec-card__detail {
  flex-basis: 100%;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  border-top: 1px dashed var(--color-border);
  padding-top: var(--space-sm);
}

.rec-card__detail p {
  margin: 0 0 var(--space-xs);
}

.rec-label {
  color: var(--color-text-placeholder);
  font-weight: 500;
}

/* AI 选题弹窗 */
.rec-dialog-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xl) 0;
  text-align: center;
  color: var(--color-text-secondary);
}

.rec-dialog-loading p {
  margin: 0;
}

.rec-dialog-loading__icon {
  font-size: 40px;
  color: var(--color-primary);
}

.rec-dialog-actions {
  margin-top: 16px;
  text-align: right;
}

.rec-dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.rec-dialog-footer .config-hint {
  margin-top: 0;
}
</style>
