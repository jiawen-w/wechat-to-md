# wechat-to-md

微信公众号文章**抓取 + AI 智能重组**工具。

- 把任意公众号文章保存为本地 Markdown（含图片）
- 把多篇文章喂给 AI，一键重组成一篇新的公众号文章（会读取原来的图片信息，新的文章也会包含图片）
- 支持模仿量子位、极客公园、机器之心等 8 种自媒体大 V 风格
- 输出兼容 [wewrite](https://wewrite.app) 字节跳动排版主题

---

## 功能一览

### 1. 抓取文章 → Markdown

- 提取标题、公众号名、发布时间、正文
- 自动下载所有图片到本地 `images/` 目录（支持微信懒加载 `data-src`）
- 支持一次输入多个链接，批量保存
- 按主题名称统一归档到指定文件夹
- 失败链接自动汇总提示

### 2. AI 智能重组（`--merge`）

- 读取目录下所有已抓取的 Markdown 文章
- 调用豆包大模型（`doubao-seed-2.0-pro`）将多篇文章重新整合
- 支持多模态图片理解：AI 分析每张图片内容，智能决定插入位置
- 去除冗余，重构逻辑，生成 1800–2200 字的新文章

### 3. 自媒体风格库（8 种）

| 编号 | 风格 | 特点 |
|------|------|------|
| 0 | 默认 | 通用公众号风格 |
| 1 | 量子位 | 科技感，专业严谨 |
| 2 | 极客公园 | 用 Why 追问，有非共识判断 |
| 3 | 机器之心 | 论文级深度，技术→商业→生态推演 |
| 4 | 李继刚 | Lisp 哲学风，语言极致凝练 |
| 5 | 求志 2046 | 创业投资视角，关注商业本质 |
| 6 | 数字生命卡兹克 | 硬核技术解读，深入浅出 |
| 7 | 赛文乔伊 | 产品思维，用户体验视角 |

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
pip install requests beautifulsoup4
```

如需使用 AI 重组功能，还需：

```bash
pip install openai python-dotenv
```

并在项目根目录创建 `.env` 文件：

```env
DOUBAN_API_KEY=你的豆包API密钥
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
    │   ├── article.md
    │   └── images/
    ├── 文章标题二/
    │   ├── article.md
    │   └── images/
    └── 新合并的文章.md       ← AI 重组输出（含 wewrite 头部）
```

---

## 注意事项

- 微信文章链接有时效性，建议尽快保存
- 需要登录才能访问的文章无法抓取
- AI 重组功能需要豆包 API，图片分析会消耗额外 token
- 生成的 wewrite 格式文章可直接粘贴到 [wewrite.app](https://wewrite.app) 使用

---

## License

MIT
