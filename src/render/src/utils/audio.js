// 单词发音：有道词典发音接口（type=2 美音），源自 en-mini 的 playAudio。
// 约定：音频失败绝不影响轮播——加载失败/被拒/超时全部静默跳过，只留 console 痕迹。
const YOUDAO_VOICE_URL = 'https://dict.youdao.com/dictvoice?type=2&audio='

let current = null

export function playWordAudio(word) {
  if (!word) return
  try {
    // 快速切词时先停掉上一个，不叠音
    if (current) {
      current.pause()
      current.src = ''
    }
    current = new Audio(YOUDAO_VOICE_URL + encodeURIComponent(word))
    current.onerror = () => console.warn('发音加载失败:', word)
    current.play().catch((e) => console.warn('发音播放失败:', word, e && e.message))
  } catch (e) {
    console.warn('发音异常:', word, e.message)
  }
}
