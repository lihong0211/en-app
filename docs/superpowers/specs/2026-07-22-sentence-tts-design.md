# 例句朗读(TTS)设计

## 背景 & 目标

`word_sentences` 表(service-ali)已经存在,每个词性(`word_meanings` 一行)对应一条例句(`en_text`/`zh_text`),`audio_url` 字段当时就是为了"TTS 方案确定后回填"预留的,一直是 `NULL`。现在例句数据已经积累了不少,需要把 `audio_url` 填上,并在客户端把例句展示+播放出来。

TTS 方案:有道智云语音合成(`openapi.youdao.com/ttsapi`),复用 `.env` 里已有的 `YOUDAO_APP_KEY`/`YOUDAO_APP_SECRET`(目前这对密钥用于 `service/en_desktop/youdao.py` 的文本翻译接口,需要确认有道智云后台已开通"语音合成"产品)。

## 涉及仓库

功能跨两个仓库,和拼读拆分功能(见 `2026-07-19-phonics-breakdown-design.md`)是同一套模式——后端离线批量生成 + 前端只读播放,不做前端/客户端实时调用云端 TTS:

- **service-ali**(后端):调有道 TTS 批量生成例句音频文件,写回 `audio_url`;API 序列化里把例句挂到对应 meaning 上
- **en-elctron**(本仓库,Electron 客户端):展示例句文本,播放 `audio_url` 指向的静态音频

**为什么是离线批量生成,不是实时调用**:例句文本基本不变,没必要每次播放都现算一遍——多一次网络延迟、多一次调用量,密钥还必须经某个后端中转才安全(不能塞进客户端)。批量生成一次、存成静态文件、写回 URL,以后播放就是纯静态资源,零延迟零重复成本。

**实施顺序**:先在 service-ali 把 TTS 调用和生成脚本跑通、小样本验证音频质量和 `audio_url` 可访问,再做 API 序列化扩展和 en-elctron 前端部分。

## 一、TTS 调用封装(service-ali)

在 `service/en_desktop/youdao.py` 新增:

```python
def synthesize_speech(text: str) -> bytes | None:
    """
    调有道智云语音合成 API,返回 mp3 二进制;请求失败/接口报错返回 None。
    """
```

- 端点 `https://openapi.youdao.com/ttsapi`,复用文件里已有的 `_sign`/`_truncate` 签名逻辑(同一套 v3 签名规则)
- 有道 TTS 接口失败时返回的是 JSON 错误体而不是音频二进制,需要按 `Content-Type` 或响应头判断,报错/未开通产品/超时都归一为返回 `None`,不抛异常(参照 `fetch_phonetic` 的降级风格)

## 二、生成脚本(service-ali)

`scripts/generate_sentence_audio.py`,比照 `scripts/generate_phonics.py` 的 `--limit`/`--apply`/dry-run 惯例:

1. 查询 `word_sentences` 里 `audio_url IS NULL` 的行(按 `id` 增量,支持后续新例句跑增量批处理),`--limit` 支持先跑小样本
2. 对每一行,把 `en_text` 传给 `synthesize_speech`
3. 调用失败(返回 `None`)的行跳过、打日志(例句原文、失败原因),不写脏数据、不重试
4. 成功的,把 mp3 写到服务器本地 `/lihong/static/word_sentences/<sentence_id>.mp3`(复用 nginx 已有的 `location ^~ /static/` alias,该 alias 挂在 `doctor-dog.com` 这个 server block 下,不需要改 nginx 配置),写回 `audio_url = f"https://doctor-dog.com/static/word_sentences/{id}.mp3"`(域名直接写死,和项目里其它地方一样没有走 BASE_URL 环境变量的惯例)
5. `--dry-run`(默认)只打印统计(成功/跳过数量);`--apply` 才真正生成文件+写库
6. 先跑几十条小样本,人工听一遍音频质量、确认 `audio_url` 能正常访问,再考虑全量跑

**运行位置**:这个脚本要直接在服务器上跑(SSH 上去,和现有 `deploy.sh` 走的服务器一致)。数据库是远程直连没问题,但静态文件要落在服务器本地磁盘的 `/lihong/static/`,本地生成再传反而要多写一道 rsync/scp 逻辑,没必要。

失败/跳过的例句,`audio_url` 保持 `NULL`,前端表现为该例句没有播放按钮(见下文"降级")。

## 三、API 序列化扩展(service-ali)

不新开端点,在现有组装 meaning 的地方(`service/en_desktop/words.py::_meanings_of`、`service/en_desktop/libraries.py::_meanings_grouped`)顺带按 `word_meaning_id` 查一下 `word_sentences`,给每条 meaning 加一个 `sentence` 字段:

- 有对应例句:`sentence: {"en_text": "...", "zh_text": "...", "audio_url": "..." | null}`
- 没有例句:`sentence: null`

`/words/list`、`/words/{id}`、`/libraries/{id}/words` 这几个已有接口自然带上这个字段,前端按需读取。`audio_url` 为 `null` 是正常状态(例句还没跑批量生成,或者生成失败),不是错误。

## 四、前端交互(en-elctron)

- **词表(`Main.vue`)**:每条 meaning 下面展示例句原文+中文翻译,`sentence.audio_url` 不为 `null` 时在旁边加一个播放按钮;为 `null` 时不显示按钮(不显示比置灰更干净,跟 phonics 的降级方式一致)
- **桌面悬浮轮播(`Desk.vue`)**:单词发音(`playWordAudio`)播完后,间隔一小段时间接着播一条例句(取当前词第一条有 `audio_url` 的 meaning),受现有 `pb.audioEnabled` 开关统一控制;没有可播的例句就跳过,不报错、不特殊提示
- **播放实现**:复用现有 `new Audio(url).play()` 模式,失败静默处理(参照 `utils/audio.js::playWordAudio` 的 try/catch + `onerror` 风格),不用新写封装

## 不做的事(明确排除)

- 不做前端/客户端直接调云端 TTS(避免密钥暴露和重复调用成本)
- 不做多音色/多语速选择
- 不重新生成已有 `audio_url` 的例句(除非手动把该字段清空)
- 不做例句跟读打分
