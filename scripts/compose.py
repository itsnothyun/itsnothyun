# Builds assets/profile.svg: one window that holds the banner, whoami, the project
# cards and pulse of the day. Each part is rendered on its own, stripped of its frame,
# and inlined as a nested <svg>. Inlined, not embedded as <image>: images nested in an
# SVG that GitHub shows through <img> freeze on their first frame. Every part's ids,
# classes and keyframes get a prefix, and its CSS is scoped to its own <svg>.
import html, itertools, os, re, tempfile

import gen
import term

W = 1200
BG, BAR, ON, MID, DIM, OFF, LINE = term.BG, term.BAR, term.ON, term.MID, term.DIM, term.OFF, term.LINE
FONT = term.FONT
TOP = 40          # title bar
LABEL = 44        # section label strip

CARDS = [
    ('PULSE', "your machine's vitals, in pixels", 'macos · windows · linux'),
    ('EXPLORER', 'open and convert any file, on-device', 'react · tauri v2 · web + desktop'),
    ('SYNC', 'every server, on one screen', 'web app · invite only'),
    ('TRACK', 'who shipped what, today', 'web app · private'),
    ('CONNECT', 'your network, by device', 'desktop · private'),
    ('STASH', 'floating notes, stashed locally', 'tauri 2 · rust · sqlite fts5'),
]


def unframe(svg):
    # the panel draws the only frame; drop each part's own hairline border
    return re.sub(r'<rect x="\.5" y="\.5"[^>]*stroke="#303030"/>', '', svg)


def size(svg):
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    return float(m.group(1)), float(m.group(2))


_ids = itertools.count()


def scope_css(css, p):
    # rename classes and keyframes, and scope plain selectors (text, *) to this part
    css = re.sub(r'\.([A-Za-z][\w-]*)', lambda m: f'.{p}-{m.group(1)}', css)
    css = re.sub(r'@keyframes\s+([\w-]+)', lambda m: f'@keyframes {p}-{m.group(1)}', css)
    css = re.sub(r'animation:\s*(?!none)([A-Za-z][\w-]*)', lambda m: f'animation:{p}-{m.group(1)}', css)
    out, depth, stack, i, sel = [], 0, [], 0, ''
    for ch in css:
        if ch == '{':
            head = sel.strip()
            in_kf = any(k.startswith('@keyframes') for k in stack)
            if not head.startswith('@') and not in_kf:
                head = ','.join(f'.{p} {h.strip()}' for h in head.split(','))
            out.append(head + '{'); stack.append(sel.strip()); sel = ''
        elif ch == '}':
            out.append(sel + '}'); sel = ''
            if stack: stack.pop()
        elif ch == ';' and stack and not stack[-1].startswith('@'):
            out.append(sel + ';'); sel = ''
        else:
            sel += ch
    return ''.join(out) + sel


def embed(svg, x, y, w=None):
    p = f'p{next(_ids)}'
    vw, vh = size(svg)
    w = w or vw
    h = vh * w / vw
    svg = unframe(svg)
    inner = svg[svg.index('>', svg.index('<svg')) + 1: svg.rindex('</svg>')]
    css = ''.join(re.findall(r'<style>(.*?)</style>', inner, re.S))
    inner = re.sub(r'<style>.*?</style>', '', inner, flags=re.S)
    inner = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{p}-{m.group(1)}"', inner)
    inner = re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{p}-{m.group(1)})', inner)
    inner = re.sub(r'class="([^"]+)"', lambda m: 'class="' + ' '.join(f'{p}-{c}' for c in m.group(1).split()) + '"', inner)
    inner = re.sub(r'animation:\s*(?!none)([A-Za-z][\w-]*)', lambda m: f'animation:{p}-{m.group(1)}', inner)
    return (f'<svg class="{p}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" viewBox="0 0 {vw:g} {vh:g}">'
            f'<style>{scope_css(css, p)}</style>{inner}</svg>'), h


