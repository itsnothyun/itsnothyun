# Daily beat: shifts the header's ASCII field to today's phase and rewrites the
# activity block in README.md from public GitHub data. Run by .github/workflows/daily.yml.
import datetime as dt, json, os, re, sys, urllib.request

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

recent = [(r['name'], r['pushed_at'][:10], pushes.get(r['name'], 0)) for r in repos]
releases = []
for name in RELEASE_REPOS:
    rel = api(f'/repos/{USER}/{name}/releases/latest')
    if rel and rel.get('tag_name'):
        releases.append((name, rel['tag_name'], rel['published_at'][:10]))
releases.sort(key=lambda r: r[2], reverse=True)

sys.path.insert(0, HERE)
import compose
compose.build(os.path.join(ROOT, 'assets', 'profile.svg'), now, recent, releases, day)

summary = '; '.join(f'{n} {c} commit{"s" * (c != 1)} this week' for n, _, c in recent if c) or 'a quiet week'
block = ('<p align="center">\n  <img src="assets/profile.svg" width="100%" '
         'alt="Hyun, software engineer building the pulse ecosystem: Pulse, Explorer, Sync, Track, Connect and Stash. '
         f'Pulse of the day, {now:%Y-%m-%d}: {summary}" />\n</p>')

readme_path = os.path.join(ROOT, 'README.md')
readme = open(readme_path, encoding='utf8').read()
readme = re.sub(r'<!-- pulse:start -->.*?<!-- pulse:end -->',
                f'<!-- pulse:start -->\n{block}\n<!-- pulse:end -->', readme, flags=re.S)
open(readme_path, 'w', encoding='utf8', newline='\n').write(readme)

print(block)
