// Section components

const { useState } = React;

function Nav() {
  return (
    <nav className="nav" data-screen-label="nav">
      <div className="shell nav-inner">
        <a href="#top" className="nav-logo">
          <span className="nav-logo-mark">炼</span>
          <span>公众号炼金术 <span style={{color: 'var(--ink-3)', fontWeight: 500, fontSize: 13, marginLeft: 4}}>· Alchemy</span></span>
        </a>
        <div className="nav-links">
          <a href="#flow">流程</a>
          <a href="#styles">8 种风格</a>
          <a href="#rules">写作铁律</a>
          <a href="#typography">排版</a>
          <a href="#cli">命令行</a>
          <a href="#faq">FAQ</a>
        </div>
        <a href="#cli" className="nav-cta">
          <span>克隆仓库</span>
          <span style={{fontSize: 14}}>→</span>
        </a>
      </div>
    </nav>
  );
}

function Hero() {
  return (
    <header className="hero dotgrid" id="top" data-screen-label="hero">
      <div className="shell">
        <span className="hero-tag">
          <span className="dot"></span>
          v0.3.1 · MIT 开源 · 本地运行
        </span>
        <h1 className="hero-title display">
          把<span className="ink-orange">爆款</span>
          <br />
          <span className="squiggle">炼</span>出来。
          <br />
          不是<span className="ink-purple">写</span>出来。
        </h1>
        <p className="hero-sub">
          一条给公众号作者用的命令行流水线：<b>抓取</b>同行 10 篇文章，
          用 8 种自媒体大 V 风格<b>重写</b>成一篇，套上 Naishi 紫色卡片<b>排版</b>，
          一键<b>推送</b>到草稿箱。
          <br />
          从看到选题，到打开公众号后台，只需要 5 分钟。
        </p>
        <div className="hero-ctas">
          <a className="btn btn-primary" href="#cli">
            立刻开始 <span>↗</span>
          </a>
          <a className="btn btn-ghost" href="#styles">
            看看 8 种风格写出来啥样
          </a>
        </div>

        <div className="hero-stats">
          <div className="hero-stat">
            <div className="hero-stat-num">8</div>
            <div className="hero-stat-label">自媒体大 V 写作风格</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-num">5<span style={{fontSize: 24}}> min</span></div>
            <div className="hero-stat-label">从选题到草稿箱</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-num">36</div>
            <div className="hero-stat-label">条去 AI 化写作铁律</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-num">100<span style={{fontSize: 24}}>%</span></div>
            <div className="hero-stat-label">本地运行，凭证不出本机</div>
          </div>
        </div>
      </div>

      <span className="sticker sticker-1">朱雀检测过线</span>
      <span className="sticker sticker-2">不上传任何数据</span>
      <span className="sticker sticker-3">支持豆包 / Claude / DS</span>
    </header>
  );
}

