# wechat-to-md

将微信公众号文章保存为本地 Markdown 文件，图片一并下载到本地。

支持**单篇**抓取、**批量**抓取，并可按主题统一归档到指定文件夹。

---

## 功能

- 提取标题、公众号名、发布时间、正文
- 递归解析图片（支持微信懒加载 `data-src`），下载到 `images/` 子目录
- 支持一次输入多个链接，批量保存
- 自定义主题文件夹名称，统一归档
- 失败链接汇总提示

---

## 安装依赖

```bash
pip install requests beautifulsoup4
```

---

## 使用方法

### 直接运行（交互式）

```bash
python wechat_to_md.py
```

运行后会依次提示：

```
请输入主题名称（将作为文件夹名，直接回车则不创建主题文件夹）: 大卫芬奇
请逐行输入文章链接，输入空行结束：
  链接: https://mp.weixin.qq.com/s/xxxxx
  链接: https://mp.weixin.qq.com/s/yyyyy
  链接:        ← 空行回车，开始下载
```

### 命令行参数

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

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | 文章链接，可传多个（留空则交互输入） | — |
| `-o / --output` | 根输出目录 | 当前目录 |
| `-t / --topic` | 主题文件夹名 | — |
| `--no-images` | 不下载图片 | 否 |

---

## 输出结构

```
输出目录/
└── 主题名称/               ← 你输入的主题（可选）
    ├── 文章标题一/
    │   ├── article.md
    │   └── images/
    │       ├── abc123.jpg
    │       └── def456.png
    └── 文章标题二/
        ├── article.md
        └── images/
```

---

## 注意事项

- 微信文章链接有时效性，建议尽快保存
- 部分需要登录才能查看的文章无法抓取
- 图片链接由微信 CDN 签名，下载后才能长期访问

---

## License

MIT
