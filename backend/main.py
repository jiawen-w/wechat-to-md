"""
公众号炼金术 API · FastAPI 后端
职责：接收公众号文章 URL → 抓取正文 → AI 重写 → SSE 实时推送进度

启动：
    cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
import os
import json
import uuid
import asyncio
import io
import contextlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import wechat_to_md as wmd

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="公众号炼金术 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存任务存储
jobs: dict[str, dict] = {}

DOCS_DIR = Path(__file__).parent.parent / "docs"


# ── 请求模型 ──────────────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    urls: list[str]
    style: str = "default"
    topic: str = ""


# ── 路由 ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/styles")
async def api_styles():
    """返回所有可用风格"""
    return [
        {"key": k, "name": v["name"], "description": v["description"]}
        for k, v in wmd.ZIMEITI_STYLES.items()
    ]


@app.post("/api/run")
async def api_run(req: RunRequest):
    """提交任务，立即返回 job_id，后台异步执行"""
    if not req.urls:
        raise HTTPException(400, "urls 不能为空")
    urls = [u.strip() for u in req.urls if u.strip()]
    if not urls:
        raise HTTPException(400, "请至少提供一个有效链接")
    if len(urls) > 5:
        raise HTTPException(400, "最多支持 5 篇文章")

    job_id = uuid.uuid4().hex[:8]
    jobs[job_id] = {"status": "running", "logs": [], "result": None, "error": None}
    asyncio.create_task(_run_job(job_id, urls, req.style, req.topic))
    return {"job_id": job_id}


@app.get("/api/stream/{job_id}")
async def api_stream(job_id: str):
    """SSE：实时推送进度日志，任务结束时发送结果"""
    if job_id not in jobs:
        raise HTTPException(404, "任务不存在")

    async def event_gen():
        last = 0
        while True:
            job = jobs.get(job_id)
            if not job:
                break
            logs = job["logs"]
            if len(logs) > last:
                for msg in logs[last:]:
                    payload = json.dumps({"type": "log", "msg": msg}, ensure_ascii=False)
                    yield f"data: {payload}\n\n"
                last = len(logs)

            status = job["status"]
            if status == "done":
                payload = json.dumps(
                    {"type": "done", "result": job["result"]}, ensure_ascii=False
                )
                yield f"data: {payload}\n\n"
                return
            elif status == "failed":
                payload = json.dumps(
                    {"type": "error", "msg": job.get("error", "未知错误")},
                    ensure_ascii=False,
                )
                yield f"data: {payload}\n\n"
                return

            await asyncio.sleep(0.3)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── 后台任务 ──────────────────────────────────────────────────────────────────

async def _run_job(job_id: str, urls: list[str], style: str, topic: str):
    loop = asyncio.get_event_loop()

    def log(msg: str):
        jobs[job_id]["logs"].append(str(msg))

    def do_work():
        # 1. 逐篇抓取文章
        articles = []
        for i, url in enumerate(urls, 1):
            log(f"📥 [{i}/{len(urls)}] 正在抓取文章...")
            try:
                html = wmd.fetch_html(url)
                title, author, pub_time, content = wmd.parse_article(html)
                if content is None:
                    log(f"⚠️  无法解析文章正文，已跳过")
                    continue
                body_md = wmd.clean_md(wmd.node_to_md(content, None))
                meta_lines = [f"# {title}", ""]
                if author:
                    meta_lines.append(f"**公众号**: {author}")
                if pub_time:
                    meta_lines.append(f"**发布时间**: {pub_time}")
                meta_lines += ["", "---", "", body_md]
                full_md = "\n".join(meta_lines)
                articles.append((title, full_md, Path("/tmp")))
                log(f"✓  《{title[:30]}》  |  {author or '未知公众号'}  |  {len(body_md)} 字")
            except Exception as e:
                log(f"✗  抓取失败: {e}")

        if not articles:
            raise RuntimeError("所有文章抓取失败，请检查链接是否有效或文章是否需要登录")

        # 2. AI 重写
        style_name = wmd.ZIMEITI_STYLES.get(style, {}).get("name", style)
        log(f"\n🤖 开始用「{style_name}」风格重写 {len(articles)} 篇文章...")
        log("   （豆包 AI 处理中，约需 15-30 秒）")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result_md, _ = wmd.merge_articles_with_ai(
                articles, topic=topic, include_images=False, style_key=style
            )

        # 把 AI 输出的 print 也补进日志
        for line in buf.getvalue().splitlines():
            if line.strip():
                log(f"   {line}")

        # 提取标题（第一行 # 开头）
        first_line = result_md.strip().splitlines()[0] if result_md.strip() else ""
        result_title = first_line.lstrip("# ").strip() or "重写结果"

        char_count = len(result_md.replace(" ", "").replace("\n", ""))
        log(f"\n✅ 重写完成！共 {char_count} 字")
        return {
            "markdown": result_md,
            "title": result_title,
            "style": style,
            "style_name": style_name,
            "article_count": len(articles),
        }

    try:
        result = await loop.run_in_executor(None, do_work)
        jobs[job_id]["result"] = result
        jobs[job_id]["status"] = "done"
    except Exception as e:
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["status"] = "failed"


# ── 静态文件（docs/） ─────────────────────────────────────────────────────────

@app.get("/")
async def root():
    p = DOCS_DIR / "app.html"
    if p.exists():
        return FileResponse(str(p))
    return {"msg": "公众号炼金术 API 运行中"}

@app.get("/landing")
async def landing():
    p = DOCS_DIR / "index.html"
    if p.exists():
        return FileResponse(str(p))
    raise HTTPException(404)

if DOCS_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(DOCS_DIR)), name="static")
