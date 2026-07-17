<template>
  <div class="player">
    <!-- 左侧：词库（歌单）栏 -->
    <aside class="sidebar">
      <div class="drag-strip"></div>
      <div class="user" v-if="user">
        <div class="avatar">
          <img v-if="user.avatar" :src="user.avatar" alt="" />
          <span v-else>{{ (user.nickname || user.username || '?').slice(0, 1).toUpperCase() }}</span>
        </div>
        <div class="user-name">{{ user.nickname || user.username }}</div>
      </div>

      <div class="nav-section">
        <div class="nav-item" :class="{ active: activeLibraryId === 'all' }" @click="selectLibrary('all')">
          <span class="nav-icon">♪</span>全部单词
        </div>
      </div>

      <div class="section-label">我的词库</div>
      <div class="library-list">
        <div v-for="lib in libraries" :key="lib.id" class="nav-item library-item"
          :class="{ active: activeLibraryId === lib.id }" @click="selectLibrary(lib.id)">
          <template v-if="renamingId === lib.id">
            <input v-model="renameText" class="inline-input" @keyup.enter="confirmRename(lib)"
              @keyup.esc="renamingId = null" @blur="confirmRename(lib)" v-focus />
          </template>
          <template v-else>
            <span class="lib-name">{{ lib.name }}</span>
            <span class="lib-count">{{ lib.word_count }}</span>
            <span class="lib-actions" v-if="lib.name !== '我的收藏'">
              <button class="mini-btn" title="重命名" @click.stop="startRename(lib)">✎</button>
              <button class="mini-btn" title="删除" @click.stop="removeLibrary(lib)">✕</button>
            </span>
          </template>
        </div>

        <div class="nav-item new-library" v-if="creatingLibrary">
          <input v-model="newLibraryName" class="inline-input" placeholder="词库名称" @keyup.enter="confirmCreate"
            @keyup.esc="creatingLibrary = false" @blur="confirmCreate" v-focus />
        </div>
        <div class="nav-item add-library" v-else @click="creatingLibrary = true">＋ 新建词库</div>
      </div>
    </aside>

    <!-- 中间：单词（歌曲）列表 -->
    <section class="content">
      <header class="content-header">
        <div class="header-titles">
          <h1 class="view-title">{{ activeLibraryName }}</h1>
          <span class="view-sub">{{ filteredWords.length }} 个单词</span>
        </div>
        <div class="header-actions">
          <input v-model="filterText" class="filter-input" placeholder="筛选单词…" />
          <button class="play-all-btn" :disabled="!filteredWords.length" @click="playFrom()">▶ 播放</button>
        </div>
      </header>

      <div class="table-wrap" @click="openMenuWordId = null">
        <table class="word-table">
          <thead>
            <tr>
              <th class="col-idx">#</th>
              <th>单词</th>
              <th class="col-phonetic">音标</th>
              <th>释义</th>
              <th class="col-ops"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(w, i) in filteredWords" :key="w.id" :class="{ playing: isPlayingRow(w) }"
              @dblclick="playFrom(i)">
              <td class="col-idx">
                <span v-if="isPlayingRow(w)" class="equalizer" :class="{ paused: !pb.playing }">
                  <i></i><i></i><i></i>
                </span>
                <span v-else class="row-num">{{ i + 1 }}</span>
                <button class="row-play" title="从这里播放" @click="playFrom(i)">▶</button>
              </td>
              <td class="col-word">{{ w.word }}</td>
              <td class="col-phonetic">{{ w.us_pronunciation || w.en_pronunciation }}</td>
              <td class="col-meaning">
                <span v-for="(m, mi) in w.meaning" :key="mi" class="meaning-item">
                  <i class="pos">{{ m.type }}</i>{{ m.content }}
                </span>
              </td>
              <td class="col-ops">
                <template v-if="activeLibraryId === 'all'">
                  <button class="op-btn" title="加入词库" @click.stop="openMenuWordId = openMenuWordId === w.id ? null : w.id">＋</button>
                  <div v-if="openMenuWordId === w.id" class="lib-menu" @click.stop>
                    <div v-for="lib in libraries" :key="lib.id" class="lib-menu-item" @click="addToLibrary(w, lib)">
                      {{ lib.name }}
                    </div>
                  </div>
                </template>
                <button v-else class="op-btn" title="移出词库" @click="removeFromLibrary(w)">✕</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="!loading && !filteredWords.length" class="empty">
          {{ filterText ? '没有匹配的单词' : activeLibraryId === 'all' ? '还没有单词，划词查询后收藏即可入库' : '词库还是空的，去「全部单词」里把单词加进来' }}
        </div>
      </div>

      <!-- 底部：播放条 -->
      <footer class="player-bar">
        <div class="now-playing">
          <transition name="fade" mode="out-in">
            <div v-if="pb.currentWord" class="now-word" :key="pb.currentWord.id || pb.currentWord.word">
              <div class="now-title">{{ pb.currentWord.word }}</div>
              <div class="now-sub">
                {{ firstMeaning(pb.currentWord) }}
              </div>
            </div>
            <div v-else class="now-word">
              <div class="now-sub">选一个词库，像放歌一样背单词</div>
            </div>
          </transition>
        </div>

        <div class="transport">
          <button class="t-btn" title="上一个" :disabled="!pb.total" @click="electronAPI?.playbackPrev()">⏮</button>
          <button class="t-btn t-play" :title="pb.playing ? '暂停' : '播放'" @click="togglePlay">
            {{ pb.playing ? '⏸' : '▶' }}
          </button>
          <button class="t-btn" title="下一个" :disabled="!pb.total" @click="electronAPI?.playbackNext()">⏭</button>
        </div>

        <div class="bar-right">
          <span class="playing-from" v-if="pb.total">{{ pb.libraryName }} · {{ pb.index + 1 }}/{{ pb.total }}</span>
          <button class="mode-btn" :title="pb.shuffle ? '随机播放' : '顺序播放'" @click="electronAPI?.setShuffle(!pb.shuffle)">
            {{ pb.shuffle ? '🔀 随机' : '→ 顺序' }}
          </button>
          <button class="mode-btn" :class="{ on: pb.audioEnabled }" title="切换单词时播放发音"
            @click="electronAPI?.setAudio(!pb.audioEnabled)">
            发音{{ pb.audioEnabled ? '开' : '关' }}
          </button>
          <button class="mode-btn" :class="{ on: pb.barVisible }" title="桌面词幕" @click="electronAPI?.toggleBar()">
            词幕{{ pb.barVisible ? '开' : '关' }}
          </button>
        </div>
      </footer>
    </section>

    <transition name="fade">
      <div v-if="toast" class="toast">{{ toast }}</div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onBeforeUnmount } from 'vue'
