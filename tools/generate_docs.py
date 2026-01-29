"""
Enhanced Documentation Generator for Ornata.
CommonMark-compliant with advanced features, syntax highlighting, and modern UX.
"""

from __future__ import annotations

import html
import importlib
import inspect
import os
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DocConfig:
    package_root: str = "src/ornata"
    package_name: str = "ornata"
    output_dir: str = "docs/html"
    project_title: str = "Ornata Docs"
    verbose: bool = True


@dataclass
class SymbolReference:
    module_page: str
    module_name: str
    anchor: str


PLACEHOLDER_PATTERN = re.compile(r'CTX-[A-Z]+-[0-9a-f]+-CTX')
SYMBOL_WORD_PATTERN = re.compile(r'\b[A-Za-z_]\w*\b')
MAX_SYMBOL_LINKS = 3


CSS_STYLES = """
:root {
    --bg-body: #f8fafc;
    --bg-sidebar: #ffffff;
    --bg-card: #ffffff;
    --text-main: #0f172a;
    --text-muted: #64748b;
    --border-color: #e2e8f0;
    --primary: #3b82f6;
    --primary-hover: #2563eb;
    --primary-light: #eff6ff;
    --code-bg: #1e293b;
    --code-text: #e2e8f0;
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    --gradient-accent: linear-gradient(90deg, #3b82f6, #60a5fa);
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
    --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-body: #0f172a;
        --bg-sidebar: #1e293b;
        --bg-card: #1e293b;
        --text-main: #f1f5f9;
        --text-muted: #94a3b8;
        --border-color: #334155;
        --primary: #60a5fa;
        --primary-hover: #93c5fd;
        --primary-light: rgba(59, 130, 246, 0.15);
        --code-bg: #020617;
        --code-text: #f8fafc;
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.2);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.3);
        --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.3);
    }
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body { 
    font-family: var(--font-sans); 
    background: var(--bg-body); 
    color: var(--text-main); 
    height: 100vh; 
    display: flex; 
    overflow: hidden; 
    line-height: 1.6; 
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

a { 
    color: var(--primary); 
    text-decoration: none; 
    transition: color 0.2s ease, text-decoration 0.2s ease; 
    font-weight: 500; 
}
a:hover { color: var(--primary-hover); text-decoration: underline; }
a.broken-link { 
    color: var(--error); 
    text-decoration: line-through; 
    cursor: not-allowed; 
}
a.broken-link:hover { color: var(--error); }

/* LAYOUT */
.layout { display: flex; width: 100%; height: 100%; }

/* SIDEBAR */
.sidebar { 
    width: 300px; 
    background: var(--bg-sidebar); 
    border-right: 1px solid var(--border-color); 
    display: flex; 
    flex-direction: column; 
    flex-shrink: 0; 
    z-index: 20;
    position: sticky;
    top: 0;
    height: 100vh;
}
.sidebar-header { 
    padding: 1.5rem; 
    border-bottom: 1px solid var(--border-color);
    background: var(--gradient-accent);
    color: white;
}
.brand { 
    font-size: 1.25rem; 
    font-weight: 800; 
    letter-spacing: -0.025em; 
    display: flex; 
    align-items: center; 
    gap: 0.5rem;
    color: white;
}
.search-wrapper { margin-top: 1rem; position: relative; }
.search-input { 
    width: 100%; 
    padding: 0.6rem 0.8rem; 
    border-radius: 6px; 
    border: 1px solid rgba(255,255,255,0.3); 
    background: rgba(255,255,255,0.15); 
    color: white; 
    font-family: inherit; 
    font-size: 0.9rem; 
    transition: all 0.2s; 
}
.search-input::placeholder { color: rgba(255,255,255,0.7); }
.search-input:focus { 
    outline: none; 
    background: rgba(255,255,255,0.25);
    box-shadow: 0 0 0 3px rgba(255,255,255,0.2); 
}

.nav-scroller { flex: 1; overflow-y: auto; padding: 1rem 0; }
.nav-group { margin-bottom: 1.5rem; }
.nav-header { 
    padding: 0 1.5rem 0.5rem; 
    font-size: 0.75rem; 
    text-transform: uppercase; 
    letter-spacing: 0.05em; 
    color: var(--text-muted); 
    font-weight: 700; 
}
.nav-link { 
    display: block; 
    padding: 0.4rem 1.5rem; 
    font-size: 0.9rem; 
    color: var(--text-muted); 
    border-left: 3px solid transparent; 
    transition: all 0.2s ease; 
    white-space: nowrap; 
    overflow: hidden; 
    text-overflow: ellipsis; 
}
.nav-link:hover { 
    background: var(--primary-light); 
    color: var(--primary); 
    text-decoration: none;
}
.nav-link.active { 
    border-left-color: var(--primary); 
    background: var(--primary-light); 
    color: var(--primary); 
    font-weight: 600; 
}

/* MAIN AREA */
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; position: relative; }

/* TOP BAR */
.topbar { 
    flex-shrink: 0; 
    height: 60px; 
    background: var(--bg-sidebar); 
    border-bottom: 1px solid var(--border-color); 
    display: flex; 
    align-items: center; 
    padding: 0 2rem; 
    justify-content: space-between; 
    position: sticky; 
    top: 0; 
    z-index: 10; 
    backdrop-filter: blur(8px); 
}
.breadcrumbs { 
    display: flex; 
    align-items: center; 
    gap: 0.5rem; 
    color: var(--text-muted); 
    font-size: 0.9rem; 
}
.crumb-link { 
    color: var(--text-muted); 
    transition: color 0.2s; 
    position: relative;
}
.crumb-link:hover { 
    color: var(--primary); 
    text-decoration: none; 
}
.crumb-link:hover::after {
    content: attr(data-tooltip);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    background: var(--code-bg);
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    white-space: nowrap;
    margin-bottom: 0.25rem;
}
.crumb-active { color: var(--text-main); font-weight: 600; }
.crumb-separator { opacity: 0.4; font-size: 0.8em; }
.back-btn { 
    display: inline-flex; 
    align-items: center; 
    gap: 0.4rem; 
    padding: 0.4rem 0.8rem; 
    background: transparent; 
    border: 1px solid var(--border-color); 
    border-radius: 6px; 
    color: var(--text-main); 
    font-size: 0.85rem; 
    font-weight: 500; 
    cursor: pointer; 
    transition: all 0.2s; 
}
.back-btn:hover { 
    background: var(--primary-light); 
    border-color: var(--primary); 
    color: var(--primary); 
}

/* CONTENT SCROLL */
.content-scroll { 
    flex: 1; 
    overflow-y: auto; 
    padding: 2rem 4rem; 
    scroll-behavior: smooth; 
}
.container { max-width: 900px; margin: 0 auto; padding-bottom: 6rem; }

/* TYPOGRAPHY */
h1 { 
    font-size: 2.5rem; 
    font-weight: 800; 
    letter-spacing: -0.03em; 
    margin: 0 0 1.5rem; 
    line-height: 1.2; 
    color: var(--text-main);
    background: var(--gradient-accent);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
h2 { 
    font-size: 1.75rem; 
    font-weight: 700; 
    letter-spacing: -0.01em; 
    margin: 3rem 0 1rem; 
    padding-bottom: 0.5rem; 
    border-bottom: 2px solid var(--border-color); 
    color: var(--text-main);
    line-height: 1.3;
}
h3 { 
    font-size: 1.25rem; 
    font-weight: 600; 
    margin: 2rem 0 0.75rem;
    line-height: 1.4;
}
h4 {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 1.5rem 0 0.5rem;
    line-height: 1.4;
}
p { 
    margin-bottom: 1.25rem; 
    font-size: 1rem; 
    color: var(--text-main); 
    line-height: 1.7; 
}

/* CODE */
code.inline { 
    font-family: var(--font-mono); 
    font-size: 0.85em; 
    background: var(--primary-light); 
    color: var(--primary); 
    padding: 0.2em 0.4em; 
    border-radius: 4px; 
}
pre { 
    background: var(--code-bg); 
    color: var(--code-text); 
    border-radius: 8px; 
    padding: 1.25rem; 
    overflow-x: auto; 
    margin: 1.5rem 0; 
    box-shadow: var(--shadow-lg); 
    border: 1px solid var(--border-color);
    position: relative;
    line-height: 1.5;
}
pre code { 
    background: transparent; 
    color: inherit; 
    padding: 0; 
    font-size: 0.9em; 
    white-space: pre; 
    font-family: var(--font-mono);
}
pre.language-python code { color: var(--code-text); }

/* Syntax Highlighting */
.keyword { color: #c792ea; font-weight: 600; }
.string { color: #c3e88d; }
.number { color: #f78c6c; }
.comment { color: #546e7a; font-style: italic; }
.function { color: #82aaff; }
.class-name { color: #ffcb6b; font-weight: 600; }
.builtin { color: #89ddff; }
.decorator { color: #f07178; }

/* Copy Button */
.copy-btn {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    color: white;
    padding: 0.3rem 0.6rem;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s;
    font-family: var(--font-sans);
}
.copy-btn:hover {
    background: rgba(255,255,255,0.2);
}
.copy-btn.copied {
    background: var(--success);
    border-color: var(--success);
}

/* Line Numbers */
.line-numbers {
    counter-reset: line;
}
.line-numbers code {
    counter-increment: line;
}
.line-numbers code::before {
    content: counter(line);
    display: inline-block;
    width: 2em;
    margin-right: 1em;
    color: var(--text-muted);
    text-align: right;
    user-select: none;
}

/* LISTS */
ul, ol { 
    margin: 1rem 0 1rem 1.5rem; 
    padding: 0; 
}
li { 
    margin: 0.5rem 0; 
    line-height: 1.6; 
}
ul ul, ol ol, ul ol, ol ul { 
    margin: 0.25rem 0 0.25rem 1.5rem; 
}

/* Task Lists */
.task-list { list-style: none; margin-left: 0; }
.task-list li { position: relative; padding-left: 1.75rem; }
.task-list input[type="checkbox"] {
    position: absolute;
    left: 0;
    top: 0.25rem;
    margin: 0;
}
.task-list input[type="checkbox"]:checked + span {
    text-decoration: line-through;
    color: var(--text-muted);
}

/* BLOCKQUOTE */
blockquote { 
    border-left: 4px solid var(--primary); 
    background: var(--bg-body); 
    margin: 1.5rem 0; 
    padding: 1rem 1.5rem; 
    border-radius: 0 8px 8px 0; 
    font-style: italic; 
    color: var(--text-muted);
    box-shadow: var(--shadow-sm);
}

/* TABLES */
table { 
    width: 100%; 
    border-collapse: collapse; 
    margin: 2rem 0; 
    border-radius: 8px; 
    overflow: hidden; 
    border: 1px solid var(--border-color); 
    box-shadow: var(--shadow-md);
}
th, td { 
    text-align: left; 
    padding: 0.75rem 1rem; 
    border-bottom: 1px solid var(--border-color); 
}
th { 
    background: var(--bg-sidebar); 
    font-weight: 600; 
    font-size: 0.85rem; 
    text-transform: uppercase; 
    letter-spacing: 0.05em; 
    color: var(--text-muted); 
}
th.center, td.center { text-align: center; }
th.right, td.right { text-align: right; }
tr:last-child td { border-bottom: none; }
tbody tr:nth-child(even) { background: rgba(59, 130, 246, 0.05); }
tbody tr:hover { background: var(--primary-light); }

/* HORIZONTAL RULE */
hr { 
    border: 0; 
    border-top: 2px solid var(--border-color); 
    margin: 3rem 0; 
}

/* STRIKETHROUGH */
del { 
    text-decoration: line-through; 
    color: var(--text-muted); 
}

/* FOOTNOTES */
.footnotes { 
    margin-top: 3rem; 
    padding-top: 1.5rem; 
    border-top: 1px solid var(--border-color); 
    font-size: 0.9rem; 
}
.footnote-ref { 
    color: var(--primary); 
    font-size: 0.75em; 
    vertical-align: super; 
}

/* API CARDS */
.api-card { 
    margin-bottom: 2rem; 
    background: var(--bg-card); 
    border: 1px solid var(--border-color); 
    border-radius: 10px; 
    overflow: hidden; 
    box-shadow: var(--shadow-md); 
    transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s; 
}
.api-card:hover { 
    transform: translateY(-2px); 
    box-shadow: var(--shadow-lg); 
    border-color: var(--primary); 
}
.api-card.class-card { border-left: 4px solid #4338ca; }
.api-card.function-card { border-left: 4px solid #15803d; }
.api-card.method-card { border-left: 4px solid #475569; }

.api-header { 
    background: var(--bg-sidebar); 
    padding: 0.75rem 1.25rem; 
    border-bottom: 1px solid var(--border-color); 
    font-family: var(--font-mono); 
    font-size: 0.9rem; 
    display: flex; 
    align-items: center; 
    flex-wrap: wrap; 
    gap: 0.75rem; 
}
.tag { 
    padding: 3px 8px; 
    border-radius: 4px; 
    font-size: 0.7rem; 
    font-weight: 700; 
    text-transform: uppercase; 
    letter-spacing: 0.5px; 
}
.tag-class { background: #e0e7ff; color: #4338ca; border: 1px solid #c7d2fe; }
.tag-func { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
.tag-method { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }

.api-name { 
    font-weight: 700; 
    color: var(--primary); 
    font-size: 1rem; 
}
.api-sig { 
    color: var(--text-muted); 
    opacity: 0.8; 
    font-size: 0.85rem; 
}
.type-hint { 
    color: #f59e0b; 
    font-weight: 600; 
}
.api-body { padding: 1.25rem; }

/* Collapsible Sections */
.collapsible-toggle {
    background: var(--bg-body);
    border: 1px solid var(--border-color);
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 1rem 0;
    transition: all 0.2s;
}
.collapsible-toggle:hover {
    background: var(--primary-light);
    border-color: var(--primary);
}
.collapsible-content {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
}
.collapsible-content.expanded {
    max-height: 10000px;
}

/* UTILITIES */
.hidden { display: none !important; }
.text-muted { color: var(--text-muted); }
.text-center { text-align: center; }
.mt-4 { margin-top: 2rem; }

/* EMOJI */
.emoji { 
    display: inline-block; 
    width: 1.2em; 
    height: 1.2em; 
    vertical-align: -0.2em; 
}

/* RESPONSIVE */
@media (max-width: 768px) {
    .sidebar { width: 250px; }
    .content-scroll { padding: 1rem 1.5rem; }
    h1 { font-size: 2rem; }
    h2 { font-size: 1.5rem; }
}

"""

