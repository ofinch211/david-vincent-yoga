"""Check the exported preview is independent of Flask and project-path safe."""
import re
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from scripts.build_pages import build
from app import PAGES

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ['href', 'src'] and value and value.startswith('/'):
                self.targets.append(value)

class PagesTests(unittest.TestCase):
    def test_export_has_no_backend_dependencies_or_private_records(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build(root, 'https://example.github.io/yoga')
            self.assertTrue((root / '.nojekyll').exists())
            contact = (root / 'contact/index.html').read_text()
            self.assertNotIn('<form', contact)
            self.assertIn('mailto:dlvincent@hotmail.co.uk', contact)
            self.assertIn('opens your email application', contact)
            self.assertFalse(list(root.rglob('*.sqlite3')))
            for page in root.rglob('*.html'):
                text = page.read_text()
                self.assertNotIn('csrf_token', text)
                self.assertNotIn('127.0.0.1', text)
                self.assertIn('name="robots" content="noindex, nofollow"', text)
            self.assertEqual(len(list(root.rglob('index.html'))), len(PAGES))
    def test_export_links_and_fonts_resolve_under_repository_prefix(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build(root, 'https://example.github.io/yoga')
            for page in root.rglob('*.html'):
                parser = Links()
                parser.feed(page.read_text())
                for target in parser.targets:
                    path = urlparse(target).path
                    self.assertTrue(path.startswith('/yoga/'), (page, target))
                    local = root / path[len('/yoga/'):]
                    if local.is_dir():
                        local = local / 'index.html'
                    self.assertTrue(local.exists(), (page, target))
            css = (root / 'static/style.css').read_text()
            self.assertIn("url('/yoga/static/fonts/", css)
            about = (root / 'about/index.html').read_text()
            self.assertIn('href="https://example.github.io/yoga/about/"', about)

if __name__ == '__main__':
    unittest.main()