import http from '../api/http'
import { playWordAudio } from '../utils/audio'

const electronAPI = window.electronAPI

const user = ref(null)
const libraries = ref([])
const words = ref([])
const loading = ref(false)
const activeLibraryId = ref('all')
const filterText = ref('')
const openMenuWordId = ref(null)

const creatingLibrary = ref(false)
const newLibraryName = ref('')
const renamingId = ref(null)
const renameText = ref('')

const toast = ref('')
let toastTimer = null
let unsubscribe = null
let unsubscribeAudio = null
let unsubscribeCollected = null

// 主进程播放状态镜像
const pb = reactive({
  libraryId: null,
  libraryName: '',
  index: -1,
  total: 0,
  playing: false,
  shuffle: true,
  audioEnabled: true,
  barVisible: false,
  currentWord: null
})

const vFocus = { mounted: (el) => el.focus() }

const activeLibraryName = computed(() => {
  if (activeLibraryId.value === 'all') return '全部单词'
  return libraries.value.find((l) => l.id === activeLibraryId.value)?.name || ''
})

const filteredWords = computed(() => {
  const q = filterText.value.trim().toLowerCase()
  if (!q) return words.value
  return words.value.filter(
    (w) =>
      w.word.toLowerCase().includes(q) ||
      (w.meaning || []).some((m) => m.content.includes(q))
  )
})

function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 2000)
}

function firstMeaning(word) {
  const m = (word.meaning || [])[0]
  return m ? `${m.type} ${m.content}` : ''
}