JS_SCRIPT = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const navLinks = document.querySelectorAll('.nav-link');
    const copyButtons = document.querySelectorAll('.copy-btn');
    
    // SEARCH with fuzzy matching
    searchInput?.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase().trim();
        navLinks.forEach(link => {
            const text = link.textContent.toLowerCase();
            // Simple fuzzy: check if all chars in term appear in order
            let pos = 0;
            for (let char of term) {
                pos = text.indexOf(char, pos);
                if (pos === -1) {
                    link.classList.add('hidden');
                    return;
                }
                pos++;
            }
            link.classList.remove('hidden');
            
            // Highlight matching text
            if (term) {
                const regex = new RegExp(`(${term})`, 'gi');
                link.innerHTML = link.textContent.replace(regex, '<mark>$1</mark>');
            }
        });
    });

    // ACTIVE STATE & SCROLLSPY
    const currentPath = window.location.pathname.split('/').pop();
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
            link.scrollIntoView({ block: 'center', behavior: 'smooth' });
        }
    });

    // COPY BUTTONS
    copyButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const pre = btn.parentElement;
            const code = pre.querySelector('code');
            try {
                await navigator.clipboard.writeText(code.textContent);
                btn.textContent = 'Copied!';
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.textContent = 'Copy';
                    btn.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('Copy failed:', err);
            }
        });
    });

    // COLLAPSIBLE SECTIONS
    document.querySelectorAll('.collapsible-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const content = toggle.nextElementSibling;
            content.classList.toggle('expanded');
            const icon = toggle.querySelector('.toggle-icon');
            if (icon) {
                icon.textContent = content.classList.contains('expanded') ? '▼' : '▶';
            }
        });
    });

    // AUTO-LINK DETECTION
    document.querySelectorAll('a').forEach(link => {
        const href = link.getAttribute('href');
        if (href && href.startsWith('#') && href !== '#') {
            // Check if target exists
            const target = document.querySelector(href);
            if (!target) {
                link.classList.add('broken-link');
                link.title = 'Target not found';
            }
        }
    });
});
</script>
"""


class EnhancedMarkdownParser:
    def __init__(
        self,
        known_modules: list[str],
        current_package: str,
        all_symbols: dict[str, SymbolReference],
        symbol_patterns: dict[str, re.Pattern[str]] | None = None,
    ):
        self.known_modules = set(known_modules)
        self.current_package = current_package
        self.all_symbols = all_symbols
        self.placeholders = {}
        self.footnotes = {}
        self.symbol_patterns = symbol_patterns or {}

    def parse(self, text: str) -> str:
        if not text:
            return ""

        text = html.escape(text, quote=False)
        text = self._protect_code_blocks(text)
        text = self._process_footnotes(text)
        text = self._parse_headers(text)
        text = re.sub(r'^\s*[-*_]{3,}\s*$', '<hr>', text, flags=re.MULTILINE)
        text = self._parse_links(text)
        text = self._auto_link_urls(text)
        text = self._auto_link_symbols(text)
        text = self._parse_inline_formatting(text)
        text = self._parse_lists(text)
        text = self._parse_blockquotes(text)
        text = self._parse_tables(text)
        text = self._apply_paragraphs(text)
        text = self._parse_emoji(text)
        text = self._restore_placeholders(text)
        return text

    def _protect_code_blocks(self, text: str) -> str:
        def preserve_code(match):
            uid = f"CTX-PROTECTED-{uuid.uuid4().hex}-CTX"
            lang = match.group(1) or 'python'
            code_content = match.group(2)
            highlighted = self._syntax_highlight(code_content, lang)
            self.placeholders[uid] = f'''<pre class="language-{lang}">
<button class="copy-btn">Copy</button>
<code>{highlighted}</code>
</pre>'''
            return uid
        text = re.sub(r'```(\w+)?\n(.*?)```', preserve_code, text, flags=re.DOTALL)
        return text

    def _syntax_highlight(self, code: str, lang: str) -> str:
        """Basic Python syntax highlighting"""
        if lang != 'python':
            return code

        keywords = r'\b(def|class|if|elif|else|for|while|return|import|from|as|try|except|finally|with|lambda|yield|async|await|pass|break|continue|raise|assert|del|global|nonlocal|in|is|and|or|not)\b'
        code = re.sub(keywords, r'<span class="keyword">\1</span>', code)
        code = re.sub(r'(["\'])(?:(?=(\\?))\2.)*?\1', r'<span class="string">\g<0></span>', code)
        code = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="number">\1</span>', code)
        code = re.sub(r'(#.*?)$', r'<span class="comment">\1</span>', code, flags=re.MULTILINE)
        code = re.sub(r'(@\w+)', r'<span class="decorator">\1</span>', code)
        code = re.sub(r'(@\w+)', r'<span class="decorator">\1</span>', code)
        builtins = r'\b(print|len|range|str|int|float|list|dict|set|tuple|bool|type|isinstance|enumerate|zip|map|filter|sum|min|max|abs|all|any|sorted|reversed)\b'
        code = re.sub(builtins, r'<span class="builtin">\1</span>', code)
        return code

    def _process_footnotes(self, text: str) -> str:
        """Extract footnote definitions"""
        def extract_footnote(match):
            ref = match.group(1)
            content = match.group(2)
            self.footnotes[ref] = content
            return ''

        text = re.sub(r'^\[\^(\w+)\]:\s*(.+)$', extract_footnote, text, flags=re.MULTILINE)
        return text

    def _parse_headers(self, text: str) -> str:
        for i in range(6, 0, -1):
            text = re.sub(
                r'^{} (.+)$'.format('#' * i), 
                r'<h{0} id="\1">\1</h{0}>'.format(i), 
                text, 
                flags=re.MULTILINE
            )
        return text

    def _parse_links(self, text: str) -> str:
        def link_replacer(match):
            label, target = match.groups()
            if target.startswith(("http://", "https://")):
                return f'<a href="{target}" target="_blank">{label}</a>'

            if target in self.known_modules:
                return f'<a href="{target}.html">{label}</a>'

            if self.current_package:
                candidate = f"{self.current_package}.{target}"
                if candidate in self.known_modules:
                    return f'<a href="{candidate}.html">{label}</a>'

            symbol_ref = self.all_symbols.get(target)
            if symbol_ref:
                return f'<a href="{symbol_ref.module_page}#{target}">{label}</a>'

            if "." in target:
                module_part, _, symbol_name = target.rpartition('.')
                symbol_ref = self.all_symbols.get(symbol_name)
                if symbol_ref and symbol_ref.module_name == module_part:
                    return f'<a href="{symbol_ref.module_page}#{symbol_name}">{label}</a>'

            matches = [m for m in self.known_modules if m.endswith(f".{target}")]
            if len(matches) == 1:
                return f'<a href="{matches[0]}.html">{label}</a>'

            return f'<a href="#" class="broken-link" title="Link target not found: {target}">{label}</a>'

        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_replacer, text)
        text = re.sub(r'\[\^(\w+)\]', r'<sup class="footnote-ref"><a href="#fn-\1">\1</a></sup>', text)
        return text

    def _auto_link_urls(self, text: str) -> str:
        """Auto-linkify plain URLs"""
        url_pattern = r'(?<!href=")(https?://[^\s<>"]+)'
        text = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)
        return text

    def _auto_link_symbols(self, text: str) -> str:
        """Auto-link class and function names"""
        for symbol, pattern in self.symbol_patterns.items():
            symbol_ref = self.all_symbols.get(symbol)
            if not symbol_ref:
                continue
            replacement = (
                f'<a href="{symbol_ref.module_page}#{symbol_ref.anchor}" '
                f'title="Jump to {symbol}">{symbol}</a>'
            )
            text = pattern.sub(replacement, text, count=3)
        return text

    def _parse_inline_formatting(self, text: str) -> str:
        text = re.sub(r'`([^`]+)`', r'<code class="inline">\1</code>', text)
        text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
        return text

    def _parse_lists(self, text: str) -> str:
        lines = text.split('\n')
        out = []
        stack = []
        for line in lines:
            task_match = re.match(r'^(\s*)[-*]\s+\[([ xX])\]\s+(.+)', line)
            if task_match:
                indent = len(task_match.group(1))
                checked = task_match.group(2).lower() == 'x'
                content = task_match.group(3)
                self._adjust_stack(stack, out, 'task', indent)
                check_attr = 'checked' if checked else ''
                out.append(f'<li><input type="checkbox" {check_attr} disabled><span>{content}</span></li>')
                continue

            ul_match = re.match(r'^(\s*)[-*]\s+(.+)', line)
            if ul_match:
                indent = len(ul_match.group(1))
                content = ul_match.group(2)
                self._adjust_stack(stack, out, 'ul', indent)
                out.append(f'<li>{content}</li>')
                continue

            ol_match = re.match(r'^(\s*)(\d+)\.\s+(.+)', line)
            if ol_match:
                indent = len(ol_match.group(1))
                content = ol_match.group(3)
                self._adjust_stack(stack, out, 'ol', indent)
                out.append(f'<li>{content}</li>')
                continue

            while stack:
                list_type, _ = stack.pop()
                tag = 'ul' if list_type in ('ul', 'task') else 'ol'
                _class_attr = ' class="task-list"' if list_type == 'task' else ''
                out.append(f'</{tag}>')
            out.append(line)

        while stack:
            list_type, _ = stack.pop()
            tag = 'ul' if list_type in ('ul', 'task') else 'ol'
            out.append(f'</{tag}>')
        return '\n'.join(out)

    def _adjust_stack(self, stack, out, list_type, indent):
        """Manage nested list stack"""
        while stack and stack[-1][1] >= indent:
            prev_type, _ = stack.pop()
            tag = 'ul' if prev_type in ('ul', 'task') else 'ol'
            out.append(f'</{tag}>')

        if not stack or stack[-1][1] < indent:
            tag = 'ul' if list_type in ('ul', 'task') else 'ol'
            class_attr = ' class="task-list"' if list_type == 'task' else ''
            out.append(f'<{tag}{class_attr}>')
            stack.append((list_type, indent))

    def _parse_blockquotes(self, text: str) -> str:
        lines = text.split('\n')
        out = []
        in_quote = False
        quote_lines = []
        for line in lines:
            if line.strip().startswith('&gt;'):
                content = re.sub(r'^\s*&gt;\s?', '', line)
                quote_lines.append(content)
                in_quote = True
            else:
                if in_quote:
                    out.append(f'<blockquote>{" ".join(quote_lines)}</blockquote>')
                    quote_lines = []
                    in_quote = False
                out.append(line)

        if in_quote:
            out.append(f'<blockquote>{" ".join(quote_lines)}</blockquote>')
        return '\n'.join(out)

    def _parse_tables(self, text: str) -> str:
        lines = text.split('\n')
        out = []
        in_table = False
        alignments = []
        is_header_row = True
        for _, line in enumerate(lines):
            if '|' in line and 'CTX-PROTECTED' not in line and not line.strip().startswith('<'):
                cols = [c.strip() for c in line.strip('|').split('|')]
                
                is_sep = all(re.match(r'^:?-+:?', c) for c in cols if c)
                if is_sep:
                    alignments = []
                    for col in cols:
                        if col.startswith(':') and col.endswith(':'):
                            alignments.append('center')
                        elif col.endswith(':'):
                            alignments.append('right')
                        else:
                            alignments.append('left')
                    is_header_row = False
                    continue

                if not in_table:
                    out.append('<table><thead>' if is_header_row else '<table><tbody>')
                    in_table = True

                cells = []
                for j, col in enumerate(cols):
                    align_class = alignments[j] if j < len(alignments) and alignments[j] != 'left' else ''
                    class_attr = f' class="{align_class}"' if align_class else ''
                    tag = 'th' if is_header_row else 'td'
                    cells.append(f'<{tag}{class_attr}>{col}</{tag}>')

                out.append(f"<tr>{''.join(cells)}</tr>")
                if is_header_row:
                    out.append('</thead><tbody>')
                    is_header_row = False
            else:
                if in_table:
                    out.append('</tbody></table>')
                    in_table = False
                    alignments = []
                    is_header_row = True
                out.append(line)

        if in_table:
            out.append('</tbody></table>')

        return '\n'.join(out)

    def _apply_paragraphs(self, text: str) -> str:
        block_tags = ('<h', '<ul', '<ol', '<li', '<pre', '<blockquote', '<table', 
                     '<tr', '<td', '<th', '<div', '<hr', '<p', 'CTX-PROTECTED', '<thead', '<tbody')
        paras = re.split(r'\n\s*\n', text)
        out = []

        for p in paras:
            p = p.strip()
            if not p:
                continue

            is_block = any(p.startswith(tag) for tag in block_tags)

            if is_block:
                out.append(p)
            else:
                out.append(f'<p>{p}</p>')

        return '\n'.join(out)

    def _parse_emoji(self, text: str) -> str:
        """Convert :emoji: to Unicode"""
        emoji_map = {
            ':smile:': '😊',
            ':heart:': '❤️',
            ':check:': '✓',
            ':cross:': '✗',
            ':star:': '⭐',
            ':warning:': '⚠️',
            ':info:': 'ℹ️',
            ':rocket:': '🚀',
            ':fire:': '🔥',
            ':thumbsup:': '👍',
            ':thumbsdown:': '👎',
        }
        for code, emoji in emoji_map.items():
            text = text.replace(code, f'<span class="emoji">{emoji}</span>')
        return text

    def _restore_placeholders(self, text: str) -> str:
        for uid, html_code in self.placeholders.items():
            text = text.replace(uid, html_code)

        if self.footnotes:
            footnotes_html = '<div class="footnotes"><h2>Footnotes</h2><ol>'
            for ref, content in self.footnotes.items():
                footnotes_html += f'<li id="fn-{ref}">{content}</li>'
            footnotes_html += '</ol></div>'
            text += footnotes_html

        self.placeholders.clear()
        self.footnotes.clear()
        return text

class DocGenerator:
    def __init__(self, config: DocConfig):
        self.config = config
        self.modules = []
        self.all_symbols = {}
        self.symbol_patterns: dict[str, re.Pattern[str]] = {}
        
    def run(self):
        self._discover_modules()
        self._build_symbol_index()
        self._render_all()
    
    def _should_include_member(self, name: str) -> bool:
        """Return True for members we want to document (skip non-__init__ dunders)."""
        return not (name.startswith("__") and name != "__init__")

    def _register_symbol(
        self,
        alias: str,
        reference: SymbolReference,
        *,
        override: bool = False,
    ) -> None:
        """Map a symbol alias to its canonical location."""
        if override or alias not in self.all_symbols:
            self.all_symbols[alias] = reference

    def _register_class_methods(self, cls: type, module_name: str, module_page: str) -> None:
        """Gather methods defined on a class for symbol linking."""
        for method_name, method_obj in inspect.getmembers(cls):
            if not self._should_include_member(method_name):
                continue
            
            if method_name not in cls.__dict__:
                continue
            if not (
                inspect.isfunction(method_obj)
                or inspect.ismethod(method_obj)
                or inspect.isroutine(method_obj)
            ):
                continue

            anchor = f"{cls.__name__}.{method_name}"
            reference = SymbolReference(
                module_page=module_page,
                module_name=module_name,
                anchor=anchor,
            )
            self._register_symbol(anchor, reference)
            self._register_symbol(f"{module_name}.{anchor}", reference, override=True)

    def _compile_symbol_patterns(self) -> dict[str, re.Pattern[str]]:
        """Precompile regexes for symbol auto-linking."""
        patterns: dict[str, re.Pattern[str]] = {}
        for symbol in self.all_symbols:
            if "." in symbol:
                continue
            
            escaped = re.escape(symbol)
            patterns[symbol] = re.compile(
                rf"\b{escaped}\b(?![^<]*>)(?![^`]*`)",
                flags=re.MULTILINE,
            )
        return patterns

    def _discover_modules(self):
        root_path = Path(self.config.package_root)
        if not root_path.exists():
            print(f"Error: Path {root_path} does not exist.")
            return

        sys.path.insert(0, str(root_path.parent))

        for file_path in sorted(root_path.rglob("*.py")):
            if "__pycache__" in file_path.parts:
                continue

            rel_path = file_path.relative_to(root_path.parent)
            mod_name = str(rel_path.with_suffix("")).replace(os.sep, ".")
            if mod_name.endswith(".__init__"):
                mod_name = mod_name[:-9]

            try:
                importlib.import_module(mod_name)
                self.modules.append(mod_name)
            except Exception as e:
                if self.config.verbose:
                    print(f"⚠️  Skipped {mod_name}: {e}")

    def _build_symbol_index(self):
        """Build index of all classes/functions for auto-linking"""
        self.all_symbols.clear()
        for mod_name in self.modules:
            mod = sys.modules[mod_name]
            module_page = f"{mod_name}.html"
            for name, obj in inspect.getmembers(mod):
                if not self._should_include_member(name):
                    continue
                
                try:
                    if hasattr(obj, "__module__") and obj.__module__ != mod_name:
                        continue
                except Exception:
                    pass

                if inspect.isclass(obj):
                    reference = SymbolReference(module_page=module_page, module_name=mod_name, anchor=name)
                    self._register_symbol(name, reference)
                    self._register_symbol(f"{mod_name}.{name}", reference, override=True)
                    self._register_class_methods(obj, mod_name, module_page)
                elif inspect.isfunction(obj) or inspect.isroutine(obj):
                    reference = SymbolReference(module_page=module_page, module_name=mod_name, anchor=name)
                    self._register_symbol(name, reference)
                    self._register_symbol(f"{mod_name}.{name}", reference, override=True)

        self.symbol_patterns = self._compile_symbol_patterns()

    def _render_all(self):
        out_dir = Path(self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"✨ Generating docs for {len(self.modules)} modules...")
        for mod_name in self.modules:
            parser = EnhancedMarkdownParser(
                self.modules, 
                mod_name.rsplit('.', 1)[0],
                self.all_symbols,
                self.symbol_patterns,
            )
            self._render_module(mod_name, out_dir, parser)

        index_path = out_dir / "index.html"
        if self.modules:
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(f'<meta http-equiv="refresh" content="0; url={self.modules[0]}.html">')

        print(f"✓ Documentation generated in {out_dir}")

    def _render_module(self, mod_name: str, out_dir: Path, parser: EnhancedMarkdownParser):
        mod = sys.modules[mod_name]
        filename = f"{mod_name}.html"
        file_path = out_dir / filename
        content = []
        doc = inspect.getdoc(mod) or ""
        content.append(f"<h1>{mod_name}</h1>")
        if doc:
            content.append(parser.parse(doc))
        else:
            content.append("<p class='text-muted'><em>No documentation string provided.</em></p>")

        classes = []
        functions = []
        variables = []
        for name, obj in inspect.getmembers(mod):
            if not self._should_include_member(name):
                continue
            
            try:
                if hasattr(obj, "__module__") and obj.__module__ != mod_name:
                    continue
            except Exception:
                pass

            if inspect.isclass(obj):
                classes.append((name, obj))
            elif inspect.isfunction(obj) or inspect.isroutine(obj):
                functions.append((name, obj))
            elif not inspect.ismodule(obj):
                variables.append((name, obj))

        if classes:
            content.append("<h2>Classes</h2>")
            for name, cls in classes:
                content.append(self._render_class(name, cls, parser))

        if functions:
            content.append("<h2>Functions</h2>")
            for name, func in functions:
                content.append(self._render_function(name, func, parser))

        if variables:
            content.append("<h2>Variables</h2>")
            content.append(self._render_variables(variables))

        full_html = self._wrap_layout(mod_name, "\n".join(content))
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_html)

    def _render_class(self, name: str, cls: Any, parser: EnhancedMarkdownParser) -> str:
        doc = inspect.getdoc(cls) or ""
        sig_html = self._get_signature_html(cls)
        methods = []
        for n, o in inspect.getmembers(cls):
            if inspect.isfunction(o) or inspect.isroutine(o):
                if n in cls.__dict__:
                    methods.append((n, o))

        methods_html = ""
        if methods:
            methods_html = f'''
            <div class="collapsible-toggle">
                <strong>Methods ({len(methods)})</strong>
                <span class="toggle-icon">▶</span>
            </div>
            <div class="collapsible-content">
                {"".join([self._render_function(n, f, parser, is_method=True) for n, f in methods])}
            </div>
            '''

        return f"""
        <div class="api-card class-card" id="{name}">
            <div class="api-header">
                <span class="tag tag-class">class</span>
                <span class="api-name">{name}</span>
                {sig_html}
            </div>
            <div class="api-body">
                {parser.parse(doc)}
                {methods_html}
            </div>
        </div>
        """

    def _render_function(self, name: str, func: Any, parser: EnhancedMarkdownParser, is_method=False) -> str:
        sig_html = self._get_signature_html(func, is_method)
        doc = inspect.getdoc(func) or ""
        tag, tag_cls, card_cls = ("method", "tag-method", "method-card") if is_method else ("def", "tag-func", "function-card")
        
        return f"""
        <div class="api-card {card_cls}" id="{name}">
            <div class="api-header">
                <span class="tag {tag_cls}">{tag}</span>
                <span class="api-name">{name}</span>
                {sig_html}
            </div>
            <div class="api-body">
                {parser.parse(doc)}
            </div>
        </div>
        """

    def _get_signature_html(self, obj: Any, is_method: bool = False) -> str:
        """Get function signature with type hint highlighting"""
        try:
            sig = inspect.signature(obj)
            params = []
            for param_name, param in sig.parameters.items():
                if is_method and param_name == 'self':
                    continue
                
                param_str = param_name
                if param.annotation != inspect.Parameter.empty:
                    ann = str(param.annotation).replace('<class \'', '').replace('\'>', '')
                    param_str += f': <span class="type-hint">{html.escape(ann)}</span>'
                
                if param.default != inspect.Parameter.empty:
                    default = repr(param.default)
                    param_str += f' = {html.escape(default)}'
                
                params.append(param_str)
            
            return_annotation = ''
            if sig.return_annotation != inspect.Signature.empty:
                ret = str(sig.return_annotation).replace('<class \'', '').replace('\'>', '')
                return_annotation = f' → <span class="type-hint">{html.escape(ret)}</span>'
            
            params_str = ', '.join(params)
            return f'<span class="api-sig">({params_str}){return_annotation}</span>'
        except Exception:
            return '<span class="api-sig">(...)</span>'

    def _render_variables(self, variables: list) -> str:
        rows = []
        for name, value in variables:
            val_str = str(value)
            if len(val_str) > 100:
                val_str = val_str[:100] + "..."
            rows.append(f"<tr><td><code class='inline'>{name}</code></td><td><code class='inline'>{html.escape(val_str)}</code></td></tr>")
        return f"<table><thead><tr><th>Variable</th><th>Value</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"

    def _wrap_layout(self, current_mod: str, content: str) -> str:
        nav_items = []
        for mod in self.modules:
            cls = "nav-link active" if mod == current_mod else "nav-link"
            nav_items.append(f'<a href="{mod}.html" class="{cls}">{mod}</a>')
        
        parts = current_mod.split('.')
        breadcrumbs_html = []
        running_path = ""
        
        for i, part in enumerate(parts):
            running_path = running_path + "." + part if i > 0 else part
            
            if running_path in self.modules:
                tooltip = f'data-tooltip="{running_path}"'
                breadcrumbs_html.append(f'<a href="{running_path}.html" class="crumb-link" {tooltip}>{part}</a>')
            else:
                if i == len(parts) - 1:
                    breadcrumbs_html.append(f'<span class="crumb-active">{part}</span>')
                else:
                    breadcrumbs_html.append(f'<span>{part}</span>')

            if i < len(parts) - 1:
                breadcrumbs_html.append('<span class="crumb-separator">/</span>')
                
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{current_mod} - {self.config.project_title}</title>
    <style>{CSS_STYLES}</style>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
    <div class="layout">
        <aside class="sidebar">
            <div class="sidebar-header">
                <span class="brand">📚 {self.config.project_title}</span>
                <div class="search-wrapper">
                    <input type="text" id="search-input" class="search-input" placeholder="Search modules...">
                </div>
            </div>
            <nav class="nav-scroller">
                <div class="nav-group">
                    <div class="nav-header">Modules</div>
                    {"".join(nav_items)}
                </div>
            </nav>
        </aside>
        
        <main class="main">
            <div class="topbar">
                <div class="breadcrumbs">
                    {''.join(breadcrumbs_html)}
                </div>
                <button onclick="history.back()" class="back-btn">
                    <span>←</span> Back
                </button>
            </div>
            <div class="content-scroll" id="content">
                <div class="container">
                    {content}
                </div>
            </div>
        </main>
    </div>
    {JS_SCRIPT}
</body>
</html>
"""

def main():
    config = DocConfig(
        package_root="src/ornata",
        package_name="ornata",
        output_dir="docs/html",
        project_title="Ornata Documentation"
    )
    generator = DocGenerator(config)
    generator.run()

if __name__ == "__main__":
    main()