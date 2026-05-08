#!/usr/bin/env python3
"""
微信公众号文章工具：抓取 + 智能重组

用法：
    # 抓取文章
    python wechat_to_md.py <文章链接>
    python wechat_to_md.py <文章链接> -o ./输出目录
    python wechat_to_md.py <文章链接> --no-images   # 不下载图片

    # 重组多篇文章为新公众号文章
    python wechat_to_md.py --merge ./文章目录
    python wechat_to_md.py --merge ./文章目录 -o 新文章.md
    python wechat_to_md.py --merge ./文章目录 --topic "新文章主题"
"""

import requests
from bs4 import BeautifulSoup
import os
import re
import sys
import hashlib
import argparse
import shutil
import base64
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件中的环境变量

# ---------- 网络请求 ----------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://mp.weixin.qq.com/",
}


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text


# ---------- 解析文章元数据 ----------

def parse_article(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # 标题
    title = ""
    for sel in ["h1#activity-name", "h1.rich_media_title", "h1"]:
        tag = soup.select_one(sel)
        if tag:
            title = tag.get_text(strip=True)
            break

    # 公众号名
    author = ""
    for sel in ["#js_name", ".account_nickname_inner", "#profileBt strong"]:
        tag = soup.select_one(sel)
        if tag:
            author = tag.get_text(strip=True)
            break

    # 发布时间
    pub_time = ""
    for sel in ["#publish_time", ".publish_time", "em#publish_time"]:
        tag = soup.select_one(sel)
        if tag:
            pub_time = tag.get_text(strip=True)
            break

    # 正文
    content = soup.select_one("#js_content") or soup.select_one(".rich_media_content")

    return title or "untitled", author, pub_time, content


# ---------- 图片下载 ----------

def download_image(img_url: str, img_dir: Path) -> str | None:
    try:
        resp = requests.get(img_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
        ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif", "image/webp": "webp"}
        ext = ext_map.get(content_type, "jpg")
        fname = hashlib.md5(img_url.encode()).hexdigest()[:12] + f".{ext}"
        fpath = img_dir / fname
        if not fpath.exists():
            fpath.write_bytes(resp.content)
        return fname
    except Exception as e:
        print(f"  [警告] 图片下载失败: {img_url[:60]}... — {e}", file=sys.stderr)
        return None


# ---------- HTML → Markdown ----------

def node_to_md(el, img_dir: Path | None) -> str:
    """递归将 BeautifulSoup 节点转为 Markdown 文本。"""
    from bs4 import NavigableString, Tag

    if isinstance(el, NavigableString):
        return str(el)

    tag = el.name
    if tag is None:
        return ""

    # 跳过脚本/样式/广告占位
    if tag in {"script", "style", "noscript"}:
        return ""

    inner = "".join(node_to_md(c, img_dir) for c in el.children)

    if tag in {"p", "div", "section"}:
        stripped = inner.strip()
        return f"\n\n{stripped}\n\n" if stripped else ""

    if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(tag[1])
        return f"\n\n{'#' * level} {inner.strip()}\n\n"

    if tag == "br":
        return "\n"

    if tag == "strong" or tag == "b":
        t = inner.strip()
        return f"**{t}**" if t else ""

    if tag in {"em", "i"}:
        t = inner.strip()
        return f"*{t}*" if t else ""

    if tag == "a":
        href = el.get("href", "")
        t = inner.strip()
        if href and not href.startswith("javascript"):
            return f"[{t}]({href})" if t else href
        return t

    if tag == "img":
        # 优先取 data-src（微信懒加载）
        src = el.get("data-src") or el.get("src", "")
        if not src:
            return ""
        alt = el.get("alt") or el.get("data-copyright", "图片")
        if img_dir and src.startswith("http"):
            fname = download_image(src, img_dir)
            if fname:
                print(f"  [图片] {fname}")
                return f"\n\n![{alt}](images/{fname})\n\n"
        return f"\n\n![{alt}]({src})\n\n"

    if tag in {"ul", "ol"}:
        items = []
        for i, li in enumerate(el.find_all("li", recursive=False), 1):
            li_text = "".join(node_to_md(c, img_dir) for c in li.children).strip()
            prefix = f"{i}." if tag == "ol" else "-"
            items.append(f"{prefix} {li_text}")
        return "\n\n" + "\n".join(items) + "\n\n"

    if tag == "li":
        return inner

    if tag == "blockquote":
        lines = inner.strip().splitlines()
        return "\n\n" + "\n".join(f"> {l}" for l in lines) + "\n\n"

    if tag == "code":
        return f"`{inner}`"

    if tag == "pre":
        return f"\n\n```\n{inner.strip()}\n```\n\n"

    if tag == "hr":
        return "\n\n---\n\n"

    if tag == "table":
        return _table_to_md(el, img_dir)

    return inner


def _table_to_md(table, img_dir) -> str:
    rows = table.find_all("tr")
    if not rows:
        return ""
    lines = []
    for i, row in enumerate(rows):
        cells = row.find_all(["th", "td"])
        line = "| " + " | ".join(
            "".join(node_to_md(c, img_dir) for c in cell.children).strip()
            for cell in cells
        ) + " |"
        lines.append(line)
        if i == 0:
            lines.append("| " + " | ".join("---" for _ in cells) + " |")
    return "\n\n" + "\n".join(lines) + "\n\n"


def clean_md(text: str) -> str:
    # 合并超过两个连续空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------- 文章智能重组 ----------

def load_articles_from_dir(dir_path: str) -> list[tuple[str, str, Path]]:
    """从目录加载所有Markdown文章，返回(标题, 内容, 文章目录路径)"""
    articles = []
    dir_path = Path(dir_path)

    if not dir_path.exists():
        raise ValueError(f"目录不存在: {dir_path}")

    # 查找所有article.md文件（本工具抓取的格式）
    for md_file in dir_path.rglob("article.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            article_dir = md_file.parent
            articles.append((str(article_dir.name), content, article_dir))
            print(f"已加载: {article_dir.name}")
        except Exception as e:
            print(f"  [警告] 读取失败 {md_file}: {e}", file=sys.stderr)

    # 如果没有找到article.md，尝试直接加载目录下的md文件
    if not articles:
        for md_file in dir_path.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                article_dir = md_file.parent
                articles.append((md_file.stem, content, article_dir))
                print(f"已加载: {md_file.name}")
            except Exception as e:
                print(f"  [警告] 读取失败 {md_file}: {e}", file=sys.stderr)

    return articles


def encode_image_to_base64(image_path: str) -> str:
    """将图片编码为base64格式"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def analyze_image_content(image_path: str, client: OpenAI) -> str:
    """使用多模态模型分析图片内容"""
    try:
        base64_image = encode_image_to_base64(image_path)
        response = client.chat.completions.create(
            model="doubao-seed-2.0-pro",  # 支持多模态
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请详细描述这张图片的内容，包括主题、文字信息、图表数据、场景等，越详细越好。"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [警告] 图片分析失败: {e}", file=sys.stderr)
        return ""


def extract_images_from_article(article_dir: Path, content: str) -> list[dict]:
    """从文章内容和目录中提取所有图片信息"""
    images = []
    img_dir = article_dir / "images"

    if not img_dir.exists():
        return images

    # 匹配Markdown图片语法
    img_pattern = r'!\[(.*?)\]\((images/.*?)\)'
    matches = re.findall(img_pattern, content)

    for alt, img_rel_path in matches:
        img_path = article_dir / img_rel_path
        if img_path.exists():
            images.append({
                "path": str(img_path),
                "filename": img_path.name,
                "alt": alt,
                "source_article": article_dir.name
            })

    return images


def merge_articles_with_ai(articles: list[tuple[str, str, Path]], topic: str = "", include_images: bool = True, style_key: str = "default") -> tuple[str, list[dict]]:
    """使用豆包API将多篇文章重组为一篇新的公众号文章，支持图片智能插入和风格模仿"""
    if not articles:
        raise ValueError("没有可合并的文章")

    # 获取风格配置
    style = ZIMEITI_STYLES.get(style_key, ZIMEITI_STYLES["default"])
    print(f"\n共加载 {len(articles)} 篇文章，使用【{style['name']}】风格重组...")

    # 初始化豆包客户端
    client = OpenAI(
        base_url=os.getenv("DOUBAN_API_BASE", "https://ark.cn-beijing.volces.com/api/coding/v1"),
        api_key=os.getenv("DOUBAN_API_KEY", "your-api-key-here")
    )

    # 提取所有图片
    all_images = []
    if include_images:
        print("正在收集并分析所有图片...")
        for title, content, article_dir in articles:
            images = extract_images_from_article(article_dir, content)
            for img in images:
                # 分析图片内容
                img["content"] = analyze_image_content(img["path"], client)
                all_images.append(img)
                print(f"  已分析: {img['filename']} - {img['content'][:50]}...")

    # 构建提示词
    articles_text = "\n\n".join([
        f"=== 文章《{title}》 ===\n{content}"
        for title, content, _ in articles
    ])

    topic_prompt = f"，主题是：{topic}" if topic else ""

    # 图片信息部分
    images_prompt = ""
    if include_images and all_images:
        images_desc = "\n".join([
            f"图片ID: {i}\n文件名: {img['filename']}\n图片内容: {img['content']}\n原ALT: {img['alt']}\n"
            for i, img in enumerate(all_images)
        ])
        images_prompt = f"""
可用图片列表（共{len(all_images)}张）：
{images_desc}

请在文章合适的位置插入相关图片，插入格式为：[IMAGE:图片ID]
例如：
这部分内容讲解了AI技术的发展，[IMAGE:0]展示了相关数据。

图片要插入到与其内容最相关的段落旁边，每个图片只使用一次，不要重复。
"""

    system_prompt = f"""你是专业的公众号内容编辑，擅长将多篇相关文章重新整合、润色，生成一篇结构清晰、内容流畅、观点明确的高质量公众号文章。

要求：
1. 保留所有原文章的核心观点、重要信息和有价值的案例，去掉冗余信息
2. 重新组织内容结构，逻辑连贯，层次分明
3. {style['prompt']}
4. 开头要有吸引人的导语，结尾要有总结和引导，简洁有力
5. 合理使用小标题分割内容，提升可读性
6. 不要出现原文的引用标识，要自然融合所有内容
7. 字数严格控制在1800-2200字左右，不要太长
8. 段落要短小精悍，每段控制在2-3句话，不要有大段长文本
9. 语言要自然口语化，避免生硬的AI式表达，像真实的人写的一样
10. 避免使用太书面化、太正式的词汇，保持接地气的表达
11. 不要使用综上所述、总而言之、总的来说这种典型的AI写作套话
12. 绝对不要使用任何双引号，所有需要引用的内容直接转述即可
13. 输出格式为纯Markdown，不要包含任何AI相关的说明文字
{images_prompt if include_images else ''}

现在需要将以下多篇文章重新组合成一篇新的公众号文章{topic_prompt}：
"""

    try:
        response = client.chat.completions.create(
            model="doubao-seed-2.0-pro",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": articles_text}
            ],
            temperature=0.7,
            max_tokens=12000
        )

        result = response.choices[0].message.content.strip()
        print("AI重组完成！")
        return result, all_images

    except Exception as e:
        raise RuntimeError(f"AI调用失败: {str(e)}")


def replace_image_placeholders(content: str, images: list[dict], output_img_dir: Path) -> str:
    """将内容中的[IMAGE:ID]占位符替换为实际的Markdown图片标签，并复制图片到输出目录"""
    output_img_dir.mkdir(parents=True, exist_ok=True)

    # 复制所有图片到输出目录
    for img in images:
        src_path = Path(img["path"])
        dest_path = output_img_dir / img["filename"]
        if not dest_path.exists():
            shutil.copy2(src_path, dest_path)

    # 替换占位符
    for i, img in enumerate(images):
        placeholder = f"[IMAGE:{i}]"
        img_tag = f"\n\n![{img['alt'] or img['content'][:30]}](images/{img['filename']})\n\n"
        content = content.replace(placeholder, img_tag)

    # 清理可能残留的占位符
    content = re.sub(r'\[IMAGE:\d+\]', '', content)
    return content


# ---------- 自媒体大V风格库 ----------

ZIMEITI_STYLES = {
    "default": {
        "name": "默认风格",
        "description": "通用公众号写作风格，逻辑清晰，通俗易懂",
        "prompt": "语言风格符合公众号阅读习惯：生动、易懂、有吸引力"
    },
    "liangziwei": {
        "name": "量子位",
        "description": "科技媒体风格，前沿、专业、有深度",
        "prompt": "模仿量子位的写作风格：科技感十足，内容专业严谨，关注前沿技术进展，用词准确，结构清晰，适合科技类内容传播。"
    },
    "jikegongyuan": {
        "name": "极客公园",
        "description": "产品分析风格，有观点、有深度、追问本质",
        "prompt": "模仿极客公园的写作风格：善于用Why追问叙事，有独立的非共识判断，喜欢从创始人和产品视角分析问题，语言犀利有观点。"
    },
    "jiqizhixin": {
        "name": "机器之心",
        "description": "产业深度分析风格，论文级深度，数据详实",
        "prompt": "模仿机器之心的写作风格：内容有论文级深度，善于从技术→商业→生态三层推演分析，有详实的数据支撑，专业严谨，适合产业分析类内容。"
    },
    "lijigang": {
        "name": "李继刚",
        "description": "Lisp哲学风格，充满哲思，语言极致凝练",
        "prompt": "模仿李继刚的写作风格：喜欢用Lisp伪代码风格表达，充满哲学追问，语言极致压缩有美感，观点独到有启发性，短句多，留白多，引人思考。"
    },
    "qiuzhi2046": {
        "name": "求志2046",
        "description": "创业投资视角，关注商业本质，视野宏大",
        "prompt": "模仿求志2046的写作风格：站在创业投资的视角，关注商业本质，视野宏大，善于分析行业趋势和创业机会，语言平实有深度。"
    },
    "kazike": {
        "name": "数字生命卡兹克",
        "description": "硬核技术解读风格，技术功底深厚，解读透彻",
        "prompt": "模仿数字生命卡兹克的写作风格：硬核技术解读，技术功底深厚，对技术的理解非常透彻，善于把复杂技术讲得通俗易懂，有强烈的个人观点。"
    },
    "saiwenqiaoyi": {
        "name": "赛文乔伊",
        "description": "产品思维风格，关注用户体验，逻辑清晰",
        "prompt": "模仿赛文乔伊的写作风格：产品思维视角，关注用户体验和产品逻辑，分析问题有条理，善于提炼产品方法论，内容实用有干货。"
    }
}

# ---------- 字节跳动风格排版 ----------

def optimize_typography(text: str) -> str:
    """优化排版：中英混排加空格、标点规范化"""
    # 中英之间加空格
    text = re.sub(r'([一-龥])([a-zA-Z0-9])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z0-9])([一-龥])', r'\1 \2', text)

    # 数字与单位之间加空格
    text = re.sub(r'(\d+)([个只条张篇页度秒分小时元块GBMBKB%])', r'\1 \2', text)

    # 标点后加空格（中文标点后不需要，英文标点后需要）
    text = re.sub(r'([,.!?;:])([^\s\)]]|$)', r'\1 \2', text)

    # 中文标点统一
    text = text.replace('、', '、').replace('，', '，').replace('。', '。').replace('？', '？').replace('！', '！')
    text = text.replace('：', '：').replace('；', '；').replace('“', '“').replace('”', '”').replace('‘', '‘').replace('’', '’')

    # 移除多余空格
    text = re.sub(r' +', ' ', text)

    return text


def convert_to_bytedance_style(content: str, add_containers: bool = True) -> str:
    """将内容转换为字节跳动风格的wewrite格式"""
    lines = content.split('\n')
    output = []
    in_list = False
    in_code = False

    for line in lines:
        stripped = line.strip()

        # 代码块处理
        if stripped.startswith('```'):
            in_code = not in_code
            output.append(line)
            continue
        if in_code:
            output.append(line)
            continue

        # 标题优化（字节风格：加粗，层级分明）
        if stripped.startswith('# '):
            h1_text = stripped[2:].strip()
            output.append(f"# {h1_text}")
            output.append("")
            continue
        elif stripped.startswith('## '):
            h2_text = stripped[3:].strip()
            output.append(f"## {h2_text}")
            output.append("")
            continue
        elif stripped.startswith('### '):
            h3_text = stripped[4:].strip()
            output.append(f"### {h3_text}")
            output.append("")
            continue

        # 列表处理
        if stripped.startswith(('- ', '* ', '+ ')) or re.match(r'^\d+\. ', stripped):
            in_list = True
            output.append(line)
            continue
        elif in_list and not stripped:
            in_list = False
            output.append("")
            continue

        # 引用转换为wewrite的:::quote容器
        if add_containers and stripped.startswith('> '):
            quote_text = stripped[2:].strip()
            output.append(":::quote")
            output.append(quote_text)
            output.append(":::")
            output.append("")
            continue

        # 加粗优化
        line = re.sub(r'\*\*(.*?)\*\*', r'**\1**', line)

        # 普通行处理
        if stripped:
            optimized = optimize_typography(line)
            output.append(optimized)
        else:
            output.append("")

    # 合并多余空行
    content = '\n'.join(output)
    content = re.sub(r'\n{3,}', '\n\n', content)

    if add_containers:
        # 自动识别并转换对话内容
        content = convert_dialogues(content)
        # 自动识别并转换时间线内容
        content = convert_timelines(content)
        # 自动识别并转换提示框
        content = convert_callouts(content)

    return content


def convert_dialogues(content: str) -> str:
    """自动识别对话内容并转换为:::dialogue容器"""
    # 匹配类似 "A：xxx" "B：xxx" 的对话模式
    dialogue_pattern = r'([^\n：]+)：([^\n]+)\n([^\n：]+)：([^\n]+)'

    def replace_dialogue(match):
        speaker1 = match.group(1).strip()
        text1 = match.group(2).strip()
        speaker2 = match.group(3).strip()
        text2 = match.group(4).strip()

        # 检查是否是对话模式
        if len(speaker1) < 10 and len(speaker2) < 10:
            return f":::dialogue\n{speaker1}：{text1}\n> {speaker2}：{text2}\n:::"
        return match.group(0)

    return re.sub(dialogue_pattern, replace_dialogue, content)


def convert_timelines(content: str) -> str:
    """自动识别时间线内容并转换为:::timeline容器"""
    # 匹配类似 "**2024年** 完成xxx" "Q1: xxx" 的时间线模式
    timeline_pattern = r'((?:\*\*[^\*]+\*\*|\d{4}[年/Q]|\d{1,2}月|\d{1,2}日)[^\n]+(?:\n|$)){2,}'

    def replace_timeline(match):
        items = match.group(0).strip().split('\n')
        if len(items) >= 2:
            timeline_content = '\n'.join(item.strip() for item in items if item.strip())
            return f":::timeline\n{timeline_content}\n:::"
        return match.group(0)

    return re.sub(timeline_pattern, replace_timeline, content)


def convert_callouts(content: str) -> str:
    """自动识别提示类内容并转换为:::callout容器"""
    # 匹配提示、注意、警告等内容
    callout_patterns = [
        (r'(提示：|注意：|小贴士：|温馨提示：)([^\n]+)', 'tip'),
        (r'(警告：|风险提示：|注意安全：)([^\n]+)', 'warning'),
        (r'(信息：|说明：|公告：)([^\n]+)', 'info'),
        (r'(危险：|严禁：|禁止：)([^\n]+)', 'danger'),
    ]

    for pattern, callout_type in callout_patterns:
        def replace_callout(match):
            title = match.group(1).strip()
            text = match.group(2).strip()
            return f":::callout {callout_type}\n{title} {text}\n:::"

        content = re.sub(pattern, replace_callout, content)

    return content


def generate_wewrite_header(topic: str) -> str:
    """生成wewrite格式的头部信息"""
    return f"""---
title: {topic}
theme: bytedance
---
"""


# ---------- 微信草稿箱推送 ----------

import json
import mimetypes

def wx_get_access_token() -> str:
    """获取微信 access_token"""
    appid = os.getenv("WX_APPID", "")
    secret = os.getenv("WX_APPSECRET", "")
    if not appid or not secret:
        raise ValueError("请在 .env 中配置 WX_APPID 和 WX_APPSECRET")

    url = "https://api.weixin.qq.com/cgi-bin/token"
    resp = requests.get(url, params={
        "grant_type": "client_credential",
        "appid": appid,
        "secret": secret,
    }, timeout=15)
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"获取 access_token 失败: {data}")
    print(f"  access_token 获取成功（有效期 {data.get('expires_in', 7200)} 秒）")
    return data["access_token"]


def wx_upload_image(token: str, img_path: str) -> str:
    """上传图片到微信服务器，返回可用于文章内容的 URL"""
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
    mime = mimetypes.guess_type(img_path)[0] or "image/jpeg"
    with open(img_path, "rb") as f:
        resp = requests.post(url, files={"media": (Path(img_path).name, f, mime)}, timeout=30)
    data = resp.json()
    if "url" not in data:
        raise RuntimeError(f"图片上传失败 {Path(img_path).name}: {data}")
    return data["url"]


def wx_upload_thumb(token: str, img_path: str) -> str:
    """上传封面图（永久素材），返回 media_id"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    mime = mimetypes.guess_type(img_path)[0] or "image/jpeg"
    with open(img_path, "rb") as f:
        resp = requests.post(url, files={"media": (Path(img_path).name, f, mime)}, timeout=30)
    data = resp.json()
    if "media_id" not in data:
        raise RuntimeError(f"封面上传失败: {data}")
    return data["media_id"]


def md_to_wx_html(md_text: str, article_dir: Path, token: str) -> tuple[str, str]:
    """
    将 Markdown 转为微信可用的 HTML，同时上传本地图片。
    返回 (html内容, 封面图media_id)
    """
    import markdown
    # 去掉 YAML 头部（wewrite 格式）
    md_text = re.sub(r"^---\n.*?\n---\n", "", md_text, flags=re.DOTALL).strip()

    # 先处理本地图片：上传并替换路径
    img_dir = article_dir / "images"
    thumb_media_id = ""
    first_img = True

    def replace_img(match):
        nonlocal thumb_media_id, first_img
        alt = match.group(1)
        rel_path = match.group(2)

        if rel_path.startswith("http"):
            return match.group(0)  # 远程图片保持不变

        abs_path = article_dir / rel_path
        if not abs_path.exists():
            return match.group(0)

        try:
            wx_url = wx_upload_image(token, str(abs_path))
            print(f"    已上传: {abs_path.name} → {wx_url[:50]}...")

            # 第一张图作为封面
            if first_img:
                first_img = False
                try:
                    thumb_media_id = wx_upload_thumb(token, str(abs_path))
                    print(f"    封面 media_id: {thumb_media_id[:20]}...")
                except Exception as e:
                    print(f"    [警告] 封面上传失败: {e}")

            return f"![{alt}]({wx_url})"
        except Exception as e:
            print(f"    [警告] 图片上传失败 {abs_path.name}: {e}")
            return match.group(0)

    md_text = re.sub(r"!\[(.*?)\]\((.*?)\)", replace_img, md_text)

    # Markdown → HTML
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br"]
    )

    # 微信文章样式包装
    html = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', sans-serif; font-size: 16px; line-height: 1.8; color: #333; padding: 0 4px;">
{html_body}
</div>"""

    # 修正图片标签为微信格式
    html = re.sub(
        r'<img([^>]*?)src="(https://mmbiz[^"]+)"([^>]*?)>',
        r'<img\1src="\2"\3 style="max-width:100%;display:block;margin:16px auto;">',
        html
    )

    return html, thumb_media_id


def push_to_wx_draft(md_path: str):
    """将 Markdown 文件推送到微信公众号草稿箱"""
    md_path = Path(md_path)
    article_dir = md_path.parent

    print(f"\n正在推送到微信草稿箱: {md_path.name}")
    print("获取 access_token...")
    token = wx_get_access_token()

    # 读取 Markdown
    md_text = md_path.read_text(encoding="utf-8")

    # 提取标题（第一个 # 行）
    title_match = re.search(r"^#\s+(.+)$", md_text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else md_path.stem

    # 提取摘要（正文前100字）
    body = re.sub(r"^---\n.*?\n---\n", "", md_text, flags=re.DOTALL)
    body = re.sub(r"[#\*\n`>]", "", body).strip()
    digest = body[:100]

    print(f"标题: {title}")
    print("上传图片中...")

    # 转换为微信 HTML
    html_content, thumb_media_id = md_to_wx_html(md_text, article_dir, token)

    if not thumb_media_id:
        print("  [警告] 未找到封面图，使用空封面（草稿箱中可手动设置）")

    # 创建草稿
    print("创建草稿...")
    draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    payload = {
        "articles": [{
            "title": title,
            "author": "",
            "digest": digest,
            "content": html_content,
            "content_source_url": "",
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }]
    }
    resp = requests.post(draft_url, json=payload, timeout=30)
    data = resp.json()

    if data.get("errcode", 0) == 0 and "media_id" in data:
        print(f"\n✅ 推送成功！草稿 media_id: {data['media_id']}")
        print("请登录公众号后台 → 草稿箱 查看")
    else:
        raise RuntimeError(f"草稿创建失败: {data}")


# ---------- 主流程 ----------

def save_article(url: str, output_dir: str = ".", download_images: bool = True):
    print(f"正在抓取: {url}")
    html = fetch_html(url)
    title, author, pub_time, content = parse_article(html)

    if content is None:
        sys.exit("错误：未找到正文内容，可能需要登录或文章已被删除。")

    print(f"标题: {title}")
    if author:
        print(f"公众号: {author}")
    if pub_time:
        print(f"发布: {pub_time}")

    # 构建输出目录
    safe_title = re.sub(r'[\\/*?:"<>|\n\r]', "", title)[:60].strip()
    article_dir = Path(output_dir) / safe_title
    article_dir.mkdir(parents=True, exist_ok=True)

    img_dir = None
    if download_images:
        img_dir = article_dir / "images"
        img_dir.mkdir(exist_ok=True)
        print("下载图片中...")

    # 转换正文
    body_md = clean_md(node_to_md(content, img_dir))

    # 组装完整 Markdown
    lines = [f"# {title}", ""]
    if author:
        lines += [f"**公众号**: {author}", ""]
    if pub_time:
        lines += [f"**发布时间**: {pub_time}", ""]
    lines += ["---", "", body_md]

    md_text = "\n".join(lines)

    # 写文件
    md_path = article_dir / "article.md"
    md_path.write_text(md_text, encoding="utf-8")
    print(f"\n已保存: {md_path}")
    return str(md_path)


# ---------- CLI ----------

def main():
    parser = argparse.ArgumentParser(description="微信公众号文章工具：抓取 + 智能重组")
    parser.add_argument("urls", nargs="*", help="微信文章链接（可传多个，留空则交互输入）")
    parser.add_argument("-o", "--output", default=".", help="根输出目录/输出文件路径（默认当前目录）")
    parser.add_argument("-t", "--topic", default="", help="主题文件夹名称/新文章主题")
    parser.add_argument("--no-images", action="store_true", help="不下载图片，保留原始 URL")
    parser.add_argument("--merge", help="合并指定目录下的多篇文章为新公众号文章")
    parser.add_argument("--push", help="将指定 Markdown 文件推送到微信草稿箱")
    args = parser.parse_args()

    # 推送到微信草稿箱
    if args.push:
        try:
            push_to_wx_draft(args.push)
        except Exception as e:
            sys.exit(f"推送失败: {e}")
        return

    # 处理文章合并功能
    if args.merge:
        try:
            # 加载文章
            articles = load_articles_from_dir(args.merge)
            if not articles:
                sys.exit("错误：未找到任何可合并的Markdown文章")

            # 获取主题
            topic = args.topic.strip()
            if not topic:
                topic = input("请输入新文章的主题（直接回车则自动生成）: ").strip()

            # 询问是否使用图片
            include_images = input("是否复用原有文章的配图？(y/n，默认y): ").strip().lower() != 'n'

            # 询问是否使用字节跳动风格排版
            use_bytedance = input("是否使用字节跳动(bytedance)风格排版？(y/n，默认y): ").strip().lower() != 'n'

            # 选择写作风格
            print("\n请选择写作风格（输入对应数字，默认0）：")
            style_list = list(ZIMEITI_STYLES.items())
            for i, (key, style) in enumerate(style_list):
                print(f"{i}. {style['name']} - {style['description']}")

            style_input = input("请选择风格编号：").strip()
            try:
                style_index = int(style_input) if style_input else 0
                if 0 <= style_index < len(style_list):
                    style_key = style_list[style_index][0]
                else:
                    style_key = "default"
            except:
                style_key = "default"

            selected_style = ZIMEITI_STYLES[style_key]
            print(f"已选择风格：{selected_style['name']}")

            # AI重组
            merged_content, all_images = merge_articles_with_ai(articles, topic, include_images, style_key)

            # 确定输出路径
            output_path = Path(args.output)
            if output_path.is_dir():
                # 如果是目录，生成默认文件名
                safe_topic = re.sub(r'[\\/*?:"<>|\n\r]', "", topic or "合并文章")[:60].strip()
                output_path = output_path / f"{safe_topic}.md"
            else:
                # 确保是md后缀
                if output_path.suffix.lower() != ".md":
                    output_path = output_path.with_suffix(".md")

            # 处理图片
            if include_images and all_images:
                # 创建输出目录的images文件夹
                output_img_dir = output_path.parent / "images"
                merged_content = replace_image_placeholders(merged_content, all_images, output_img_dir)
                print(f"已处理 {len(all_images)} 张配图，保存到: {output_img_dir.resolve()}")

            # 字节跳动风格排版处理
            if use_bytedance:
                print("正在应用字节跳动风格排版...")
                # 添加wewrite头部
                header = generate_wewrite_header(topic or "字节跳动风格文章")
                # 转换内容格式
                styled_content = convert_to_bytedance_style(merged_content)
                # 组合最终内容
                merged_content = header + "\n" + styled_content
                print("已应用字节跳动(bytedance)主题排版，完美适配wewrite工具")

            # 保存文件
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(merged_content, encoding="utf-8")
            print(f"\n合并完成！新文章已保存到: {output_path.resolve()}")

            # 打开生成的文章
            open_prompt = input("是否打开生成的文章？(y/n，默认n): ").strip().lower()
            if open_prompt == 'y':
                if sys.platform == 'darwin':
                    os.system(f'open "{output_path.resolve()}"')
                elif sys.platform == 'win32':
                    os.startfile(output_path.resolve())
                else:
                    os.system(f'xdg-open "{output_path.resolve()}"')
            return

        except Exception as e:
            sys.exit(f"合并失败: {str(e)}")

    # 确定主题文件夹
    topic = args.topic.strip()
    if not topic:
        topic = input("请输入主题名称（将作为文件夹名，直接回车则不创建主题文件夹）: ").strip()

    base_dir = args.output
    if topic:
        safe_topic = re.sub(r'[\\/*?:"<>|\n\r]', "", topic)
        base_dir = os.path.join(args.output, safe_topic)
        os.makedirs(base_dir, exist_ok=True)
        print(f"保存到: {base_dir}")

    # 收集链接
    urls = [u.strip() for u in args.urls if u.strip()]
    if not urls:
        print("请逐行输入文章链接，输入空行结束：")
        while True:
            line = input("  链接: ").strip()
            if not line:
                break
            urls.append(line)

    if not urls:
        sys.exit("错误：未提供任何链接。")

    # 批量保存
    print(f"\n共 {len(urls)} 篇文章，开始处理...\n")
    results = []
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        try:
            path = save_article(url, base_dir, not args.no_images)
            results.append((url, path, True))
        except Exception as e:
            print(f"  [失败] {e}", file=sys.stderr)
            results.append((url, str(e), False))
        print()

    # 汇总
    ok = [r for r in results if r[2]]
    fail = [r for r in results if not r[2]]
    print("=" * 50)
    print(f"完成：{len(ok)} 成功 / {len(fail)} 失败")
    if fail:
        print("\n失败链接：")
        for url, err, _ in fail:
            print(f"  {url}\n    原因: {err}")

    # 一站式合并：如果有成功抓取的文章，询问是否直接合并
    if ok and len(ok) >= 1:
        print("\n" + "=" * 50)
        merge_now = input(f"是否直接合并刚才抓取的 {len(ok)} 篇文章？(y/n，默认y): ").strip().lower() != 'n'
        if merge_now:
            try:
                print(f"\n开始合并 {len(ok)} 篇文章...")
                # 加载刚才抓取的文章
                articles = load_articles_from_dir(base_dir)
                if not articles:
                    print("错误：未找到可合并的文章")
                    return

                # 获取新文章主题
                new_topic = input("请输入新合并文章的主题：").strip()
                if not new_topic:
                    new_topic = topic or "合并文章"

                # 询问是否使用图片
                include_images = input("是否复用原有文章的配图？(y/n，默认y): ").strip().lower() != 'n'

                # 询问是否使用字节跳动风格排版
                use_bytedance = input("是否使用字节跳动(bytedance)风格排版？(y/n，默认y): ").strip().lower() != 'n'

                # 选择写作风格
                print("\n请选择写作风格（输入对应数字，默认0）：")
                style_list = list(ZIMEITI_STYLES.items())
                for i, (key, style) in enumerate(style_list):
                    print(f"{i}. {style['name']} - {style['description']}")

                style_input = input("请选择风格编号：").strip()
                try:
                    style_index = int(style_input) if style_input else 0
                    if 0 <= style_index < len(style_list):
                        style_key = style_list[style_index][0]
                    else:
                        style_key = "default"
                except:
                    style_key = "default"

                selected_style = ZIMEITI_STYLES[style_key]
                print(f"已选择风格：{selected_style['name']}")

                # AI重组
                merged_content, all_images = merge_articles_with_ai(articles, new_topic, include_images, style_key)

                # 确定输出路径（直接保存在当前base_dir下）
                safe_topic = re.sub(r'[\\/*?:"<>|\n\r]', "", new_topic)[:60].strip()
                output_path = Path(base_dir) / f"{safe_topic}.md"

                # 处理图片
                if include_images and all_images:
                    # 创建输出目录的images文件夹
                    output_img_dir = output_path.parent / "images"
                    merged_content = replace_image_placeholders(merged_content, all_images, output_img_dir)
                    print(f"已处理 {len(all_images)} 张配图，保存到: {output_img_dir.resolve()}")

                # 字节跳动风格排版处理
                if use_bytedance:
                    print("正在应用字节跳动风格排版...")
                    # 添加wewrite头部
                    header = generate_wewrite_header(new_topic)
                    # 转换内容格式
                    styled_content = convert_to_bytedance_style(merged_content)
                    # 组合最终内容
                    merged_content = header + "\n" + styled_content
                    print("已应用字节跳动(bytedance)主题排版，完美适配wewrite工具")

                # 保存文件
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(merged_content, encoding="utf-8")
                print(f"\n🎉 合并完成！最终文章已保存到: {output_path.resolve()}")

                # 打开生成的文章
                open_prompt = input("是否打开生成的文章？(y/n，默认n): ").strip().lower()
                if open_prompt == 'y':
                    if sys.platform == 'darwin':
                        os.system(f'open "{output_path.resolve()}"')
                    elif sys.platform == 'win32':
                        os.startfile(output_path.resolve())
                    else:
                        os.system(f'xdg-open "{output_path.resolve()}"')

            except Exception as e:
                print(f"合并失败: {str(e)}", file=sys.stderr)


if __name__ == "__main__":
    main()