function isPlayingRow(w) {
  return (
    pb.currentWord &&
    pb.currentWord.id === w.id &&
    String(pb.libraryId) === String(activeLibraryId.value)
  )
}

async function fetchUser() {
  const res = await http.get('/auth/me')
  if (res.data.code === 200) user.value = res.data.data
}

async function fetchLibraries() {
  const res = await http.get('/libraries/list')
  if (res.data.code === 200) libraries.value = res.data.data
}

async function fetchWords() {
  loading.value = true
  try {
    const url =
      activeLibraryId.value === 'all'
        ? '/words/list'
        : `/libraries/${activeLibraryId.value}/words`
    const res = await http.get(url, { params: { page: 1, page_size: 10000 } })
    words.value = res.data.code === 200 ? res.data.data || [] : []
  } finally {
    loading.value = false
  }
}

function selectLibrary(id) {
  if (activeLibraryId.value === id) return
  activeLibraryId.value = id
  filterText.value = ''
  openMenuWordId.value = null
  fetchWords()
}

// ---------- 播放 ----------
function playFrom(index) {
  const list = filteredWords.value
  if (!list.length) return
  electronAPI?.startPlayback({
    libraryId: activeLibraryId.value,
    libraryName: activeLibraryName.value,
    words: JSON.parse(JSON.stringify(list)),
    startIndex: Number.isInteger(index) ? index : undefined
  })
}

function togglePlay() {
  if (!pb.total) {
    playFrom()
    return
  }
  electronAPI?.setPlaying(!pb.playing)
}

// ---------- 词库管理 ----------
async function confirmCreate() {
  const name = newLibraryName.value.trim()
  creatingLibrary.value = false
  if (!name) return
  const res = await http.post('/libraries/add', { name })
  if (res.data.code === 200) {
    newLibraryName.value = ''
    await fetchLibraries()
  } else {
    showToast(res.data.msg)
  }
}

function startRename(lib) {
  renamingId.value = lib.id
  renameText.value = lib.name
}

async function confirmRename(lib) {
  const name = renameText.value.trim()
  renamingId.value = null
  if (!name || name === lib.name) return
  const res = await http.post(`/libraries/update?library_id=${lib.id}`, { name })
  if (res.data.code === 200) {
    await fetchLibraries()
  } else {
    showToast(res.data.msg)
  }
}

async function removeLibrary(lib) {
  if (!window.confirm(`删除词库「${lib.name}」？（单词本身会保留）`)) return
  const res = await http.post(`/libraries/delete?library_id=${lib.id}`)
  if (res.data.code === 200) {
    if (activeLibraryId.value === lib.id) {
      activeLibraryId.value = 'all'
      fetchWords()
    }
    await fetchLibraries()
  } else {
    showToast(res.data.msg)
  }
}

async function addToLibrary(word, lib) {
  openMenuWordId.value = null
  const res = await http.post('/libraries/add-word', { library_id: lib.id, word_id: word.id })
  showToast(res.data.code === 200 ? `已加入「${lib.name}」` : res.data.msg)
  if (res.data.code === 200) fetchLibraries()
}

async function removeFromLibrary(word) {
  const res = await http.post('/libraries/remove-word', {
    library_id: activeLibraryId.value,
    word_id: word.id
  })
  if (res.data.code === 200) {
    words.value = words.value.filter((w) => w.id !== word.id)
    fetchLibraries()
  } else {
    showToast(res.data.msg)
  }
}

onMounted(async () => {
  const state = await electronAPI?.getPlaybackState()
  if (state) Object.assign(pb, state)
  unsubscribe = electronAPI?.onPlaybackState((state) => Object.assign(pb, state))
  unsubscribeAudio = electronAPI?.onPlayAudio(playWordAudio)
  // 划词弹窗收藏成功 → 刷新列表和词库计数
  unsubscribeCollected = electronAPI?.onWordCollected((word) => {
    fetchWords()
    fetchLibraries()
    if (word && word.word) showToast(`已收藏「${word.word}」`)
  })

  fetchUser()
  await fetchLibraries()
  await fetchWords()
})

