# Daily beat: shifts the header's ASCII field to today's phase and rewrites the
# activity block in README.md from public GitHub data. Run by .github/workflows/daily.yml.
import datetime as dt, json, os, re, subprocess, sys, urllib.request

USER = 'itsnothyun'
RELEASE_REPOS = ['Pulse', 'Pulse-Explorer', 'Stash']
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOKEN = os.environ.get('GITHUB_TOKEN', '')


def api(path):
    req = urllib.request.Request(f'https://api.github.com{path}', headers={'Accept': 'application/vnd.github+json'})
    if TOKEN:
        req.add_header('Authorization', f'Bearer {TOKEN}')
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except Exception as e:
        print(f'skip {path}: {e}', file=sys.stderr)
        return None


def rule(title, width=62):
    return f' {title} ' + '─' * (width - len(title) - 2)


now = dt.datetime.now(dt.timezone.utc)
day = now.timetuple().tm_yday

repos = api(f'/users/{USER}/repos?sort=pushed&per_page=30') or []
repos = [r for r in repos if not r['fork'] and not r['private'] and r['name'] != USER][:5]

events = api(f'/users/{USER}/events/public?per_page=100') or []
week_ago = now - dt.timedelta(days=7)
pushes = {}
for e in events:
    if e['type'] != 'PushEvent' or dt.datetime.fromisoformat(e['created_at'].replace('Z', '+00:00')) < week_ago:
        continue
    name = e['repo']['name'].split('/')[-1]
    pushes[name] = pushes.get(name, 0) + max(1, len(e['payload'].get('commits') or []))

lines = ['```text', rule('RECENT')]
for r in repos:
    pushed = r['pushed_at'][:10]
    n = pushes.get(r['name'])
    note = f'{n} commit{"s" * (n != 1)} this week' if n else 'quiet this week'
    lines.append(f'  {pushed}  {r["name"]:<16} {note}')

lines += ['', rule('RELEASES')]
for name in RELEASE_REPOS:
    rel = api(f'/repos/{USER}/{name}/releases/latest')
    if rel and rel.get('tag_name'):
        lines.append(f'  {name:<16} {rel["tag_name"]:<9} {rel["published_at"][:10]}')

lines += ['', f'  last beat  {now:%Y-%m-%d %H:%M} UTC  ·  field phase {day:03d}', '```']
block = '\n'.join(lines)

readme_path = os.path.join(ROOT, 'README.md')
readme = open(readme_path, encoding='utf8').read()
readme = re.sub(r'<!-- pulse:start -->.*?<!-- pulse:end -->',
                f'<!-- pulse:start -->\n{block}\n<!-- pulse:end -->', readme, flags=re.S)
open(readme_path, 'w', encoding='utf8', newline='\n').write(readme)

env = dict(os.environ, PULSE_PHASE=str(day * 0.37), PULSE_OUT=os.path.join(ROOT, 'assets'))
subprocess.run([sys.executable, os.path.join(HERE, 'gen.py'), 'profile'], env=env, check=True)
sys.stdout.reconfigure(encoding="utf-8")
print(block)
