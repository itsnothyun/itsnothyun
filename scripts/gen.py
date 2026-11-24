import json, math, re, sys, html
import os
HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(HERE, 'glyphs.json'), encoding='utf8'))
PHASE = float(os.environ.get('PULSE_PHASE', '0'))  # shifts the ASCII field; the daily job sets it from the date
RAMP = ' .:-=+*#%@'
BG, ON, MID, DIM, OFF = '#090909', '#f2f2ed', '#b3b3ad', '#8c8c88', '#262626'
ON_HI = '#ffffff'
FONT = "ui-monospace,'SF Mono','Cascadia Mono',Menlo,Consolas,monospace"

def grey(l):
    v = round(58 + (242-58)*l); return f'rgb({v},{v},{v-4})'

def bitmap(text):
    rows = 7; cols = []
    for i, ch in enumerate(text):
        g = G.get(ch, G[' '])[:7]
        for b in range(4, -1, -1):
            cols.append([(r >> b) & 1 for r in g])
        if i < len(text)-1: cols.append([0]*7)
    return [[cols[x][y] for x in range(len(cols))] for y in range(rows)]

def banner(path, word, lines, W=1200, CH=14, s=2, tag='', badge='', pad_top=None, pad_bot=None, type_first=True):
    CW = CH/2
    bm = bitmap(word); pw = len(bm[0])
    cols = int(W//CW)
    pad_top = (4 if tag else 2) if pad_top is None else pad_top
    pad_bot = 2 if pad_bot is None else pad_bot
    oy = pad_top; ox = (cols - pw*2*s)//2
    text_h = sum(sz + 12 for _, _, sz in lines)
    H = int((oy + 7*s + 1)*CH + text_h + pad_bot*CH)
    rows = int(H//CH) + 1
    fs = round(CH*0.86*0.98, 2)
    lit = set()
    for y in range(7):
        for x in range(pw):
            if bm[y][x]:
                for dy in range(s):
                    for dx in range(2*s): lit.add((ox+x*2*s+dx, oy+y*s+dy))
    clear = lambda x, y: ox-2 <= x < ox+pw*2*s+2 and oy-1 <= y < oy+7*s+1
    text_top = (oy+7*s+1)*CH
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{html.escape(word)}">',
           '<style>',
           f'text{{font-family:{FONT};font-size:{fs}px;white-space:pre}}',
           '.f{animation:drift 10s ease-in-out infinite alternate}',
           '.f0,.f1,.f2{opacity:0;animation:fade 7.5s linear infinite}.f1{animation-delay:-2.5s}.f2{animation-delay:-5s}',
           '@keyframes fade{0%,100%{opacity:0}16%,34%{opacity:1}50%{opacity:0}}',
           '.cur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}',
           f'@keyframes drift{{from{{transform:translateX(0)}}to{{transform:translateX(-{CW*3}px)}}}}',
           '.w{animation:glow 4.8s ease-in-out infinite}',
           '@keyframes glow{0%,100%{opacity:1}50%{opacity:.8}}',
           '.scan{animation:scan 7s linear infinite}',
           f'@keyframes scan{{from{{transform:translateY(-60px)}}to{{transform:translateY({H+60}px)}}}}',
           '.live{animation:live 2.4s ease-in-out infinite}',
           '@keyframes live{0%,100%{opacity:1}50%{opacity:.2}}',
           '@media (prefers-reduced-motion:reduce){*{animation:none!important}.f0{opacity:1}}',
           '</style>',
           f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>',
           '<defs><radialGradient id="m" cx="50%" cy="45%" r="60%"><stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>',
           f'<mask id="k"><rect width="{W}" height="{H}" fill="url(#m)"/></mask>',
           '<linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".045"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>',
           f'<clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>',
           '<g clip-path="url(#c)">', '<g mask="url(#k)"><g class="f">']
    fcols = cols + 6
    for p in range(3):
        out.append(f'<g class="f{p}">')
        for y in range(rows):
            if y*CH + CH > text_top - 4: break
            by_lvl = {}
            for x in range(fcols):
                if clear(x, y): continue
                wave = 0.5 + 0.5*math.sin(x*0.07 + p*2.094 + PHASE + math.sin(y*0.12 + p*0.7)*1.9 + 1.3)
                lvl = min(9, round(wave**3*0.55*9))
                if lvl: by_lvl.setdefault(lvl, []).append(x)
            for lvl, xs in by_lvl.items():
                row = [' ']*fcols
                for x in xs: row[x] = RAMP[lvl]
                line = ''.join(row).rstrip()
                out.append(f'<text x="0" y="{y*CH+CH*0.8:.1f}" fill="{grey(lvl/9*0.5)}" textLength="{len(line)*CW:.1f}" lengthAdjust="spacingAndGlyphs">{html.escape(line)}</text>')
        out.append('</g>')
    out.append('</g></g>')
    wm = []
    for y in range(oy, oy+7*s):
        row = [' ']*cols
        for x in range(ox, ox+pw*2*s):
            if (x, y) in lit: row[x] = '@'
        line = ''.join(row).rstrip()
        wm.append(f'<text x="0" y="{y*CH+CH*0.8:.1f}" textLength="{len(line)*CW:.1f}" lengthAdjust="spacingAndGlyphs">{html.escape(line)}</text>')
    x0, x1 = ox*CW, (ox+pw*2*s)*CW; band = max(60, (x1-x0)*0.16)
    out.append(f'<clipPath id="sc"><rect y="0" width="{band:.0f}" height="{H}" x="{x0-band:.0f}"><animate attributeName="x" values="{x0-band:.0f};{x1:.0f};{x1:.0f}" keyTimes="0;0.6;1" dur="5s" repeatCount="indefinite"/></rect></clipPath>')
    out.append(f'<g class="w" fill="{MID}">' + ''.join(wm) + '</g>')
    out.append(f'<g fill="{ON_HI}" clip-path="url(#sc)">' + ''.join(wm) + '</g>')
    ty = text_top + 4
    for i, (txt, col, size) in enumerate(lines):
        ty += size
        if i == 0 and type_first:
            cw = size*0.6; tw = len(txt)*cw; tx = W/2 - tw/2
            vals = f"0;{tw:.0f};{tw:.0f};0;0"; kt = "0;0.35;0.85;0.95;1"
            out.append(f'<clipPath id="ty"><rect x="{tx:.0f}" y="{ty-size-4}" height="{size+10}" width="0"><animate attributeName="width" values="{vals}" keyTimes="{kt}" dur="9s" calcMode="linear" repeatCount="indefinite"/></rect></clipPath>')
            out.append(f'<text x="{tx:.0f}" y="{ty}" fill="{col}" clip-path="url(#ty)" textLength="{tw:.0f}" style="font-size:{size}px">{html.escape(txt)}</text>')
            out.append(f'<rect class="cur" y="{ty-size+2}" width="{cw*0.9:.1f}" height="{size+1}" fill="{ON}" x="{tx:.0f}"><animate attributeName="x" values="{";".join(f"{tx+float(v):.0f}" for v in vals.split(";"))}" keyTimes="{kt}" dur="9s" calcMode="linear" repeatCount="indefinite"/></rect>')
        else:
            out.append(f'<text x="{W/2}" y="{ty}" text-anchor="middle" fill="{col}" style="font-size:{size}px">{html.escape(txt)}</text>')
        ty += 12
    if tag:
        out.append(f'<text x="28" y="34" fill="{DIM}" style="font-size:12px;letter-spacing:2px">{html.escape(tag)}</text>')
    if badge:
        bx = W - 28 - len(badge)*9.4 - 12
        out.append(f'<circle class="live" cx="{bx:.1f}" cy="29.5" r="3.5" fill="{ON}"/>')
        out.append(f'<text x="{W-28}" y="34" text-anchor="end" fill="{DIM}" style="font-size:12px;letter-spacing:2px">{html.escape(badge)}</text>')
    out.append(f'<rect class="scan" x="0" y="0" width="{W}" height="60" fill="url(#s)"/>')
    out.append('</g>')
    out.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="13.5" fill="none" stroke="#303030"/></svg>')
    open(path, 'w', encoding='utf8').write('\n'.join(out))

def card(path, word, sub, meta):
    banner(path, word, [(sub, MID, 15), (meta, DIM, 12)], W=600, CH=9, s=1, pad_top=3, pad_bot=2, type_first=False)

def heartbeat(path, W=1200, H=100):
    mid = 56; pts = []; x = 0
    beat = [(0,0),(14,-6),(22,0),(32,0),(38,10),(46,-44),(54,26),(60,0),(76,0),(88,-12),(102,0)]
    while x < W:
        for bx, by in beat: pts.append((x+bx, mid+by))
        x += 300
    d = 'M0,%d ' % mid + ' '.join(f'L{px},{py}' for px, py in pts if px <= W) + f' L{W},{mid}'
    import math as _m
    P = [(0, mid)] + [p for p in pts if p[0] <= W] + [(W, mid)]
    L = int(sum(_m.dist(a, b) for a, b in zip(P, P[1:]))) + 420
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="heartbeat">',
           '<style>',
           f'text{{font-family:{FONT};white-space:pre}}',
           f'.trace{{stroke-dasharray:420 {L};animation:run 4s linear infinite}}',
           f'@keyframes run{{from{{stroke-dashoffset:420}}to{{stroke-dashoffset:-{L-420}}}}}',
           '.live{animation:live 2.4s ease-in-out infinite}@keyframes live{0%,100%{opacity:1}50%{opacity:.2}}',
           '@media (prefers-reduced-motion:reduce){*{animation:none!important}.trace{stroke-dasharray:none}}',
           '</style>',
           '<defs><linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".08" stop-color="#fff"/><stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>',
           f'<mask id="mk"><rect width="{W}" height="{H}" fill="url(#fadeL)"/></mask></defs>',
           f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="13.5" fill="none" stroke="#303030"/>',
           f'<g mask="url(#mk)"><path d="{d}" fill="none" stroke="#2e2e2e" stroke-width="2" stroke-linejoin="round"/>',
           f'<path class="trace" d="{d}" fill="none" stroke="{ON}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/></g>',
           '</svg>']
    open(path, 'w', encoding='utf8').write('\n'.join(out))

