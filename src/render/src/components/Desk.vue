<template>
  <div
    class="app"
    :class="{ hover: isHovering }"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
    @mousedown="startDrag"
  >
    <div class="overlay" />

    <div class="controls">
      <button
        class="ctrl-btn"
        title="最小化"
        @click="minimize"
      >
        <span
          class="ctrl-btn-icon ctrl-btn-icon--minimize"
        />
      </button>
      <button
        class="ctrl-btn"
        title="关闭"
        @click="closeWindow"
      >
        <span
          class="ctrl-btn-icon ctrl-btn-icon--close"
        />
      </button>
    </div>

    <transition
      name="fade"
      mode="out-in"
    >
      <div
        v-if="currentWord"
        :key="currentWord.id || currentWord.word"
        class="word-block"
      >
        <div class="word-text">
          {{ currentWord.word }}
        </div>
        <div
          v-for="(m, i) in (currentWord.meaning || []).slice(0, 2)"
          :key="i"
          class="word-meaning"
        >
          <span>{{ m.type }}</span>{{ m.content }}
        </div>
      </div>
      <div
        v-else
        class="word-block"
      >
        <div class="word-meaning">
          在主界面选择词库开始播放
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { playWordAudio, playSentenceAudio, firstSentenceAudioUrl } from '../utils/audio'

// 悬浮词幕条是主进程播放状态的纯展示层：不自己拉数据、不自己跑定时器
const playback = ref(null)
let unsubscribe = null
let unsubscribeAudio = null
let hoverLeaveTimer = null
const isHovering = ref(false)

const currentWord = computed(() => playback.value?.currentWord || null)

const onMouseEnter = () => {
  clearTimeout(hoverLeaveTimer)
  isHovering.value = true
  window.electronAPI?.setPlaying(false)
}

const onMouseLeave = () => {
  // 短暂延迟再隐藏，鼠标移向按钮途中稍微划出窗口边界不会立刻收起控制条
  hoverLeaveTimer = setTimeout(() => {
    isHovering.value = false
    window.electronAPI?.playbackNext() // 恢复轮播时立刻切一次，不用再等一整个间隔周期
    window.electronAPI?.setPlaying(true)
  }, 300)
}

const minimize = () => window.electronAPI?.minimizeWindow()
const closeWindow = () => window.electronAPI?.closeWindow()

// 自定义拖拽：不用 -webkit-app-region: drag，避免和 hover 事件冲突
let dragStart = null

const onDrag = (e) => {
  if (!dragStart) return
  const dx = e.screenX - dragStart.x
  const dy = e.screenY - dragStart.y
  dragStart = { x: e.screenX, y: e.screenY }
  window.electronAPI?.moveWindowBy(dx, dy)
}

const stopDrag = () => {
  dragStart = null
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
}

const startDrag = (e) => {
  if (e.target.closest('.ctrl-btn')) return
  e.preventDefault()
  dragStart = { x: e.screenX, y: e.screenY }
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
}

onMounted(async () => {
  playback.value = await window.electronAPI?.getPlaybackState()
  unsubscribe = window.electronAPI?.onPlaybackState((state) => {
    playback.value = state
  })
  // 主界面关闭时，主进程会把发音事件定向发给词幕条
  unsubscribeAudio = window.electronAPI?.onPlayAudio((word) => {
    playWordAudio(word, () => {
      const url = firstSentenceAudioUrl(currentWord.value)
      if (url) playSentenceAudio(url)
    })
  })
})

onBeforeUnmount(() => {
  clearTimeout(hoverLeaveTimer)
  if (unsubscribe) unsubscribe()
  if (unsubscribeAudio) unsubscribeAudio()
  stopDrag()
})
</script>

<style scoped>
.app {
  position: relative;
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  background: transparent;
  overflow: hidden;
  padding: 12px;
  user-select: none;
  cursor: default;
}

.overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.app.hover .overlay {
  opacity: 1;
}

.controls {
  position: absolute;
  top: 5px;
  right: 30px;
  display: flex;
  gap: 5px;
  opacity: 0;
  transition: opacity 0.2s ease;
  -webkit-app-region: no-drag;
  z-index: 2;
}

.app.hover .controls {
  opacity: 1;
}

.ctrl-btn {
  width: 20px;
  height: 20px;
  padding: 0;
  margin: 0;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.65);
  font-size: 16px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease;
}

.ctrl-btn:hover {
  color: rgb(236, 68, 68);
  background: rgba(255, 255, 255, 0.12);
}

.ctrl-btn-icon {
  display: block;
  position: relative;
  width: 10px;
  height: 10px;
}

.ctrl-btn-icon--minimize {
  height: 1.4px;
  align-self: center;
  background: currentColor;
}

.ctrl-btn-icon--close::before,
.ctrl-btn-icon--close::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 10px;
  height: 1.4px;
  background: currentColor;
}

.ctrl-btn-icon--close::before {
  transform: translate(-50%, -50%) rotate(45deg);
}

.ctrl-btn-icon--close::after {
  transform: translate(-50%, -50%) rotate(-45deg);
}

.word-block {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  max-height: 100%;
  overflow: hidden;
  text-align: left;
  color: rgb(70, 185, 234);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.95), 0 0 2px rgba(0, 0, 0, 0.9);
  word-break: break-word;
}

.word-text {
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 6px;
}

.word-meaning {
  color: rgb(70, 185, 234);
  font-size: 14px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  width: 370px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.word-type {
  margin-right: 4px;
  font-weight: 600;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.6s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
