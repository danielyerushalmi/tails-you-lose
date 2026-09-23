"""Build the single-file Vercel deployment: site/index.html with its local assets pointed at jsDelivr's
mirror of this repo, pinned to one commit.

Why: the Vercel project is not connected to GitHub yet, so the deployment is created by uploading files
through the API. Uploading only index.html (and serving scripts, styles, data and images from the pinned
commit) keeps the upload small and makes every deployed byte traceable to a commit.
Once Vercel's GitHub integration is connected, deploy the site/ folder directly instead.

Usage: python tools/vercel_index.py <commit-sha>  ->  writes deploy/index.html
"""
import hashlib, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sha = sys.argv[1]
CDN = f"https://cdn.jsdelivr.net/gh/danielyerushalmi/tails-you-lose@{sha}/site/"

html = open(os.path.join(ROOT, "site", "index.html"), encoding="utf-8").read()
n_before = html.count('href="styles.css') + html.count('src="app.js')
html = re.sub(r'href="styles\.css\?v=\d+"', f'href="{CDN}styles.css"', html)
html = re.sub(r'src="app\.js\?v=\d+"', f'src="{CDN}app.js"', html)
html = re.sub(r'<meta property="og:image" content="[^"]+">', f'<meta property="og:image" content="{CDN}assets/og.jpg">', html)
assert n_before == 2 and 'href="styles.css' not in html and 'src="app.js' not in html, "asset rewrite failed"

os.makedirs(os.path.join(ROOT, "deploy"), exist_ok=True)
out = os.path.join(ROOT, "deploy", "index.html")
open(out, "w", encoding="utf-8", newline="\n").write(html)
data = html.encode("utf-8")
print(f"wrote {out}: {len(data)} bytes, sha1 {hashlib.sha1(data).hexdigest()}")
