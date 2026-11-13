import re
import sqlite3
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from app import create_app, PAGES


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ['href', 'src']:
            target = attrs.get(key, '')
            if target.startswith('/') and not target.startswith('//'):
                self.targets.append(target.split('#')[0])


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.db = str(Path(self.directory.name) / 'test.sqlite3')
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'test-only-secret', 'DATABASE': self.db})
        self.client = self.app.test_client()
    def tearDown(self):
        self.directory.cleanup()
    def valid_form(self):
        page = self.client.get('/contact').get_data(as_text=True)
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        return dict(csrf_token=token, name='Test Student', email='student@example.com', phone='', class_type='private', preferred_date='2099-01-01', preferred_time='10:30', experience='new', message='Interested in a first session', consent='yes')
    def count(self):
        with sqlite3.connect(self.db) as db:
            return db.execute('SELECT COUNT(*) FROM enquiries').fetchone()[0]
    def test_pages_assets_and_internal_links(self):
        for page in PAGES:
            path = '/' if page == 'home' else '/' + page
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            html = response.get_data(as_text=True)
            self.assertEqual(len(re.findall(r'<h1[ >]', html)), 1, path)
            parser = Links()
            parser.feed(html)
            for target in set(parser.targets):
                with self.client.get(target) as linked_response:
                    self.assertEqual(linked_response.status_code, 200, f'{path} → {target}')
    def test_valid_enquiry_is_persisted_and_does_not_claim_booking(self):
        with patch('app.notify_enquiry') as notify:
            response = self.client.post('/contact', data=self.valid_form(), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Your enquiry is saved.', response.data)
        self.assertIn(b'not a confirmed appointment', response.data)
        self.assertEqual(self.count(), 1)
        notify.assert_called_once()
        self.assertNotIn(b'Your enquiry is saved.', self.client.get('/contact?sent=1').data)
    def test_invalid_fields_preserve_input_without_saving(self):
        data = self.valid_form()
        data.update(email='invalid', preferred_date='2020-01-01', preferred_time='25:00', experience='invalid', class_type='invalid')
        del data['consent']
        response = self.client.post('/contact', data=data)
        self.assertEqual(response.status_code, 422)
        self.assertIn(b'Test Student', response.data)
        self.assertIn(b'Please check your enquiry', response.data)
        self.assertEqual(self.count(), 0)
    def test_csrf_and_honeypot_reject_requests(self):
        data = self.valid_form()
        data['csrf_token'] = 'invalid'
        self.assertEqual(self.client.post('/contact', data=data).status_code, 422)
        data = self.valid_form()
        data['website'] = 'spam'
        self.assertEqual(self.client.post('/contact', data=data).status_code, 422)
        self.assertEqual(self.count(), 0)
    def test_resubmission_does_not_duplicate(self):
        data = self.valid_form()
        self.assertEqual(self.client.post('/contact', data=data).status_code, 303)
        self.assertEqual(self.client.post('/contact', data=data).status_code, 422)
        self.assertEqual(self.count(), 1)
    def test_storage_failure_provides_recoverable_error(self):
        data = self.valid_form()
        with patch('app.save_enquiry', side_effect=sqlite3.OperationalError('test failure')):
            response = self.client.post('/contact', data=data)
        self.assertEqual(response.status_code, 422)
        self.assertIn(b'could not be saved', response.data)
        self.assertEqual(self.count(), 0)
    def test_escaping_and_payload_limits(self):
        data = self.valid_form()
        data['name'] = '<script>alert(1)</script>'
        data['message'] = 'x' * 3001
        response = self.client.post('/contact', data=data)
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(b'<script>alert(1)</script>', response.data)
        self.assertIn(b'&lt;script&gt;', response.data)
        self.assertEqual(self.client.post('/contact', data={'message': 'x' * 40000}).status_code, 413)
    def test_seo_and_security(self):
        self.assertEqual(self.client.get('/not-found').status_code, 404)
        response = self.client.get('/contact')
        self.assertIn('HttpOnly', response.headers['Set-Cookie'])
        self.assertIn('SameSite=Lax', response.headers['Set-Cookie'])
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
        self.assertIn("default-src 'self'", response.headers['Content-Security-Policy'])
        from xml.etree import ElementTree
        root = ElementTree.fromstring(self.client.get('/sitemap.xml').data)
        self.assertEqual(len(root), len(PAGES))
        self.assertIn(b'Sitemap:', self.client.get('/robots.txt').data)

if __name__ == '__main__':
    unittest.main()
