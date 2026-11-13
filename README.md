# David Vincent Yoga

**Website preview:** https://ofinch211.github.io/david-vincent-yoga/  
**Source repository:** https://github.com/ofinch211/david-vincent-yoga

The Pages version is a public design preview with direct email/telephone enquiries. The full Flask application and its validated SQLite form remain in this repository for local use or future server hosting. No enquiry records or secrets are included.

A locally runnable, server-rendered yoga website with seven main pages, privacy information, responsive navigation and a real SQLite enquiry form. Built with Flask, Jinja templates, CSS and a small amount of JavaScript. No Node build step, payment integration or accounts are required.

## Run on your Mac

Requires Python 3.10 or later. Open Terminal in this folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. Stop with Control-C. If port 5000 is occupied, run `PORT=5001 python app.py` and open port 5001 instead. Restart the server after Python changes; refresh the browser after template, style or content changes.

## What’s included

- Home, Yoga’s roots, Ashtanga, Dharma, About David, Classes & Pricing, Contact and Privacy pages.
- Shared navigation, footer, custom favicon, individual page titles, descriptions and Open Graph metadata.
- A visual history timeline, Eight Limbs overview, practice explanations, comparison table and class FAQs.
- All five class categories, class-specific enquiry links and configurable prices/durations.
- Validated name, email, optional telephone, practice, optional date/time, experience, message and privacy acknowledgement.
- CSRF protection, a spam honeypot, payload limits, escaped output and duplicate-submission protection.
- SQLite persistence, a separate notification integration point and an explicit enquiry-only confirmation.
- Sitemap, robots file, reduced-motion support, accessible labels, focus styles and a mobile menu.
- Locally served photographs and fonts. No analytics or third-party font requests.

## Edit the content

Edit **content.json** in a text editor. Keep JSON punctuation intact. Refresh to see changes; no rebuild is needed.

- `bio`: David’s main biography introduction.
- `email`, `phone`, `location`, `instagram`: real business details when confirmed. Empty contact fields show clearly labelled placeholders; Instagram is hidden until supplied.
- `portrait`: set to `/static/images/david.jpg` after adding a permission-cleared image of David. The “dv.” monogram is the approved personal-journey visual; retain it unless David specifically requests a portrait.
- `classes`: titles, descriptions, duration, suitability, price and labels. Keep existing class IDs stable so enquiry links remain valid.
- Educational copy and other editorial sections live in the corresponding files under `templates/`.
- Styles and breakpoints live in `static/style.css`. Navigation behaviour lives in `static/site.js`.

David’s teaching experience is stated as **over 200 hours by June 2025**, not teacher-training hours. David’s recognised teaching certification from The Yoga People and the school’s Yoga Alliance registration were supplied by the project owner. The course title, training hours and completion date have not been supplied; no personal Yoga Alliance registration or lineage authorisation is claimed. Training and guide pricing are editable in content.json.

## Replace photographs

Replace `static/images/practice.jpg` (hero), `movement.jpg` (Ashtanga) and `stillness.jpg` (Dharma) with suitably licensed images, keeping filenames or updating template references. Update the associated alt text. Current images were generated with the built-in image tool: one outdoor meditation image in Croydon-inspired parkland, an indoor male practice image and a mostly female class with a male teacher in a modest British hall. They do not depict David, his actual students or a verified teaching venue. See **ASSETS.md** for sources and font licences.

## Read saved enquiries

The database is created automatically at `instance/enquiries.sqlite3`. It is not served by the website and is ignored by Git.

```sh
python manage_enquiries.py
python manage_enquiries.py --export /tmp/david-enquiries.csv
```

The first command lists saved enquiries. The second exports full details to a new CSV; it refuses to overwrite an existing file and neutralises spreadsheet formula prefixes. Keep exports private. Back up the database securely and review retention manually. No public admin interface is exposed. Test submissions use temporary databases and do not populate the real enquiry list.

## Environment variables

`.env.example` documents the available variables. The application reads the process environment; it does not automatically load `.env` files.

```sh
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
export SITE_URL="http://127.0.0.1:5000"
python app.py
```

Set a stable secret in a production environment; without one, a new development key is generated on startup, invalidating earlier forms. `SITE_URL` controls canonical, Open Graph and sitemap URLs. Set `COOKIE_SECURE=1` only when served over HTTPS. Never put credentials in `content.json`, templates or frontend JavaScript.

## Notifications and future bookings

`enquiry_service.py` is the integration boundary. Successful requests are stored before notifications run. By default **no email is sent**. David must read saved records locally.

To integrate notifications, configure `ENQUIRY_WEBHOOK_URL` with an authenticated HTTPS service and `ENQUIRY_WEBHOOK_TOKEN` with its bearer token. The webhook receives a JSON object with `reference` and `enquiry` fields. It can send a notification through an email provider. Configure a provider only when authorised to receive the submitted personal information. A failed notification leaves the enquiry safely stored and logs only its reference. Delivery retries are not implemented. Update the visible local-preview notices and privacy policy when real delivery is configured.

