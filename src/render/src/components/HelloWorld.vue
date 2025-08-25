<template>
  <div class="app">
    <h1>Electron + Vue 3 + Python</h1>
    <button @click="callPythonAPI">调用 Python 接口</button>
    <p>{{ message }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const message = ref('')

const callPythonAPI = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/hello')
    debugger
  } catch (error) {
    console.error('Error calling Python API:', error)
  }
}
</script>