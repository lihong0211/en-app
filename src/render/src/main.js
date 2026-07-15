import { createApp } from 'vue'
import App from './App.vue'
import { Swiper, SwiperSlide } from 'swiper/vue'

// 导入样式
import 'swiper/css'
import 'swiper/css/navigation'
import 'swiper/css/pagination'

const app = createApp(App)

// 全局注册组件
app.component('Swiper', Swiper)
app.component('SwiperSlide', SwiperSlide)

app.mount('#app')