OUT = os.environ.get('PULSE_OUT', '.')
which = sys.argv[1] if len(sys.argv) > 1 else 'profile'
if which == 'profile':
    banner(os.path.join(OUT, 'header.svg'), 'HYUN', [('quiet, local-first tools for your desktop, servers and team', MID, 17),
                                 ('rust · swift · c# · typescript · react · tauri', DIM, 13)],
           tag='~/itsnothyun', badge='ONLINE')
    for slug, word, sub, meta in [
        ('pulse', 'PULSE', "your machine's vitals, in pixels", 'macos · windows · linux'),
        ('explorer', 'EXPLORER', 'open and convert any file, on-device', 'react · tauri v2 · web + desktop'),
        ('stash', 'STASH', 'floating notes, stashed locally', 'tauri 2 · rust · sqlite fts5'),
        ('sync', 'SYNC', 'every server, on one screen', 'web app · invite only'),
        ('track', 'TRACK', 'who shipped what, today', 'web app · private'),
        ('connect', 'CONNECT', 'your network, by device', 'desktop · private'),
    ]:
        card(os.path.join(OUT, f'card-{slug}.svg'), word, sub, meta)
    heartbeat(os.path.join(OUT, 'heartbeat.svg'))
elif which == 'stash':
    banner('stash-banner.svg', 'STASH', [('Capture it. Stash it. Find it instantly.', MID, 17),
                                        ('local-first floating notes for macos and windows', DIM, 13)],
           CH=11, tag='STASH / DESKTOP', badge='v0.1.3')
