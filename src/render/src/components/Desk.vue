<template>
  <div class="app">
    <div class="swiper-container" @mouseenter="pauseAutoplay" @mouseleave="resumeAutoplay">
      <swiper :modules="modules" :direction="'vertical'" :slides-per-view="3" :space-between="10" :centeredSlides="true"
        :autoplay="autoplayConfig" @swiper="onSwiper" @slideChange="onSlideChange" @reachEnd="onReachEnd"
        class="custom-swiper vertical-swiper">
        <swiper-slide v-for="(word, index) in words" :key="word.id || index">
          <div class="word-card" :class="{ 'active': currentIndex === index, 'inactive': currentIndex !== index }">
            <div class="word-text">{{ word.word }}</div>
            <div v-for="meaning in word.meaning" class="word-meaning">
              <span class="word-type">{{ meaning.type }}</span>
              : {{ meaning.content }}
            </div>
          </div>
        </swiper-slide>
        <!-- 加载更多指示器 -->
        <swiper-slide v-if="hasMore && isLoading">
          <div class="load-more-indicator">
            <div class="loading-spinner"></div>
            <p>加载更多单词中...</p>
          </div>
        </swiper-slide>
      </swiper>
    </div>

    <!-- 分页信息显示 -->
    <div class="pagination-info">
      <span>第 {{ currentPage }} 页</span>
      <span>已加载 {{ words.length }} 个单词</span>
      <span v-if="!hasMore">已加载全部数据</span>
    </div>
  </div>
</template>

<script setup>
import axios from 'axios'
import { ref, computed, onMounted } from 'vue'
import { Swiper, SwiperSlide } from 'swiper/vue'
import { Autoplay } from 'swiper/modules'
import 'swiper/css'
import 'swiper/css/pagination'

const words = ref([])
const swiperInstance = ref(null)
const currentIndex = ref(0)
const isAutoPlay = ref(true)
const isHovering = ref(false)
const currentPage = ref(0)
const hasMore = ref(true)
const isLoading = ref(false)
const isReachEndTriggered = ref(false)

const modules = [Autoplay]

const autoplayConfig = computed(() => {
  return isAutoPlay.value && !isHovering.value ? {
    delay: 5000,
    disableOnInteraction: false,
    pauseOnMouseEnter: true
  } : false
})

const getList = async (page) => {
  if (isLoading.value || !hasMore.value) return

  isLoading.value = true
  try {
    const response = await axios.get('/api/words/list', {
      params: {
        page,
        page_size: 10  // 每页加载10个单词
      }
    })

    if (response.data.data && response.data.data.length > 0) {
      if (page === 1) {
        words.value = response.data.data
      } else {
        words.value = [...words.value, ...response.data.data]
      }

      // 检查是否还有更多数据
      hasMore.value = response.data.data.length >= 10

    } else {
      hasMore.value = false
    }
    currentPage.value = page

  } catch (error) {
    console.error('获取单词失败:', error)
    hasMore.value = false
  } finally {
    isLoading.value = false
    isReachEndTriggered.value = false
  }
}

const loadMore = () => {
  // 防止重复触发
  if (isReachEndTriggered.value || isLoading.value || !hasMore.value) return

  isReachEndTriggered.value = true
  getList(currentPage.value + 1)
}

const onSwiper = (swiper) => {
  swiperInstance.value = swiper
}

const onSlideChange = (swiper) => {
  currentIndex.value = swiper.activeIndex

  // 只有当滑动到最后一个slide时才触发加载更多
  if (currentIndex.value >= words.value.length - 1 && hasMore.value) {
    loadMore()
  }
}

const onReachEnd = () => {
  // 只有当还有更多数据且没有正在加载时才触发
  if (hasMore.value) {
    loadMore()
  }
}

const pauseAutoplay = () => {
  isHovering.value = true
  if (swiperInstance.value && swiperInstance.value.autoplay) {
    swiperInstance.value.autoplay.stop()
  }
}

const resumeAutoplay = () => {
  isHovering.value = false
  if (swiperInstance.value && swiperInstance.value.autoplay) {
    swiperInstance.value.autoplay.start()
  }
}

onMounted(() => {
  getList(1)
})
</script>

<style scoped>
.app {
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.swiper-container {
  width: 100%;
  max-width: 500px;
  height: 100vh;
  margin: 0 auto;
  cursor: pointer;
}

.custom-swiper {
  overflow: visible;
  height: 100%;
}

.vertical-swiper {
  height: 100vh;
}

.word-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 0 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  color: #fff;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  min-height: 180px;
  transform: scale(0.8);
  opacity: 0.6;
}

.word-card.active {
  transform: scale(1);
  opacity: 1;
  min-height: 220px;
  background: rgba(255, 255, 255, 0.2);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
}

.word-card.inactive {
  transform: scale(0.8);
  opacity: 0.6;
}

.word-content {
  text-align: center;
}

.word-text {
  margin-top: -20px;
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 15px;
  color: #fff;
  transition: all 0.3s ease;
  text-align: left;
}

.word-card.active .word-text {
  font-size: 42px;
}

.word-card.inactive .word-text {
  font-size: 28px;
}

.word-meaning {
  text-align: left;
  font-size: 14px;
  transition: all 0.3s ease;
}

.word-card.active .word-meaning {
  font-size: 16px;
}

.word-card.inactive .word-meaning {
  font-size: 12px;
  opacity: 0.8;
}

.word-type {
  font-weight: 600;
}

.load-more-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 180px;
  color: rgba(255, 255, 255, 0.7);
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.pagination-info {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 20px;
  font-size: 14px;
  opacity: 0.8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .word-text {
    font-size: 28px;
  }

  .word-card.active .word-text {
    font-size: 32px;
  }

  .word-card.inactive .word-text {
    font-size: 22px;
  }

  .swiper-container {
    max-width: 90%;
  }

  .word-card {
    height: 150px;
  }

  .word-card.active {
    height: 180px;
  }

  .swiper-container:active {
    cursor: grabbing;
  }

  .pagination-info {
    flex-direction: column;
    gap: 5px;
    text-align: center;
  }
}
</style>
