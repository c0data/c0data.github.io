#!/usr/bin/env python3
"""Build posts/<slug>/index.html from posts/<slug>.md.

    python3 posts/build.py posts/the-message-format-in-ascii.md

Needs the `markdown` package. The page shell mirrors the landing page's
colours; control pictures (U+2400..U+241F) inside code are tinted by a
few lines of script at the bottom of the page.
"""
import html, pathlib, re, sys
import markdown

src = pathlib.Path(sys.argv[1])
text = src.read_text(encoding="utf-8")
lines = text.splitlines()
title = lines[0].lstrip("# ").strip()
byline = ""
body_start = 1
if len(lines) > 2 and lines[2].startswith("*"):
    byline = lines[2].strip("* ").strip()
    body_start = 3
body = markdown.markdown("\n".join(lines[body_start:]), extensions=["smarty"], output_format="html5")
description = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", body.split("</p>")[0]))[:200]
slug = src.stem
out = src.parent / slug / "index.html"
out.parent.mkdir(parents=True, exist_ok=True)

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} — C0DATA</title>
<meta name="description" content="{html.escape(description)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://c0data.github.io/posts/{slug}/">
<link rel="canonical" href="https://c0data.github.io/posts/{slug}/">
<style>
  :root {{
    --bg: #0d1117; --bg-raised: #161b22; --bg-code: #1c2129; --border: #30363d;
    --text: #c9d1d9; --text-dim: #8b949e; --text-bright: #e6edf3;
    --accent: #e3a93b; --accent-dim: #b8860b;
    --mono: 'SF Mono', 'Cascadia Code', 'Fira Code', 'JetBrains Mono', Consolas, monospace;
    --sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: var(--bg); color: var(--text); font-family: var(--sans); font-size: 1.0625rem; line-height: 1.65; }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  nav {{ border-bottom: 1px solid var(--border); background: var(--bg-raised); font-family: var(--mono); }}
  nav .container {{ max-width: 46rem; margin: 0 auto; padding: 0.9rem 1.25rem; display: flex; justify-content: space-between; align-items: center; }}
  nav .logo {{ font-weight: 700; letter-spacing: 0.05em; color: var(--text-bright); }}
  nav .logo span {{ color: var(--accent); }}
  nav ul {{ list-style: none; display: flex; gap: 1.25rem; font-size: 0.85rem; }}
  nav ul a {{ color: var(--text-dim); }}
  nav ul a:hover {{ color: var(--accent); text-decoration: none; }}
  main {{ max-width: 46rem; margin: 0 auto; padding: 3rem 1.25rem 4rem; }}
  h1 {{ font-size: 2rem; line-height: 1.2; color: var(--text-bright); margin-bottom: 0.5rem; }}
  .byline {{ color: var(--text-dim); font-family: var(--mono); font-size: 0.85rem; margin-bottom: 2.5rem; }}
  h2 {{ font-size: 1.3rem; color: var(--text-bright); margin: 2.5rem 0 0.9rem; }}
  p, ul, ol {{ margin-bottom: 1.1rem; }}
  li {{ margin-left: 1.4rem; }}
  em {{ color: var(--text-bright); }}
  code {{ font-family: var(--mono); font-size: 0.92em; background: var(--bg-code); padding: 0.1em 0.35em; border-radius: 3px; }}
  pre {{ font-family: var(--mono); font-size: 0.9rem; line-height: 1.55; background: var(--bg-code); border: 1px solid var(--border); border-radius: 6px; padding: 1rem 1.2rem; overflow-x: auto; margin: 1.2rem 0 1.4rem; }}
  pre code {{ background: none; padding: 0; font-size: inherit; }}
  .c0 {{ color: var(--accent); }}
  footer {{ border-top: 1px solid var(--border); color: var(--text-dim); font-family: var(--mono); font-size: 0.85rem; }}
  footer .container {{ max-width: 46rem; margin: 0 auto; padding: 1.5rem 1.25rem; display: flex; gap: 1.25rem; flex-wrap: wrap; }}
  footer a {{ color: var(--text-dim); }}
  footer a:hover {{ color: var(--accent); }}
</style>
</head>
<body>
<nav>
  <div class="container">
    <a class="logo" href="../../"><span>C0</span>DATA</a>
    <ul>
      <li><a href="../">Writing</a></li>
      <li><a href="https://github.com/c0data/c0-spec">Spec</a></li>
      <li><a href="https://github.com/c0data">GitHub</a></li>
    </ul>
  </div>
</nav>
<main>
<article>
<h1>{html.escape(title)}</h1>
<p class="byline">{html.escape(byline)}</p>
{body}
</article>
</main>
<footer>
  <div class="container">
    <a href="../../">c0data.github.io</a>
    <a href="https://github.com/c0data/c0-spec">Spec</a>
    <a href="https://github.com/c0data">GitHub</a>
    <a href="https://openbohemians.org">An Open Bohemians project</a>
  </div>
</footer>
<script>
// Tint the control pictures (U+2400..U+241F) inside code blocks.
for (const el of document.querySelectorAll('pre, code')) {{
  for (const node of [...el.childNodes].filter(n => n.nodeType === 3)) {{
    if (!/[\\u2400-\\u241f]/.test(node.nodeValue)) continue;
    const frag = document.createDocumentFragment();
    for (const part of node.nodeValue.split(/([\\u2400-\\u241f]+)/)) {{
      if (!part) continue;
      if (/^[\\u2400-\\u241f]+$/.test(part)) {{
        const s = document.createElement('span'); s.className = 'c0'; s.textContent = part; frag.appendChild(s);
      }} else frag.appendChild(document.createTextNode(part));
    }}
    node.replaceWith(frag);
  }}
}}
</script>
</body>
</html>
"""
out.write_text(page, encoding="utf-8")
print(out)