def label(y, text, right=''):
    out = [f'<line x1="0" y1="{y + .5:.1f}" x2="{W}" y2="{y + .5:.1f}" stroke="{LINE}"/>',
           f'<text x="28" y="{y + 27:.1f}" fill="{DIM}" style="font-size:12px;letter-spacing:2px">'
           f'<tspan fill="{OFF}">── </tspan>{html.escape(text)}</text>']
    if right:
        out.append(f'<text x="{W - 28}" y="{y + 27:.1f}" text-anchor="end" fill="{OFF}" style="font-size:12px;letter-spacing:1px">{html.escape(right)}</text>')
    return out


def build(path, now, recent, releases, phase):
    tmp = tempfile.mkdtemp()
    p = lambda n: os.path.join(tmp, n)
    gen.PHASE = phase * 0.37
    gen.banner(p('header.svg'), 'HYUN', [('quiet, local-first tools for your desktop, servers and team', MID, 17),
                                         ('rust · swift · c# · typescript · react · tauri', DIM, 13)], pad_top=2)
    for word, sub, meta in CARDS:
        gen.card(p(f'card-{word}.svg'), word, sub, meta)
    term.whoami(p('whoami.svg'), bare=True)
    term.render(p('today.svg'), now, recent, releases, phase, bare=True)
    read = lambda n: open(p(n), encoding='utf8').read()

    body, y = [], TOP
    img, h = embed(read('header.svg'), 0, y); body.append(img); y += h

    body += label(y, 'WHOAMI'); y += LABEL
    img, h = embed(read('whoami.svg'), 0, y); body.append(img); y += h

    body += label(y, 'THE PULSE ECOSYSTEM', 'five tools · one quiet look'); y += LABEL
    half = W / 2
    for i in range(0, len(CARDS), 2):
        row_h = 0
        for j, (word, _, _) in enumerate(CARDS[i:i + 2]):
            img, h = embed(read(f'card-{word}.svg'), j * half, y, half); body.append(img); row_h = max(row_h, h)
        if i:  # hairline between card rows
            body.append(f'<line x1="28" y1="{y + .5:.1f}" x2="{W - 28}" y2="{y + .5:.1f}" stroke="#1c1c1c"/>')
        body.append(f'<line x1="{half + .5}" y1="{y + 14:.1f}" x2="{half + .5}" y2="{y + row_h - 14:.1f}" stroke="#1c1c1c"/>')
        y += row_h

    body += label(y, 'PULSE OF THE DAY', f'{now:%Y-%m-%d}'); y += LABEL
    img, h = embed(read('today.svg'), 0, y); body.append(img); y += h + 8

    H = y
    title = 'hyun — ~/itsnothyun — 120×80'
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:.0f}" width="{W}" height="{H:.0f}" role="img" '
           f'aria-label="Hyun: software engineer building the pulse ecosystem — whoami, projects and pulse of the day">',
           f'<style>text{{font-family:{FONT};white-space:pre}}'
           '.live{animation:live 2.4s ease-in-out infinite}@keyframes live{0%,100%{opacity:1}50%{opacity:.2}}'
           '@media (prefers-reduced-motion:reduce){*{animation:none!important}}</style>',
           f'<clipPath id="win"><rect width="{W}" height="{H:.0f}" rx="14"/></clipPath>',
           f'<g clip-path="url(#win)"><rect width="{W}" height="{H:.0f}" fill="{BG}"/>',
           f'<rect width="{W}" height="{TOP}" fill="{BAR}"/><line x1="0" y1="{TOP - .5}" x2="{W}" y2="{TOP - .5}" stroke="{LINE}"/>',
           *[f'<circle cx="{24 + i * 20}" cy="{TOP / 2}" r="6" fill="none" stroke="{OFF}" stroke-width="1.5"/>' for i in range(3)],
           f'<text x="{W / 2}" y="{TOP / 2 + 4}" text-anchor="middle" fill="{DIM}" style="font-size:12px;letter-spacing:1px">{html.escape(title)}</text>',
           f'<circle class="live" cx="{W - 104}" cy="{TOP / 2}" r="3.5" fill="{ON}"/>',
           f'<text x="{W - 28}" y="{TOP / 2 + 4}" text-anchor="end" fill="{DIM}" style="font-size:12px;letter-spacing:2px">ONLINE</text>',
           *body, '</g>',
           f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1:.0f}" rx="13.5" fill="none" stroke="{LINE}"/></svg>']
    open(path, 'w', encoding='utf8').write('\n'.join(svg))
