<template>
  <Login v-if="view === 'login'" />
  <Desk v-else-if="view === 'bar'" />
  <Main v-else />
</template>

<script setup>
import Desk from './components/Desk.vue'
import Login from './components/Login.vue'
import Main from './components/Main.vue'

// login=登录窗口 / bar=悬浮词幕条 / 默认=酷狗式主界面
const view = new URLSearchParams(window.location.search).get('view') || 'main'
</script>

<style>
html,
body,
#app {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  background: transparent;
}

body {
  background: transparent !important;
  margin: 0 !important;
  padding: 0 !important;
}
</style>
