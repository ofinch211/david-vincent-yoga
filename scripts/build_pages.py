"""Export an isolated GitHub Pages preview; keep the Flask application intact.

Run: python3 scripts/build_pages.py
Never copies instance/, secrets, exports or runtime databases.
"""
import argparse
import html
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlencode
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import PAGES, create_app
from flask import render_template


def build(destination, base_url):
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    if parsed.scheme not in ['https', 'http'] or not parsed.netloc:
        raise ValueError('Use a full http(s) base URL')
    prefix = parsed.path.rstrip('/')
    site = json.loads((ROOT / 'content.json').read_text())
    routes = {name: prefix + ('/' if name == 'home' else '/' + name + '/') for name in PAGES}

    def rewrite_markup(markup):
        def replace(match):
            attr, quote, value = match.groups()
            if value.startswith('/static/'):
                value = prefix + value
            elif value.startswith('/') and not value.startswith('//'):
                path = re.split(r'[?#]', value, maxsplit=1)[0]
                suffix = value[len(path):]
                key = path.strip('/') or 'home'
                value = routes.get(key, prefix + path) + suffix
            return attr + '=' + quote + value + quote
        return re.sub(r'(href|src|action)=([\"\'])(.*?)\2', replace, markup)

    destination.mkdir(parents=True, exist_ok=True)
    # Only replace a dedicated generated output directory, never the source tree.
    asset_dir = destination / 'static'
    if asset_dir.exists():
        shutil.rmtree(asset_dir)
    shutil.copytree(ROOT / 'static', asset_dir)
    for asset in asset_dir.rglob('*'):
        if asset.suffix in ['.css', '.js']:
            asset.write_text(asset.read_text().replace('/static/', prefix + '/static/'))
    with tempfile.TemporaryDirectory() as temporary:
        app = create_app({'TESTING': True, 'DATABASE': str(Path(temporary) / 'preview.sqlite3'), 'SITE_URL': base_url.rstrip('/')})
        for name, (title, description) in PAGES.items():
            template = {'contact': 'contact_static.html', 'privacy': 'privacy_static.html'}.get(name, name + '.html')
            with app.test_request_context('/' if name == 'home' else '/' + name):
                markup = render_template(template, page=name, title=title, description=description, static_preview=True,
                    enquiry_mailto='mailto:' + site['email'] + '?' + urlencode({'subject': 'Yoga session enquiry', 'body': 'Hello David,\n\nI would like to enquire about a yoga session.\n\nPreferred practice:\nExperience:\nPreferred dates / times:\n\nThank you.'}))
            # Canonical/OG URLs use clean Pages directory routes.
            canonical = base_url.rstrip('/') + ('/' if name == 'home' else '/' + name + '/')
            markup = re.sub(r'(<link rel="canonical" href=")[^"]+', lambda m: m.group(1) + html.escape(canonical, quote=True), markup)
            markup = re.sub(r'(<meta property="og:url" content=")[^"]+', lambda m: m.group(1) + html.escape(canonical, quote=True), markup)
            target = destination / ('index.html' if name == 'home' else name + '/index.html')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(rewrite_markup(markup))
        with app.test_request_context('/not-found'):
            markup = render_template('404.html', page='', title='Page not found', description='Return to David Vincent Yoga.', static_preview=True)
            (destination / '404.html').write_text(rewrite_markup(markup))
    (destination / '.nojekyll').write_text('')
    (destination / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + base_url.rstrip('/') + '/sitemap.xml\n')
    urls = [base_url.rstrip('/') + ('/' if name == 'home' else '/' + name + '/') for name in PAGES]
    (destination / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>' + escape(url) + '</loc></url>' for url in urls) + '</urlset>')
    print(f'Exported {len(PAGES)} pages to {destination} for {base_url}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='https://ofinch211.github.io/david-vincent-yoga')
    args = parser.parse_args()
    build(ROOT / 'docs', args.base_url)