function Ticker() {
  const phrases = [
    "ALCHEMY", "抓取 → 重组 → 排版 → 推送", "DE-AI MODE",
    "8 STYLES", "微信原生卡片样式", "公众号炼金术",
    "v0.3.1", "MIT LICENSE", "本地运行",
  ];
  const items = [...phrases, ...phrases]; // duplicate for seamless loop
  return (
    <div className="ticker-wrap" aria-hidden="true">
      <div className="ticker">
        {items.map((p, i) => (
          <span key={i}>
            {p}
            <span className="star">✦</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function Flow() {
  return (
    <section className="section section-bg-paper" id="flow" data-screen-label="flow">
      <div className="shell">
        <span className="eyebrow alt-orange">FLOW · 流水线</span>
        <h2 className="section-title display">四步，<br/>把一堆爆款<br/>炼成你的一篇。</h2>
        <p className="section-lede">
          没有 SaaS 后台，没有"上传文件等待结果"。所有事情发生在你的电脑里——
          一条命令开始，一条命令结束。
        </p>

        <div className="steps">
          {window.PROCESS_STEPS.map((s, i) => (
            <div className="step" key={i}>
              <div className="step-num display">{s.num}</div>
              <div className="step-tag">{s.tag}</div>
              <div className="step-title">{s.title}</div>
              <div className="step-desc">{s.desc}</div>
              <div className="step-accent"></div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function StylesGallery() {
  const [active, setActive] = useState(0);
  const cur = window.WRITING_STYLES[active];

  return (
    <section className="section" id="styles" data-screen-label="styles">
      <div className="shell">
        <div style={{display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 24}}>
          <div>
            <span className="eyebrow">STYLES · 8 种笔法</span>
            <h2 className="section-title display">同一个选题，<br/>八个人写。</h2>
            <p className="section-lede">
              点左边切换风格，右边换成对应大 V 笔法下的成稿。题目都是同一个：
              <em style={{background: 'var(--yellow)', fontStyle: 'normal', padding: '0 4px'}}>「GPT-5 发布的那一天」</em>
              ——结果差远了。
            </p>
          </div>
          <div style={{
            background: 'var(--paper)', border: '2px solid var(--ink)',
            padding: '14px 18px', boxShadow: 'var(--shadow)',
            fontFamily: '"JetBrains Mono", monospace', fontSize: 12,
            transform: 'rotate(-1deg)', maxWidth: 240,
          }}>
            <div style={{fontWeight: 700, marginBottom: 6, fontSize: 13}}>📝 一句指令</div>
            <div style={{color: 'var(--ink-3)', lineHeight: 1.55}}>
              <span style={{color: 'var(--orange)'}}>--style</span> liangziwei <span style={{color: 'var(--ink-3)'}}>↩</span>
            </div>
          </div>
        </div>

        <div className="gallery">
          <div className="style-list">
            {window.WRITING_STYLES.map((s, i) => (
              <button
                key={s.key}
                className={`style-item ${i === active ? 'active' : ''}`}
                onClick={() => setActive(i)}
              >
                <span className="style-chip" style={{
                  background: i === active ? 'transparent' : s.color,
                  color: i === active ? '#fff' : (s.color === '#FFD60A' || s.color === '#C8F4A6' || s.color === '#B8F2A0' || s.color === '#FFC2D1' ? '#0B0B0B' : '#fff'),
                }}>{s.code}</span>
                <span className="style-item-body">
                  <div className="style-item-name">{s.name}</div>
                  <div className="style-item-desc">{s.desc}</div>
                </span>
                <span style={{
                  opacity: i === active ? 1 : 0.3,
                  fontSize: 18,
                  color: i === active ? 'var(--yellow)' : 'var(--ink)',
                }}>→</span>
              </button>
            ))}
          </div>

          <div className="style-preview">
            <div className="style-preview-head">
              <div className="style-preview-dots">
                <span></span><span></span><span></span>
              </div>
              <div>article.preview.md · {cur.code}</div>
              <div style={{color: '#888'}}>{cur.en}</div>
            </div>
            <div className="style-preview-body">
              <div className="style-preview-meta">
                <span className="style-preview-author">{cur.author}</span>
                <span className="style-preview-topic">// 选题：GPT-5 发布的那一天</span>
              </div>
              <h3 className="style-preview-title serif">{cur.title}</h3>
              <div className="style-preview-text">{cur.body}</div>
              <div className="style-preview-foot">
                <span className="style-preview-badge">✓ AI 浓度自检 8/8 通过</span>
                <span>—— 重组耗时 12.4s · 字数 {cur.body.replace(/\s/g, '').length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function DeAIRules() {
  return (
    <section className="section section-bg-ink" id="rules" data-screen-label="rules">
      <div className="shell">
        <div style={{maxWidth: 720}}>
          <span className="eyebrow alt">DE-AI RULES · 写作铁律</span>
          <h2 className="section-title display" style={{color: 'white'}}>
            朱雀过线，<br/>
            <span style={{color: 'var(--yellow)'}}>不是靠运气。</span>
          </h2>
          <p className="section-lede">
            我们把"看起来像 AI 写的"拆成 36 条可检查的特征，
            每次重写都会逐条扫描——任何一条没过关，重写。下面是其中最关键的六条。
          </p>
        </div>

        <div className="rules">
          {window.DE_AI_RULES.map((r, i) => (
            <div className="rule" key={i} style={{
              background: i % 3 === 0 ? 'transparent' : (i % 3 === 1 ? 'rgba(255,255,255,0.02)' : 'transparent'),
            }}>
              <div className="rule-num display">{r.num}</div>
              <div className="rule-title">{r.title}</div>
              <div className="rule-text">{r.text}</div>
              <div className="rule-bad">{r.bad}</div>
              <div className="rule-good">{r.good}</div>
            </div>
          ))}
        </div>

        <div style={{
          marginTop: 32, padding: '18px 22px',
          background: 'var(--yellow)', color: 'var(--ink)',
          border: '2px solid var(--yellow)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          flexWrap: 'wrap', gap: 14,
        }}>
          <div style={{fontWeight: 800, fontSize: 16}}>
            ⚠ 全部 36 条铁律，在 prompt 系统里逐条对照。任意一条不过关，就让模型重写。
          </div>
          <a href="https://github.com/jiawen-w/wechat-to-md#去ai味写作铁律" target="_blank" rel="noopener noreferrer" style={{
            background: 'var(--ink)', color: 'var(--yellow)',
            padding: '8px 14px', textDecoration: 'none', fontWeight: 700, fontSize: 13,
          }}>读完整规则 →</a>
        </div>
      </div>
    </section>
  );
}

function Typography() {
  return (
    <section className="section section-bg-paper" id="typography" data-screen-label="typography">
      <div className="shell">
        <span className="eyebrow alt-orange">TYPOGRAPHY · 排版</span>
        <h2 className="section-title display">
          直接给你<br/>
          <span style={{background: 'var(--purple)', color: 'white', padding: '0 12px'}}>微信原生</span>的卡片样。
        </h2>
        <p className="section-lede">
          微信不支持 &lt;style&gt;、不支持 ::before、不支持 counter。
          所有样式被编译成内联 CSS 注入到 HTML，封面自动压到 1MB 以内，
          外链改成上标脚注——草稿箱里看到的，就是订阅号读者看到的。
        </p>

        <div className="naishi-stage">
          <div className="naishi-callouts">
            <div className="naishi-callout">
              <span className="naishi-callout-num">1</span>
              <h4>编号标题</h4>
              <p>H2 自动生成紫色圆形数字徽章，H3 同色下划线，层级一眼可辨。</p>
            </div>
            <div className="naishi-callout">
              <span className="naishi-callout-num">2</span>
              <h4>紫色加粗 + 高亮</h4>
              <p>所有 &lt;strong&gt; 染成主色，让重点在长文里跳出来。</p>
            </div>
            <div className="naishi-callout">
              <span className="naishi-callout-num">3</span>
              <h4>引用 / 提示卡</h4>
              <p>:::quote / :::callout 容器自动转成淡紫色卡片块，移动端不挤。</p>
            </div>
            <div className="naishi-callout">
              <span className="naishi-callout-num">4</span>
              <h4>顶部色带 + 底部署名</h4>
              <p>整张文章包在一个圆角卡片里，顶有渐变色带，底有作者签名。</p>
            </div>
          </div>

          <div className="naishi-phone">
            <div className="naishi-phone-bar">
              <span>mp.weixin.qq.com</span>
              <span>16:24</span>
            </div>
            <div className="naishi-card"></div>
            <div className="naishi-body">
              <h1 className="naishi-h1">GPT-5 学会反问，这件小事改变了协作方式</h1>
              <p className="naishi-p">
                上周用 GPT-5 写一份产品需求文档，发现一个<b>很小的细节</b>：它会先反问。
              </p>
              <h2 className="naishi-h2">
                <span className="naishi-h2-badge">01</span>
                它先想，再写
              </h2>
              <p className="naishi-p">
                我给了一段含糊的描述，它没有立刻动笔，而是先问：「你希望这份文档是给工程师还是给老板？」
              </p>
              <div className="naishi-quote">
                这个动作很小，但它改变了我跟它协作的方式——以前我是「指挥」它，现在更像在「共写」。
              </div>
              <h2 className="naishi-h2">
                <span className="naishi-h2-badge">02</span>
                工具开始有「作者意识」了
              </h2>
              <p className="naishi-p">
                它不再是一个回答机，而是一个会替你顾及读者的<b>合作者</b>。
              </p>
            </div>
            <div className="naishi-foot">
              <span className="naishi-foot-l">✨ Naishi</span>
              <span className="naishi-foot-r">扫码关注 →</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function CLI() {
  return (
    <section className="section section-bg-purple" id="cli" data-screen-label="cli">
      <div className="shell">
        <span className="eyebrow alt">COMMAND LINE · 命令行</span>
        <h2 className="section-title display" style={{color: 'white'}}>
          一行命令，<br/>
          <span style={{color: 'var(--yellow)'}}>从链接到草稿。</span>
        </h2>
        <p className="section-lede">
          不需要图形界面。Python 3.10+ / OpenAI 兼容协议 / 一个公众号 AppID。
          所有事情发生在你电脑的 <span className="mono" style={{background: 'rgba(0,0,0,0.25)', padding: '2px 6px'}}>~/wechat-pub</span> 文件夹里。
        </p>

        <div className="cli-stage">
          <div className="terminal">
            <div className="terminal-bar">
              <div className="dots"><span></span><span></span><span></span></div>
              <div className="title">~/wechat-pub — alchemy.py</div>
            </div>
            <pre className="terminal-body" style={{margin: 0, whiteSpace: 'pre-wrap'}}>
<span className="term-comment"># 1. 抓 3 篇同主题文章</span>{'\n'}
<span className="term-prompt">$</span> <span className="term-cmd">python alchemy.py</span> <span className="term-arg">https://mp.weixin.qq.com/s/aaa \</span>{'\n'}
{'    '}<span className="term-arg">https://mp.weixin.qq.com/s/bbb https://mp.weixin.qq.com/s/ccc \</span>{'\n'}
{'    '}<span className="term-arg">-t "GPT-5 发布"</span>{'\n'}
<span className="term-out">✓ </span><span className="term-out-key">已抓取</span><span className="term-out"> 3 篇，下载图片 14 张</span>{'\n'}
{'\n'}
<span className="term-comment"># 2. 用「极客公园」风格重写</span>{'\n'}
<span className="term-prompt">$</span> <span className="term-cmd">python alchemy.py</span> <span className="term-arg">--merge ./GPT-5发布</span> \{'\n'}
{'    '}<span className="term-arg">--style jikegongyuan</span> <span className="term-arg">--topic "Altman 沉默的三秒"</span>{'\n'}
<span className="term-out">✓ </span><span className="term-out-key">已合并</span><span className="term-out"> 3 篇 → 1 篇（2156 字）</span>{'\n'}
<span className="term-out">✓ </span><span className="term-out-key">AI 浓度自检</span><span className="term-out"> 8 / 8 通过</span>{'\n'}
<span className="term-out">✓ </span><span className="term-out-key">字节跳动排版</span><span className="term-out"> 已套用</span>{'\n'}
{'\n'}
<span className="term-comment"># 3. 推送到公众号草稿箱</span>{'\n'}
<span className="term-prompt">$</span> <span className="term-cmd">python alchemy.py</span> <span className="term-arg">--push ./Altman沉默的三秒.md</span>{'\n'}
<span className="term-out">→ access_token 获取成功（7200s）</span>{'\n'}
<span className="term-out">→ 上传图片 14/14 · 封面已压缩 738KB</span>{'\n'}
<span className="term-out-ok">✓ 推送成功！草稿 media_id: 9_abc...</span>{'\n'}
<span className="term-out">  请登录公众号后台 → 草稿箱 查看</span>
            </pre>
          </div>

          <div>
            <div style={{fontSize: 13, fontWeight: 700, color: 'var(--yellow)', letterSpacing: '0.08em', marginBottom: 20}}>
              UNDER THE HOOD · 你不需要操心
            </div>
            <div className="feature-bullets">
              {window.FEATURES.map((f, i) => (
                <div className="feature-bullet" key={i}>
                  <div className="feature-bullet-mark" style={{
                    background: ['#FF5A1F','#FFD60A','#C8F4A6','#FFFFFF'][i],
                  }}>{f.mark}</div>
                  <div className="feature-bullet-body">
                    <h4 style={{color: 'white'}}>{f.title}</h4>
                    <p style={{color: 'rgba(255,255,255,0.75)'}}>{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <a className="btn btn-orange" href="https://github.com/jiawen-w/wechat-to-md" target="_blank" rel="noopener noreferrer" style={{marginTop: 28}}>
              一键克隆仓库 <span>↗</span>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

function FAQ() {
  const [open, setOpen] = useState(0);
  return (
    <section className="section section-bg-paper" id="faq" data-screen-label="faq">
      <div className="shell" style={{display: 'grid', gridTemplateColumns: '380px 1fr', gap: 48, alignItems: 'start'}}>
        <div>
          <span className="eyebrow">FAQ</span>
          <h2 className="section-title display" style={{fontSize: 'clamp(36px, 4vw, 56px)'}}>
            常见<br/>问题。
          </h2>
          <p style={{color: 'var(--ink-2)', fontSize: 15, lineHeight: 1.7, marginTop: 16}}>
            没在下面找到？给作者写信：
            <br/>
            <span className="mono" style={{
              background: 'var(--ink)', color: 'var(--yellow)',
              padding: '2px 8px', display: 'inline-block', marginTop: 6,
            }}>hi@alchemy.pub</span>
          </p>
        </div>
        <div className="faq">
          {window.FAQS.map((f, i) => (
            <div key={i} className={`faq-row ${open === i ? 'open' : ''}`}>
              <button className="faq-q" onClick={() => setOpen(open === i ? -1 : i)}>
                <span>{f.q}</span>
                <span className="plus">+</span>
              </button>
              <div className="faq-a"><div className="faq-a-inner">{f.a}</div></div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Final() {
  return (
    <section className="final" id="get">
      <div className="shell">
        <h2 className="display">
          停止<span className="y">手搓</span>，<br/>
          开始<span className="o">炼金</span>。
        </h2>
        <p>开源 · MIT · Python 3.10+ · 不需要服务器 · 不需要订阅</p>
        <div className="final-ctas">
          <a className="btn btn-primary" href="https://github.com/jiawen-w/wechat-to-md" target="_blank" rel="noopener noreferrer">git clone <span>↗</span></a>
          <a className="btn btn-ghost" href="#styles">先看 8 种风格</a>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer shell">
      <div className="footer-l">
        <span className="nav-logo-mark" style={{width: 24, height: 24, fontSize: 13}}>炼</span>
        <span style={{fontWeight: 700}}>公众号炼金术</span>
        <span style={{color: 'var(--ink-3)'}}>· © 2026 · MIT License</span>
      </div>
      <div className="footer-r">
        <a href="https://github.com/jiawen-w/wechat-to-md" target="_blank" rel="noopener noreferrer">GitHub</a>
        <a href="https://github.com/jiawen-w/wechat-to-md#readme" target="_blank" rel="noopener noreferrer">文档</a>
        <a href="https://github.com/jiawen-w/wechat-to-md/commits/main" target="_blank" rel="noopener noreferrer">变更日志</a>
        <a href="https://github.com/jiawen-w" target="_blank" rel="noopener noreferrer">作者</a>
      </div>
    </footer>
  );
}

Object.assign(window, {
  Nav, Hero, Ticker, Flow, StylesGallery, DeAIRules, Typography, CLI, FAQ, Final, Footer,
});
