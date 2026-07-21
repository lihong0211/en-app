module.exports = {
    root: true,
    env: {
        node: true
    },
    extends: [
        'plugin:vue/vue3-recommended',
        'eslint:recommended'
    ],
    rules: {
      'no-debugger': 'off' // 关闭 debugger 检查
    }
  }