For phase two, introduce separate availability, booking and payment services. Keep an enquiry distinct from a booking; confirm a booking only after availability checks and any real payment-provider confirmation. Google Calendar, Stripe, reminders, cancellations, student accounts, packages and recorded sessions are future work, not simulated features in this version. Use database migrations when adding these records; SQLite can later be replaced with PostgreSQL through the service layer.

## Checks

```sh
python -m unittest discover -s tests -v
```

Eight tests cover all pages and internal assets, persistence, form validation, CSRF/honeypot rejection, duplicate submission handling, storage errors, escaping/payload limits, metadata endpoints and security headers. The expected storage-error test writes an error log while verifying recovery. Desktop and 400px homepage layouts were visually reviewed in native Chrome. Complete mobile menu interaction and full-page/device accessibility review remain manual checks; browser automation was unreliable in this session.

## Before public launch

This version is a **local preview** and has not been published. The teaching area is in and around Sanderstead, South Croydon. Guide rates are approximately £30 per person for small groups and private sessions from £40. David’s certification is with The Yoga People. Confirm the exact venue, travel arrangements, final prices, durations, availability and business contact details. Keep the approved dv. monogram for the personal journey visual. Review the first-person copy with David. Confirm the privacy controller/contact, retention policy and providers, then update the preview policy and local-only notices.

Set the real HTTPS `SITE_URL`, stable secret and secure cookies. Use a production WSGI server behind HTTPS, persistent private storage with backups, and suitable abuse/rate limiting. Flask’s built-in server is for local review. For example, install Gunicorn separately on a supported host and run `gunicorn --bind 127.0.0.1:8000 app:app` behind your reverse proxy. Keep the `instance/` directory outside public static hosting. No special directory may expose the database or exports.

Add accurate local-business structured data only when the business details are confirmed. Run a complete keyboard, phone and accessibility review before accepting public enquiries. Confirm notification delivery end to end before relying on it. Agree cancellation/payment terms before adding paid booking. The site deliberately has no fabricated prices, addresses, social profiles or testimonials.

## Project structure

```text
app.py                    Routes, validation, page metadata and security headers
content.json              Editable business and class configuration
enquiry_service.py        SQLite storage and optional notification webhook
manage_enquiries.py       Local enquiry viewing and CSV export
templates/                Reusable layout and page templates
static/                   Styles, mobile navigation, images, fonts and favicon
tests/test_site.py        Functional tests with isolated databases
instance/                 Private runtime database (ignored)
status.md                 Timestamped progress log, newest updates first
```

## Pending details and policy drafts

The owner will supply session lengths, maximum group size, initial availability, exact venue, final price inclusions and any travel/venue extras, cancellation notice, payment methods/due dates, email delivery arrangements, domain and hosting details later. These are deferred; do not invent them.

Draft Terms & Conditions are at /terms and the updated privacy/cookie notice at /privacy. They describe the current enquiry-only service and preserve consumer rights. Both use David’s supplied contact details. Before public launch, complete the business correspondence address, hosting/providers, transfer and backup/log-retention arrangements and any booking rules; do not present the drafts as final paid-booking terms. The default routine-enquiry retention is six months after last contact, reviewed manually. See status.md for the current outstanding list.

## Appearance controls

The header includes a day/dark switch and an appearance-settings button. Five palettes are available: Forest & Ivory (the original default), Coastal Blue, Warm Terracotta, Soft Lavender, and Olive & Sand. Each has a coordinated dark version covering text, section backgrounds, forms, buttons and the dv. monogram.

Preferences are stored only in the current browser under `dv-yoga-appearance`, survive refresh/navigation, and can be reset with “Restore original”. A choice in David’s browser does not change the default for other visitors. Once he chooses the permanent brand palette, update the default preference in static/appearance.js (and the no-JavaScript :root fallback in static/style.css) to apply it site-wide. The current default remains the original day palette.

static/appearance.js applies a saved preference before styles paint and handles settings, keyboard-accessible native dialog behaviour and storage failures. The palette variables are in the Appearance system section at the end of static/style.css. Controls stay hidden if JavaScript is unavailable. The privacy page describes preference storage.

Validation: eight existing functional tests pass; both JavaScript files pass syntax checks. Native Chrome checks covered switching modes, palette selection, refresh persistence, restoring the original and the settings layout at 400px. Core text/background contrast pairs were checked across all five palettes in both modes (minimum 4.5:1); this is not a complete accessibility audit.

## GitHub Pages preview

The one hosted preview is built into `docs/`. GitHub Pages publishes `main` → `/docs`, with HTTPS. Python server code is not executed by Pages; the preview’s contact page instead opens an email draft to David, with no automatic sending or stored submissions. The preview has its own accurate privacy notice, and all pages request no search indexing while business details are still provisional. This is a review link, not a completed paid-booking launch.

To update the preview after changing content or templates:

```sh
python3 scripts/build_pages.py
python3 -m unittest discover -s tests -v
git add .
git commit -m "Update website preview"
git push origin main
```

Wait for the repository’s Pages deployment to finish. Keep `instance/`, `.env`, private exports and credentials out of Git; `.gitignore` excludes them. Retain `docs/.nojekyll` so Pages serves the exported files directly. `scripts/build_pages.py` fixes project-subpath links and local font URLs, renders every page, and exports no database or form tokens. The local Flask version still runs with `python3 app.py`.