onBeforeUnmount(() => {
  if (unsubscribe) unsubscribe()
  if (unsubscribeAudio) unsubscribeAudio()
  if (unsubscribeCollected) unsubscribeCollected()
  clearTimeout(toastTimer)
})
</script>

<style scoped>
.player {
  --bg-deep: #12141d;
  --bg-side: #0d0f16;
  --bg-raised: #1a1e2a;
  --line: rgba(255, 255, 255, 0.06);
  --text: #e8ebf2;
  --dim: #8a90a3;
  --accent: #35a5ff;
  --accent-soft: rgba(53, 165, 255, 0.12);

  display: grid;
  grid-template-columns: 210px 1fr;
  width: 100%;
  height: 100vh;
  background: var(--bg-deep);
  color: var(--text);
  text-align: left;
  overflow: hidden;
  user-select: none;
}

/* ---------- 侧栏 ---------- */
.sidebar {
  background: var(--bg-side);
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 顶部留白给 macOS 红绿灯，兼作窗口拖拽区 */
.drag-strip {
  height: 40px;
  flex-shrink: 0;
  -webkit-app-region: drag;
}

.user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 16px 16px;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--accent-soft);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-section {
  padding: 0 8px;
}

.section-label {
  padding: 18px 16px 6px;
  font-size: 11px;
  letter-spacing: 0.12em;
  color: var(--dim);
}

.library-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 12px;
  min-height: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  color: var(--dim);
  position: relative;
}

.nav-item:hover {
  background: var(--bg-raised);
  color: var(--text);
}

.nav-item.active {
  background: var(--accent-soft);
  color: var(--accent);
}

.nav-icon {
  width: 16px;
  text-align: center;
}

.lib-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lib-count {
  font-size: 11px;
  color: var(--dim);
}

.lib-actions {
  display: none;
  gap: 2px;
}

.library-item:hover .lib-actions {
  display: flex;
}

.library-item:hover .lib-count {
  display: none;
}

.mini-btn {
  border: none;
  background: none;
  color: var(--dim);
  cursor: pointer;
  font-size: 12px;
  padding: 0 3px;
}

.mini-btn:hover {
  color: var(--accent);
}

.add-library {
  color: var(--dim);
  font-size: 12px;
}

.inline-input {
  width: 100%;
  background: var(--bg-raised);
  border: 1px solid var(--accent);
  border-radius: 4px;
  color: var(--text);
  font-size: 13px;
  padding: 3px 6px;
  outline: none;
}

/* ---------- 内容区 ---------- */
.content {
  display: grid;
  grid-template-rows: auto 1fr auto;
  min-width: 0;
  min-height: 0;
}

.content-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 40px 24px 14px;
  -webkit-app-region: drag;
}

.header-titles {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.view-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
}

.view-sub {
  font-size: 12px;
  color: var(--dim);
}

.header-actions {
  display: flex;
  gap: 10px;
  -webkit-app-region: no-drag;
}

.filter-input {
  width: 160px;
  background: var(--bg-raised);
  border: 1px solid var(--line);
  border-radius: 14px;
  color: var(--text);
  font-size: 12px;
  padding: 6px 12px;
  outline: none;
}

.filter-input:focus {
  border-color: var(--accent);
}

.play-all-btn {
  border: none;
  border-radius: 14px;
  background: var(--accent);
  color: #fff;
  font-size: 13px;
  padding: 6px 16px;
  cursor: pointer;
}

.play-all-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.table-wrap {
  overflow-y: auto;
  min-height: 0;
  padding: 0 12px;
}

.word-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.word-table th {
  position: sticky;
  top: 0;
  background: var(--bg-deep);
  text-align: left;
  font-size: 11px;
  font-weight: 500;
  color: var(--dim);
  padding: 6px 10px;
  border-bottom: 1px solid var(--line);
  z-index: 1;
}

.word-table td {
  padding: 9px 10px;
  border-bottom: 1px solid var(--line);
  vertical-align: middle;
}

.word-table tbody tr:hover {
  background: var(--bg-raised);
}

.word-table tbody tr.playing {
  color: var(--accent);
}

