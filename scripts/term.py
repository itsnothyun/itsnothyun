# Looping terminal windows for the profile: the command types, the output prints
# line by line, holds, then the screen clears and it runs again.
import html

BG, BAR, ON, MID, DIM, OFF, LINE = '#090909', '#111111', '#f2f2ed', '#b3b3ad', '#8c8c88', '#3a3a3a', '#303030'
FONT = "ui-monospace,'SF Mono','Cascadia Mono',Menlo,Consolas,monospace"
CW, LH, FS = 8.4, 22, 14   # cell width, line height, font size (14px mono ≈ 8.4px per char)
LOOP = 14.0                # seconds per run


def meter(n, top, width=12):
    filled = 0 if not n else max(1, round(width * n / max(top, 1)))
    return '#' * filled, '.' * (width - filled)


def render(path, now, recent, releases, phase):
    """recent: [(name, pushed_date, commits_this_week)], releases: [(name, tag, date)]"""
    rows = []   # each row: list of (col, text, color)

    def row(*cells): rows.append(list(cells))

    row((0, '', DIM))
    row((0, 'PULSE OF THE DAY', ON), (17, '·', OFF), (19, f'{now:%a %d %b %Y}'.lower(), MID), (35, '·', OFF), (37, f'{now:%H:%M} utc', DIM))
    row((0, '', DIM))
    row((0, 'RECENT', DIM), (20, 'THIS WEEK', DIM), (48, 'LAST PUSH', DIM))
    top = max([c for _, _, c in recent] + [1])
    for name, pushed, n in recent:
        on, off = meter(n, top)
        row((0, name, ON), (20, '[', OFF), (21, on, ON), (21 + len(on), off, OFF), (33, ']', OFF),
            (35, f'{n} commit{"s" * (n != 1)}' if n else 'quiet', MID if n else DIM), (48, pushed, DIM))
    row((0, '', DIM))
    row((0, 'RELEASES', DIM))
    for i, (name, tag, date) in enumerate(releases):
        row((0, name, ON), (20, tag, MID), (35, date, DIM), *([(48, '● latest', MID)] if i == 0 else []))
    row((0, '', DIM))
    row((0, f'field phase {phase:03d}', DIM), (16, '·', OFF), (18, 'next beat in 24h', DIM))
    window(path, 'pulse --today', rows, 'pulse of the day: recent activity and releases')


def whoami(path):
    rows = []

    def row(*cells): rows.append(list(cells))

    row((0, '', DIM))
    row((0, 'HYUN', ON), (6, '·', OFF), (8, 'itsnothyun', MID), (56, '●', ON), (58, 'online', DIM))
    row((0, '', DIM))
    for key, val in [('role', 'software engineer'),
                     ('builds', 'the pulse ecosystem · small, quiet, monochrome tools'),
                     ('stack', 'rust · swift · c# · python · typescript · react · tauri'),
                     ('rule', 'local-first. no telemetry. it should idle at a few percent cpu.')]:
        row((0, key, DIM), (10, val, ON if key == 'role' else MID))
    window(path, 'whoami', rows, 'hyun: software engineer building the pulse ecosystem', loop=11.0)


