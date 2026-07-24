<template>
  <div
    class="app"
    :class="{ hover: isHovering }"
    :style="{ '--subtitle-color': playback?.subtitleColor || '#46b9ea' }"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
    @mousedown="startDrag"
  >
    <div class="overlay" />

    <div class="controls">
      <div ref="colorControlRef" class="color-control">
        <button
          class="ctrl-btn color-swatch"
          title="字幕文字颜色"
          :style="{ color: playback?.subtitleColor || '#46b9ea' }"
          @click="showColorPanel = !showColorPanel"
        />
        <div v-if="showColorPanel" class="color-popover">
          <button
            v-for="c in PRESET_COLORS"
            :key="c"
            class="color-dot"
            :class="{ active: c === (playback?.subtitleColor || '#46b9ea') }"
            :style="{ color: c }"
            :title="c"
            @click="selectColor(c)"
          />
          <label class="color-dot color-dot-custom" title="自定义颜色">
            <input
              type="color"
              :value="playback?.subtitleColor || '#46b9ea'"
              @input="onColorInput"
            >
          </label>
        </div>
      </div>
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
        v-if="currentWord && isExpression"
        ref="wordBlockRef"
        :key="currentWord.id"
        class="word-block"
      >
        <div class="word-text">
          {{ currentWord.phrase }}
        </div>
        <div class="word-meaning">
          {{ currentWord.meaning }}
        </div>
      </div>
      <div
        v-else-if="currentWord"
        ref="wordBlockRef"
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
        <div
          v-if="currentSentence"
          class="word-sentence"
        >
          <div class="sentence-en">
            {{ currentSentence.en_text }}
          </div>
          <div class="sentence-zh">
            {{ currentSentence.zh_text }}
          </div>
        </div>
      </div>
      <div
        v-else
        ref="wordBlockRef"
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
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { playWordAudio, playSentenceAudio, allSentences, playSentenceQueue } from '../utils/audio'

// 悬浮词幕条是主进程播放状态的纯展示层：不自己拉数据、不自己跑定时器
const playback = ref(null)
let unsubscribe = null
let unsubscribeAudio = null
let hoverLeaveTimer = null
const isHovering = ref(false)

// 字幕颜色：几个经典桌面歌词配色 + 最后一格自定义（原生颜色选择器）
const PRESET_COLORS = ['#46b9ea', '#ffd54f', '#7cfc8d', '#ff7ac6', '#ff9f43', '#ffffff', '#ff3b8d', '#b388ff']
const showColorPanel = ref(false)
const colorControlRef = ref(null)

function selectColor(color) {
  window.electronAPI?.setSubtitleColor(color)
  showColorPanel.value = false
}

function onDocumentClick(e) {
  if (showColorPanel.value && !colorControlRef.value?.contains(e.target)) {
    showColorPanel.value = false
  }
}

const currentWord = computed(() => playback.value?.currentWord || null)
const isExpression = computed(() => playback.value?.kind === 'expression')

// 当前正在播放的例句（多义词按顺序逐条播，播完清空）
const currentSentence = ref(null)

// 内容变化（比如接播例句）时窗口高度跟着变，宽度不变
const wordBlockRef = ref(null)
let resizeObserver = null
watch(wordBlockRef, (el, oldEl) => {
  if (oldEl && resizeObserver) resizeObserver.unobserve(oldEl)
  if (el && resizeObserver) resizeObserver.observe(el)
})

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
const onColorInput = (e) => window.electronAPI?.setSubtitleColor(e.target.value)

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
  if (e.target.closest('.ctrl-btn') || e.target.closest('.color-popover')) return
  e.preventDefault()
  dragStart = { x: e.screenX, y: e.screenY }
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
}

onMounted(async () => {
  document.addEventListener('click', onDocumentClick)
  resizeObserver = new ResizeObserver((entries) => {
    const h = entries[0]?.contentRect?.height
    if (h) window.electronAPI?.resizeBar(Math.ceil(h) + 24)
  })
  if (wordBlockRef.value) resizeObserver.observe(wordBlockRef.value)

  playback.value = await window.electronAPI?.getPlaybackState()
  unsubscribe = window.electronAPI?.onPlaybackState((state) => {
    playback.value = state
  })
  // 主界面关闭时，主进程会把发音事件定向发给词幕条
  unsubscribeAudio = window.electronAPI?.onPlayAudio((payload) => {
    currentSentence.value = null
    if (payload?.kind === 'expression') {
      playSentenceAudio(payload.audioUrl, () => window.electronAPI?.notifyAudioEnded())
      return
    }
    const afterWord = () => {
      if (!playback.value?.sentenceEnabled) {
        window.electronAPI?.notifyAudioEnded()
        return
      }
      const sentences = allSentences(currentWord.value)
      if (!sentences.length) {
        window.electronAPI?.notifyAudioEnded()
        return
      }
      playSentenceQueue(
        sentences,
        (s) => (currentSentence.value = s),
        () => {
          currentSentence.value = null
          window.electronAPI?.notifyAudioEnded()
        }
      )
    }
    if (payload?.skipWordAudio) {
      afterWord()
    } else {
      playWordAudio(payload?.text, afterWord)
    }
  })
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  clearTimeout(hoverLeaveTimer)
  if (unsubscribe) unsubscribe()
  if (unsubscribeAudio) unsubscribeAudio()
  resizeObserver?.disconnect()
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

.color-swatch {
  position: relative;
  overflow: hidden;
}

.color-swatch:hover {
  color: inherit;
  background: rgba(255, 255, 255, 0.12);
}

.color-swatch::after {
  content: '';
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.5);
}

.color-control {
  position: relative;
}

.color-popover {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px;
  border-radius: 10px;
  background: rgba(20, 22, 30, 0.92);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
  -webkit-app-region: no-drag;
  z-index: 3;
}

.color-dot {
  position: relative;
  width: 16px;
  height: 16px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.3);
  cursor: pointer;
  flex-shrink: 0;
}

.color-dot.active {
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.85);
}

.color-dot-custom {
  overflow: hidden;
  background: conic-gradient(red, yellow, lime, cyan, blue, magenta, red);
}

.color-dot-custom input[type='color'] {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: none;
  padding: 0;
  opacity: 0;
  cursor: pointer;
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
  text-align: left;
  color: var(--subtitle-color, #46b9ea);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
  word-break: break-word;
}

.word-text {
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 6px;
}

.word-meaning {
  color: var(--subtitle-color, #46b9ea);
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

.word-sentence {
  margin-top: 6px;
  color: var(--subtitle-color, #46b9ea);
  font-size: 13px;
  line-height: 1.5;
  width: 370px;
}

.sentence-zh {
  margin-top: 2px;
  opacity: 0.75;
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
