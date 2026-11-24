# Social icons as ASCII pixel art: each lit pixel is a pair of '@', the tile carries a
# faint ramp field, a slow glow and a scanner sweep. Staggered so the row pulses in turn.
import html, os

BG, ON, LINE = '#090909', '#f2f2ed', '#303030'
FONT = "ui-monospace,'SF Mono','Cascadia Mono',Menlo,Consolas,monospace"
RAMP = ' .:-=+*#%@'

ICONS = {
    'gmail': [
        '.............',
        '#############',
        '##.........##',
        '#.#.......#.#',
        '#..#.....#..#',
        '#...#...#...#',
        '#....#.#....#',
        '#.....#.....#',
        '#...........#',
        '#...........#',
        '#############',
        '.............',
    ],
    'instagram': [
        '.###########.',
        '#...........#',
        '#.........#.#',
        '#...........#',
        '#....###....#',
        '#...#...#...#',
        '#...#...#...#',
        '#...#...#...#',
        '#....###....#',
        '#...........#',
        '#...........#',
        '.###########.',
    ],
    'threads': [
        '...#######...',
        '.##.......##.',
        '#...........#',
        '#....####...#',
        '#...#....#..#',
        '#...#....#..#',
        '#...#....#..#',
        '#....#####.#.',
        '#.........#..',
        '#............',
        '.##.......#..',
        '...#######...',
    ],
}


def tile(path, rows, delay=0.0, S=96, CH=6):
    CW = CH  # two half-width glyphs per pixel keep pixels square
    gw, gh = len(rows[0]), len(rows)
    ox, oy = (S - gw * CW) / 2, (S - gh * CH) / 2
    fs = CH * 0.95
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="{S}" height="{S}">',
           '<style>',
           f'text{{font-family:{FONT};font-size:{fs:.1f}px;white-space:pre}}',
           f'.g{{animation:glow 4.5s ease-in-out {delay:.2f}s infinite}}',
           '@keyframes glow{0%,100%{opacity:.78}45%,55%{opacity:1}}',
           f'.s{{animation:scan 4.5s linear {delay:.2f}s infinite}}',
           f'@keyframes scan{{0%{{transform:translateY(-30px)}}60%,100%{{transform:translateY({S + 30}px)}}}}',
           '@media (prefers-reduced-motion:reduce){*{animation:none!important}.g{opacity:1}}',
           '</style>',
           '<defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
           '<stop offset=".5" stop-color="#fff" stop-opacity=".09"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>',
           f'<clipPath id="t"><rect width="{S}" height="{S}" rx="18"/></clipPath></defs>',
           f'<g clip-path="url(#t)"><rect width="{S}" height="{S}" fill="{BG}"/>']
    # faint field in the margins
    n = int(S // CH)
    for y in range(n):
        line = ''.join(RAMP[1 + (x * 3 + y * 5) % 3] if (x + y) % 3 == 0 else ' ' for x in range(n * 2))
        out.append(f'<text x="0" y="{y * CH + CH * 0.85:.1f}" fill="#262626" textLength="{n * CH:.1f}" lengthAdjust="spacingAndGlyphs">{html.escape(line)}</text>')
    out.append(f'<rect x="{ox - 4:.1f}" y="{oy - 4:.1f}" width="{gw * CW + 8:.1f}" height="{gh * CH + 8:.1f}" fill="{BG}"/>')
    out.append(f'<g class="g" fill="{ON}">')
    for y, r in enumerate(rows):
        line = ''.join('@@' if c == '#' else '  ' for c in r).rstrip()
        if line:
            out.append(f'<text x="{ox:.1f}" y="{oy + y * CH + CH * 0.85:.1f}" textLength="{len(line) * CW / 2:.1f}" lengthAdjust="spacingAndGlyphs">{html.escape(line)}</text>')
    out.append('</g>')
    out.append(f'<rect class="s" width="{S}" height="30" fill="url(#sg)"/></g>')
    out.append(f'<rect x=".5" y=".5" width="{S - 1}" height="{S - 1}" rx="17.5" fill="none" stroke="{LINE}"/></svg>')
    open(path, 'w', encoding='utf8').write('\n'.join(out))


if __name__ == '__main__':
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets')
    for i, (name, rows) in enumerate(ICONS.items()):
        tile(os.path.join(out, f'social-{name}.svg'), rows, delay=i * 0.6)
