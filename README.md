# wechat-to-md

微信公众号文章**抓取 + AI 智能重组**工具。

- 把任意公众号文章保存为本地 **Markdown + Word** 双格式（含图片）
- 把多篇文章喂给 AI，一键重组成一篇新的公众号文章
- 支持模仿量子位、极客公园、机器之心等 8 种自媒体大 V 风格，内置去 AI 味写作规范
- 输出兼容 [wewrite](https://github.com/oaker-io/wewrite) 字节跳动排版主题

---

## 功能一览

### 1. 抓取文章 → Markdown + Word

- 提取标题、公众号名、发布时间、正文
- 自动下载所有图片到本地 `images/` 目录（支持微信懒加载 `data-src`）
- 同时生成 `article.md` 和 `article.docx`，图片全部嵌入 Word
- 支持一次输入多个链接，批量保存
- 按主题名称统一归档到指定文件夹
- 失败链接自动汇总提示

### 2. AI 智能重组（`--merge`）

- 读取目录下所有已抓取的 Markdown 文章
- 调用豆包大模型（`doubao-seed-2.0-pro`）将多篇文章重新整合
- 支持多模态图片理解：AI 分析每张图片内容，智能决定插入位置
- 去除冗余，重构逻辑，生成 1800–2200 字的新文章

### 3. 自媒体风格库（8 种）

基于真实写作风格调研，每种风格包含句式特征、开头方式、专属禁止清单。

| 编号 | 风格 | 核心特点 |
|------|------|---------|
| 0 | 默认人味风格 | 口语化、有个人立场，不像 AI |
| 1 | 量子位 | 直接高潮开头，短平快，动态动词驱动 |
| 2 | 极客公园 | 人物场景式开头，非虚构叙事，杂志深度感 |
| 3 | 机器之心 | 摘要式开头，学术严谨，保留英文术语 |
| 4 | 李继刚 | 极致压缩，字少意深，古典汉语感，禅意犀利 |
| 5 | 秋芝 2046 | 痛点开头，手把手陪伴感，跨界视角 |
| 6 | 数字生命卡兹克 | 真实聊天感，具体场景切入，完整禁止清单 |
| 7 | 赛文乔伊 | 用户行为→产品逻辑→规律，平实有温度 |

**所有风格共用「去 AI 味」铁律：**
- 禁止结构词：`首先 / 其次 / 最后 / 综上所述 / 总而言之`
- 禁止套话：`赋能 / 抓手 / 闭环 / 落地 / 深度 / 维度`
- 禁止万能开头：`在当今……的时代` / `随着……的发展`
- 禁止强行结尾：`未来可期` / `让我们一起……` / 正能量升华

### 4. 字节跳动风格排版

- 中英文混排自动加空格
- 引用块 → `:::quote` 容器
- 自动识别对话 → `:::dialogue` 容器
- 自动识别时间线 → `:::timeline` 容器
- 自动识别提示/警告 → `:::callout` 容器
- 生成 wewrite YAML 头部（`theme: bytedance`）

---

## 安装依赖

```bash
pip install requests beautifulsoup4 openai python-dotenv
```

Word 导出依赖系统安装的 [pandoc](https://pandoc.org/installing.html)：

```bash
# macOS
brew install pandoc

# Ubuntu / Debian
sudo apt install pandoc
```

如需使用 AI 重组功能，在项目根目录创建 `.env` 文件：

```env
DOUBAN_API_KEY=你的豆包 API 密钥
DOUBAN_API_BASE=https://ark.cn-beijing.volces.com/api/coding/v1
```

---

## 使用方法

### 抓取文章（交互式）

直接运行，按提示输入主题名和文章链接：

```bash
python wechat_to_md.py
```

```
请输入主题名称（直接回车则不创建主题文件夹）: 大卫芬奇
请逐行输入文章链接，输入空行结束：
  链接: https://mp.weixin.qq.com/s/xxxxx
  链接: https://mp.weixin.qq.com/s/yyyyy
  链接:        ← 空行回车开始下载
```

### 抓取文章（命令行参数）

```bash
# 单篇
python wechat_to_md.py https://mp.weixin.qq.com/s/xxxxx

# 多篇 + 主题文件夹
python wechat_to_md.py -t "大卫芬奇" https://mp.weixin.qq.com/s/aaa https://mp.weixin.qq.com/s/bbb

# 指定保存目录
python wechat_to_md.py -o ~/Desktop/公众号文章 https://mp.weixin.qq.com/s/xxxxx

# 不下载图片（保留原始 URL）
python wechat_to_md.py --no-images https://mp.weixin.qq.com/s/xxxxx
```

### AI 重组已抓取的文章

```bash
# 重组指定目录下的所有文章
python wechat_to_md.py --merge ./大卫芬奇

# 重组 + 指定输出文件
python wechat_to_md.py --merge ./大卫芬奇 -o 新文章.md

# 重组 + 直接指定主题
python wechat_to_md.py --merge ./大卫芬奇 --topic "芬奇的视觉语言"
```

重组过程中会交互式询问：
- 新文章主题
- 是否复用原文配图（AI 会分析图片内容并自动插入合适位置）
- 是否使用字节跳动风格排版
- 选择写作风格（0–7）

### 抓取后直接重组（一站式）

批量抓取完成后，脚本会自动询问是否立即对刚抓取的文章进行 AI 重组，无需再次手动运行。

---

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | 文章链接，可传多个 | 交互输入 |
| `-o / --output` | 输出目录或文件路径 | 当前目录 |
| `-t / --topic` | 主题文件夹名 / 新文章主题 | 交互输入 |
| `--no-images` | 不下载图片，保留原始 URL | 否 |
| `--merge <目录>` | 合并指定目录下的多篇文章 | — |

---

## 输出结构

```
输出目录/
└── 主题名称/
    ├── 文章标题一/
    │   ├── article.md       ← Markdown 格式
    │   ├── article.docx     ← Word 格式（图片嵌入）
    │   └── images/
    ├── 文章标题二/
    │   ├── article.md
    │   ├── article.docx
    │   └── images/
    └── 新合并的文章.md      ← AI 重组输出（含 wewrite 头部）
```

---

## 注意事项

- 微信文章链接有时效性，建议尽快保存
- 需要登录才能访问的文章无法抓取
- AI 重组功能需要豆包 API，图片分析会消耗额外 token
- 生成的 wewrite 格式文章可直接粘贴到 [wewrite](https://github.com/oaker-io/wewrite) 使用

---

## License

MIT