def window(path, cmd, rows, label, loop=LOOP):
    W, PAD, TOP = 1200, 28, 40
    LOOP = loop
    prompt = 'hyun@pulse:~$ '
    H = TOP + 26 + (len(rows) + 2) * LH + 18
    t_type, t_print, t_hold = 0.06, 0.12, 0.70   # fractions of LOOP

    def kf(name, on_at, off_at=0.94):
        a, b = round(on_at * 100, 2), round(off_at * 100, 2)
        return f'@keyframes {name}{{0%,{max(a-0.01,0)}%{{opacity:0}}{a}%,{b}%{{opacity:1}}{min(b+0.01,100)}%,100%{{opacity:0}}}}'

    css = [f'text{{font-family:{FONT};font-size:{FS}px;white-space:pre}}',
           '.cur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}',
           '@media (prefers-reduced-motion:reduce){*{animation:none!important;opacity:1!important}}']
    body = []
    y0 = TOP + 26 + LH * 0.75

    # prompt + typed command
    body.append(f'<text x="{PAD}" y="{y0:.1f}" fill="{DIM}">{html.escape(prompt)}</text>')
    cx = PAD + len(prompt) * CW
    for i, ch in enumerate(cmd):
        at = 0.02 + t_type * i / len(cmd)
        css.append(kf(f'c{i}', at))
        body.append(f'<text x="{cx + i*CW:.1f}" y="{y0:.1f}" fill="{ON}" style="animation:c{i} {LOOP}s linear infinite">{html.escape(ch)}</text>')

    # output rows print one after another
    for r, cells in enumerate(rows):
        at = 0.02 + t_type + 0.02 + t_print * r / len(rows)
        css.append(kf(f'r{r}', at))
        y = y0 + (r + 1) * LH
        parts = ''.join(f'<tspan x="{PAD + 16 + c*CW:.1f}" fill="{col}">{html.escape(t)}</tspan>' for c, t, col in cells if t)
        if parts:
            body.append(f'<text y="{y:.1f}" style="animation:r{r} {LOOP}s linear infinite">{parts}</text>')

    # final prompt with a blinking block cursor
    at = 0.02 + t_type + 0.02 + t_print + 0.01
    css.append(kf('end', at))
    ye = y0 + (len(rows) + 1) * LH
    body.append(f'<g style="animation:end {LOOP}s linear infinite"><text x="{PAD}" y="{ye:.1f}" fill="{DIM}">{html.escape(prompt)}</text>'
                f'<rect class="cur" x="{PAD + len(prompt)*CW:.1f}" y="{ye - FS + 2:.1f}" width="{CW:.1f}" height="{FS + 2}" fill="{ON}"/></g>')
    # cursor that rides the command line while it types
    css.append('@keyframes typecur{0%{opacity:1}' + f'{round((0.02+t_type)*100+1,2)}%,100%{{opacity:0}}}}')
    css.append(f'@keyframes typemove{{0%,2%{{transform:translateX(0)}}{round((0.02+t_type)*100,2)}%,100%{{transform:translateX({len(cmd)*CW:.1f}px)}}}}')
    body.append(f'<g style="animation:typecur {LOOP}s linear infinite"><rect x="{cx:.1f}" y="{y0 - FS + 2:.1f}" width="{CW:.1f}" height="{FS + 2}" fill="{ON}" '
                f'style="animation:typemove {LOOP}s steps({len(cmd)}) infinite"/></g>')

    title = f'hyun — {cmd} — 120×24'
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:.0f}" width="{W}" height="{H:.0f}" role="img" aria-label="{html.escape(label)}">',
           '<style>' + ''.join(css) + '</style>',
           f'<clipPath id="win"><rect width="{W}" height="{H:.0f}" rx="14"/></clipPath>',
           f'<g clip-path="url(#win)"><rect width="{W}" height="{H:.0f}" fill="{BG}"/>',
           f'<rect width="{W}" height="{TOP}" fill="{BAR}"/><line x1="0" y1="{TOP}.5" x2="{W}" y2="{TOP}.5" stroke="{LINE}"/>',
           *[f'<circle cx="{24 + i*20}" cy="{TOP/2}" r="6" fill="none" stroke="{OFF}" stroke-width="1.5"/>' for i in range(3)],
           f'<text x="{W/2}" y="{TOP/2 + 4}" text-anchor="middle" fill="{DIM}" style="font-size:12px;letter-spacing:1px">{html.escape(title)}</text>',
           *body, '</g>',
           f'<rect x=".5" y=".5" width="{W-1}" height="{H-1:.0f}" rx="13.5" fill="none" stroke="{LINE}"/></svg>']
    open(path, 'w', encoding='utf8').write('\n'.join(svg))


if __name__ == '__main__':
    import os
    whoami(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'whoami.svg'))
