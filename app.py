import hmac
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from flask import Flask, abort, make_response, redirect, render_template, request, session, url_for
from enquiry_service import initialise_database, save_enquiry, notify_enquiry

ROOT = Path(__file__).parent
PAGES = {
    'home': ('A practice to come home to', 'Ashtanga and Dharma Yoga near Sanderstead, South Croydon, with David Vincent. Private sessions from £40 and small-group yoga around £30 per person.'),
    'history': ('The history of yoga', 'Explore the Indian roots of yoga, the Eight Limbs, Hatha Yoga and the evolution of modern practice.'),
    'ashtanga': ('Ashtanga Vinyasa Yoga', 'Discover Ashtanga: breath, movement and a progressive practice. Learn about the Primary Series, Mysore style and led classes.'),
    'dharma': ('Dharma Yoga', 'Explore the holistic yoga approach developed by Sri Dharma Mittra, bringing together posture, breathing and meditation.'),
    'about': ('Meet David', 'Meet David Vincent, certified through The Yoga People, teaching yoga near Sanderstead. Practising since April 2022, with over 200 teaching hours by June 2025.'),
    'classes': ('Find your practice', 'Private yoga from £40 and small-group sessions around £30 per person near Sanderstead, South Croydon. Explore Ashtanga, Dharma and beginner sessions.'),
    'contact': ('Let’s begin with a conversation', 'Enquire about a personal Ashtanga or Dharma Yoga session with David Vincent. Find a practice that fits your experience.'),
    'terms': ('Terms & conditions', 'Terms for yoga enquiries, guide pricing, participation and future bookings with David Vincent Yoga.'),
    'privacy': ('Your privacy', 'How David Vincent Yoga handles session enquiries, essential cookies and your personal information.')
}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
        DATABASE=str(ROOT / 'instance' / 'enquiries.sqlite3'),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE') == '1',
        MAX_CONTENT_LENGTH=32 * 1024,
        SITE_URL=os.environ.get('SITE_URL', 'http://127.0.0.1:5000').rstrip('/'))
    if test_config:
        app.config.update(test_config)
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    initialise_database(app.config['DATABASE'])

    @app.context_processor
    def context():
        return {'site': json.loads((ROOT / 'content.json').read_text()), 'year': datetime.now().year}

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self'; form-action 'self'; base-uri 'self'; frame-ancestors 'none'"
        return response

    @app.route('/')
    @app.route('/<page>')
    def page_view(page='home'):
        if page not in PAGES:
            abort(404)
        return render_template(f'{page}.html', page=page, title=PAGES[page][0], description=PAGES[page][1])

    @app.route('/contact', methods=['GET', 'POST'], endpoint='contact')
    def contact():
        data = {}
        errors = {}
        today = datetime.now(ZoneInfo('Europe/London')).date()
        if request.method == 'POST':
            fields = ['name', 'email', 'phone', 'class_type', 'preferred_date', 'preferred_time', 'experience', 'message']
            data = {key: request.form.get(key, '').strip() for key in fields}
            token = request.form.get('csrf_token', '')
            if not token or not hmac.compare_digest(token, session.get('enquiry_token', '')):
                errors['form'] = 'This form has expired. Please review your details and try again.'
            if request.form.get('website'):
                errors['form'] = 'We could not accept this request. Please try again.'
            if not 2 <= len(data['name']) <= 100:
                errors['name'] = 'Please enter your full name (2–100 characters).'
            if len(data['email']) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', data['email']):
                errors['email'] = 'Please enter a valid email address.'
            if len(data['phone']) > 40:
                errors['phone'] = 'Please use no more than 40 characters.'
            choices = json.loads((ROOT / 'content.json').read_text())['classes']
            if data['class_type'] not in [c['id'] for c in choices] + ['unsure']:
                errors['class_type'] = 'Please select a practice or choose “Help me choose”.'
            if data['experience'] not in ['new', 'some', 'regular']:
                errors['experience'] = 'Please select your experience level.'
            if data['preferred_date']:
                try:
                    if datetime.strptime(data['preferred_date'], '%Y-%m-%d').date() < today:
                        raise ValueError()
                except ValueError:
                    errors['preferred_date'] = 'Please choose today or a future date.'
            if data['preferred_time'] and not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', data['preferred_time']):
                errors['preferred_time'] = 'Please enter a valid time.'
            if len(data['message']) > 3000:
                errors['message'] = 'Please keep your message under 3,000 characters.'
            if request.form.get('consent') != 'yes':
                errors['consent'] = 'Please acknowledge the privacy policy to send your enquiry.'
            if not errors:
                try:
                    reference = save_enquiry(app.config['DATABASE'], data, token)
                except sqlite3.Error:
                    app.logger.error('Enquiry storage unavailable')
                    errors['form'] = 'Your enquiry could not be saved. Please try again shortly.'
                else:
                    if reference:
                        notify_enquiry(reference, data, os.environ.get('ENQUIRY_WEBHOOK_URL', ''), os.environ.get('ENQUIRY_WEBHOOK_TOKEN', ''))
                    session.pop('enquiry_token', None)
                    session['enquiry_saved'] = True
                    return redirect(url_for('contact', sent='1') + '#enquiry-result', code=303)
        if not session.get('enquiry_token') or errors.get('form'):
            session['enquiry_token'] = secrets.token_urlsafe(32)
        sent = request.args.get('sent') == '1' and session.pop('enquiry_saved', False)
        return render_template('contact.html', page='contact', title=PAGES['contact'][0], description=PAGES['contact'][1],
            data=data, errors=errors, sent=sent, token=session['enquiry_token'], today=today.isoformat()), 422 if errors else 200

    @app.route('/robots.txt')
    def robots():
        return app.response_class(f"User-agent: *\nAllow: /\nSitemap: {app.config['SITE_URL']}/sitemap.xml\n", mimetype='text/plain')

    @app.route('/sitemap.xml')
    def sitemap():
        urls = [app.config['SITE_URL'] + ('/' if p == 'home' else '/' + p) for p in PAGES]
        from xml.sax.saxutils import escape
        return app.response_class('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{escape(u)}</loc></url>' for u in urls) + '</urlset>', mimetype='application/xml')

    @app.errorhandler(404)
    def missing(error):
        return render_template('404.html', page='', title='Page not found', description='Find your way back to David Vincent Yoga.'), 404

    return app

app = create_app()
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 5000)))