.col-idx {
  width: 44px;
  color: var(--dim);
  position: relative;
}

.row-num {
  font-variant-numeric: tabular-nums;
}

.row-play {
  display: none;
  position: absolute;
  left: 6px;
  top: 50%;
  transform: translateY(-50%);
  border: none;
  background: none;
  color: var(--accent);
  cursor: pointer;
  font-size: 12px;
}

tr:hover .row-num {
  visibility: hidden;
}

tr:hover .row-play {
  display: block;
}

/* 单词像词典词条：衬线体 */
.col-word {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 15px;
  font-weight: 600;
  width: 180px;
}

.col-phonetic {
  width: 150px;
  color: var(--dim);
  font-size: 12px;
}

.col-meaning {
  max-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--dim);
}

tr.playing .col-meaning,
tr.playing .col-phonetic {
  color: var(--accent);
  opacity: 0.85;
}

.meaning-item {
  margin-right: 10px;
}

.pos {
  font-style: normal;
  color: var(--accent);
  margin-right: 3px;
  opacity: 0.9;
}

.col-ops {
  width: 46px;
  text-align: right;
  position: relative;
}

.op-btn {
  visibility: hidden;
  border: none;
  background: none;
  color: var(--dim);
  font-size: 14px;
  cursor: pointer;
}

tr:hover .op-btn {
  visibility: visible;
}

.op-btn:hover {
  color: var(--accent);
}

.lib-menu {
  position: absolute;
  right: 30px;
  top: 50%;
  transform: translateY(-50%);
  background: var(--bg-raised);
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
  z-index: 5;
  min-width: 120px;
  overflow: hidden;
}

.lib-menu-item {
  padding: 7px 12px;
  font-size: 12px;
  color: var(--text);
  cursor: pointer;
  white-space: nowrap;
}

.lib-menu-item:hover {
  background: var(--accent-soft);
  color: var(--accent);
}

.empty {
  padding: 60px 0;
  text-align: center;
  color: var(--dim);
  font-size: 13px;
}

/* ---------- 播放条 ---------- */
.player-bar {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  background: var(--bg-side);
  border-top: 1px solid var(--line);
}

.now-playing {
  min-width: 0;
}

.now-title {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 17px;
  font-weight: 700;
}

.now-sub {
  font-size: 12px;
  color: var(--dim);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 320px;
}

.transport {
  display: flex;
  align-items: center;
  gap: 14px;
}

.t-btn {
  border: none;
  background: none;
  color: var(--text);
  font-size: 16px;
  cursor: pointer;
  padding: 4px;
}

.t-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.t-btn:hover:not(:disabled) {
  color: var(--accent);
}

.t-play {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.t-play:hover:not(:disabled) {
  color: #fff;
  filter: brightness(1.12);
}

.bar-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.playing-from {
  font-size: 11px;
  color: var(--dim);
}

.mode-btn {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: none;
  color: var(--dim);
  font-size: 11px;
  padding: 4px 10px;
  cursor: pointer;
}

.mode-btn:hover {
  color: var(--text);
}

.mode-btn.on {
  border-color: var(--accent);
  color: var(--accent);
}

/* ---------- 正在播放的均衡器动画（签名元素） ---------- */
.equalizer {
  display: inline-flex;
  align-items: flex-end;
  gap: 2px;
  height: 12px;
}

.equalizer i {
  width: 3px;
  background: var(--accent);
  animation: eq-bounce 0.9s ease-in-out infinite;
}

.equalizer i:nth-child(2) {
  animation-delay: 0.25s;
}

.equalizer i:nth-child(3) {
  animation-delay: 0.5s;
}

.equalizer.paused i {
  animation-play-state: paused;
}

@keyframes eq-bounce {

  0%,
  100% {
    height: 4px;
  }

  50% {
    height: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .equalizer i {
    animation: none;
    height: 8px;
  }
}

.toast {
  position: fixed;
  right: 20px;
  bottom: 76px;
  background: var(--bg-raised);
  border: 1px solid var(--line);
  color: var(--text);
  font-size: 12px;
  padding: 8px 14px;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
  z-index: 10;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
