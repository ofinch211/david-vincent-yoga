"""Read/export saved enquiries from the local machine; no public admin endpoint."""
import argparse
import csv
import sqlite3
import sys
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--export', type=Path, help='Write all enquiry fields to a private CSV file')
args = parser.parse_args()
path = Path(__file__).parent / 'instance' / 'enquiries.sqlite3'
if not path.exists():
    sys.exit('No enquiry database yet. Start the website first.')
with sqlite3.connect(path) as db:
    db.row_factory = sqlite3.Row
    rows = db.execute('SELECT id, created_at, name, email, phone, class_type, preferred_date, preferred_time, experience, message, consent FROM enquiries ORDER BY id DESC').fetchall()
if args.export:
    # Refuse to overwrite existing exports and neutralise spreadsheet formulas.
    with args.export.open('x', newline='') as output:
        writer = csv.writer(output)
        if rows:
            writer.writerow(rows[0].keys())
            for row in rows:
                writer.writerow("'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v for v in row)
    print(f'Exported {len(rows)} enquiries to {args.export}. Keep this file private.')
else:
    for row in rows:
        print(f"#{row['id']} | {row['created_at']} | {row['name']} | {row['email']} | {row['class_type']}")
    print(f'{len(rows)} enquiries. Use --export /private/path/enquiries.csv for full details.')
