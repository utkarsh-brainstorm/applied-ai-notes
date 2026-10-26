#!/usr/bin/env python3
"""
Notes Upload and GitHub Publishing Tool
BS Applied AI & Data Science
"""

import os
import sys
import re
import time
import json
import shutil
import argparse
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML = os.path.join(BASE_DIR, 'index.html')
BS_HTML = os.path.join(BASE_DIR, 'BS Applied AI & Data Science.html')
CURRICULUM_JSON = os.path.join(BASE_DIR, 'curriculum.json')
CURRICULUM_JS = os.path.join(BASE_DIR, 'curriculum.js')
CURRICULUM_JS_FILES = os.path.join(BASE_DIR, 'BS Applied AI & Data Science_files', 'curriculum.js')

NOTES_HTML_BASE = os.path.join(BASE_DIR, 'notes', 'html', 'sem4')
NOTES_PDF_BASE = os.path.join(BASE_DIR, 'notes', 'pdf', 'sem4')

SUBJECTS = [
    {
        'id': 'ml2',
        'code': 'ML-201',
        'name': 'Machine Learning 2',
        'prompt': 'Machine Learning 2 (ML2)'
    },
    {
        'id': 'oop',
        'code': 'CS-202',
        'name': 'Object Oriented Programming',
        'prompt': 'Object Oriented Programming (OOP)'
    },
    {
        'id': 'bdm',
        'code': 'DS-203',
        'name': 'Basics of Data Mining',
        'prompt': 'Basics of Data Mining (BDM)'
    },
    {
        'id': 'itw',
        'code': 'WT-204',
        'name': 'Introduction to Web Technologies',
        'prompt': 'Introduction to Web Technologies (ITW)'
    }
]

PREFIX_MAP = {
    'itw': 'IWT',
    'ml2': 'ML2',
    'oop': 'OOP',
    'bdm': 'BDM'
}


LIBRON_FONT_CSS = """
<style id="libron-font-injection">
@font-face {
  font-family: 'Libron';
  src: url('../../../../Libron_Web/Libron-Regular.woff2') format('woff2'),
       url('../../../../Libron_Web/Libron-Regular.ttf') format('truetype');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'Libron';
  src: url('../../../../Libron_Web/Libron-Bold.woff2') format('woff2'),
       url('../../../../Libron_Web/Libron-Bold.ttf') format('truetype');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'Libron';
  src: url('../../../../Libron_Web/Libron-Italic.woff2') format('woff2'),
       url('../../../../Libron_Web/Libron-Italic.ttf') format('truetype');
  font-weight: 400;
  font-style: italic;
  font-display: swap;
}
@font-face {
  font-family: 'Libron';
  src: url('../../../../Libron_Web/Libron-BoldItalic.woff2') format('woff2'),
       url('../../../../Libron_Web/Libron-BoldItalic.ttf') format('truetype');
  font-weight: 700;
  font-style: italic;
  font-display: swap;
}

html, body, .markdown-body, h1, h2, h3, h4, h5, h6, p, span, li, a, td, th {
  font-family: 'Libron', serif, -apple-system, BlinkMacSystemFont !important;
}

body {
  padding: 1.5rem 2rem !important;
  max-width: 900px !important;
  margin: 0 auto !important;
}

/* Dark mode theme styles inside iframe */
[data-theme="dark"] html,
[data-theme="dark"] body,
[data-theme="dark"] .markdown-body {
  background-color: #0a0a0a !important;
  color: #ededed !important;
}
[data-theme="dark"] .markdown-body table tr {
  background-color: #121212 !important;
  border-color: #262626 !important;
}
[data-theme="dark"] .markdown-body table tr:nth-child(2n) {
  background-color: #181818 !important;
}
[data-theme="dark"] .markdown-body table th,
[data-theme="dark"] .markdown-body table td {
  border-color: #2e2e2e !important;
}
[data-theme="dark"] .markdown-body pre,
[data-theme="dark"] .markdown-body code {
  background-color: #141414 !important;
  color: #f0f0f0 !important;
  border-color: #2a2a2a !important;
}
[data-theme="dark"] .markdown-body blockquote {
  color: #999999 !important;
  border-left-color: #444444 !important;
}
[data-theme="dark"] .markdown-body a {
  color: #58a6ff !important;
}
[data-theme="dark"] .markdown-body hr {
  background-color: #262626 !important;
}
</style>
"""


def clean_html(raw_html: str) -> str:
    """
    1. Removes lines containing 'brucks' (case-insensitive).
    2. Removes any word enclosed in '^' (e.g. ^tg1^) along with carets.
    3. Injects Libron font styles and dark mode styling.
    """
    # Remove lines with 'brucks'
    lines = [line for line in raw_html.splitlines() if 'brucks' not in line.lower()]
    cleaned = '\n'.join(lines)

    # Remove words enclosed in ^ like ^tg1^, ^fg1^, ^/tg1^
    cleaned = re.sub(r'\^/?(?:tg|fg)[\w\s]*\^', '', cleaned)

    # Avoid duplicate font injection
    if 'id="libron-font-injection"' not in cleaned:
        if '</head>' in cleaned:
            cleaned = cleaned.replace('</head>', LIBRON_FONT_CSS + '\n</head>')
        else:
            cleaned = LIBRON_FONT_CSS + '\n' + cleaned

    return cleaned


def normalize_path(path_str: str) -> str:
    """Normalize input path string, strip quotes and whitespace."""
    if not path_str:
        return ""
    p = path_str.strip().strip("'\"")
    return os.path.expanduser(p)


def load_curriculum():
    if os.path.exists(CURRICULUM_JSON):
        with open(CURRICULUM_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'semesters': [
            {'id': 1, 'title': 'Semester 01', 'emptyMessage': 'नहीं है मेरे पास', 'subjects': []},
            {'id': 2, 'title': 'Semester 02', 'emptyMessage': 'नहीं है मेरे पास', 'subjects': []},
            {'id': 3, 'title': 'Semester 03', 'emptyMessage': 'नहीं है मेरे पास', 'subjects': []},
            {'id': 4, 'title': 'Semester 04', 'subjects': []}
        ]
    }


def save_curriculum(data):
    # Save JSON
    with open(CURRICULUM_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    # Save JS files
    js_content = 'const CURRICULUM = ' + json.dumps(data, indent=2) + ';\n'
    with open(CURRICULUM_JS, 'w', encoding='utf-8') as f:
        f.write(js_content)

    os.makedirs(os.path.dirname(CURRICULUM_JS_FILES), exist_ok=True)
    with open(CURRICULUM_JS_FILES, 'w', encoding='utf-8') as f:
        f.write(js_content)

    # Bust browser cache in HTML entry points
    ts = int(time.time())
    for html_file in [INDEX_HTML, BS_HTML]:
        if os.path.exists(html_file):
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = re.sub(r'curriculum\.js(?:\?v=\d+)?', f'curriculum.js?v={ts}', content)
                content = re.sub(r'app\.js(?:\?v=\d+)?', f'app.js?v={ts}', content)
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                print(f"[Warning] Could not update cache-buster in {html_file}: {e}")


def ensure_subject_in_sem4(curriculum, sub_id, code, name):
    sem4 = None
    for s in curriculum['semesters']:
        if s['id'] == 4:
            sem4 = s
            break
    if not sem4:
        sem4 = {'id': 4, 'title': 'Semester 04', 'subjects': []}
        curriculum['semesters'].append(sem4)

    for subj in sem4['subjects']:
        if subj['id'] == sub_id:
            return subj

    new_subj = {
        'id': sub_id,
        'code': code,
        'name': name,
        'weeks': []
    }
    sem4['subjects'].append(new_subj)
    return new_subj


def add_or_update_week(subject_obj, week_num, title, html_rel_path, pdf_rel_path):
    existing = None
    for w in subject_obj['weeks']:
        if w['week'] == week_num:
            existing = w
            break

    if existing:
        if title:
            existing['title'] = title
        if html_rel_path:
            existing['htmlPath'] = html_rel_path
        if pdf_rel_path:
            existing['pdfPath'] = pdf_rel_path
    else:
        entry = {
            'week': week_num,
            'title': title or f'Week {week_num} Notes'
        }
        if html_rel_path:
            entry['htmlPath'] = html_rel_path
        if pdf_rel_path:
            entry['pdfPath'] = pdf_rel_path
        subject_obj['weeks'].append(entry)

    # Sort weeks by week number
    subject_obj['weeks'].sort(key=lambda x: x['week'])


def run_cmd(cmd_list):
    print(f"  > {' '.join(cmd_list)}")
    res = subprocess.run(cmd_list, cwd=BASE_DIR, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error: {res.stderr.strip()}")
        return False, res.stderr
    return True, res.stdout.strip()


def push_to_github(commit_msg: str):
    print("\n--- Pushing to GitHub ---")
    run_cmd(["git", "add", "."])
    success, out = run_cmd(["git", "commit", "-m", commit_msg])
    if not success and "nothing to commit" not in out:
        print("Commit note:", out)
    
    # Check remote
    success, remote_out = run_cmd(["git", "remote", "-v"])
    if not success or not remote_out:
        print("No git remote found! Setting up GitHub repository...")
        run_cmd(["gh", "repo", "create", "applied-ai-notes", "--public", "--source=.", "--remote=origin", "--push"])
    else:
        run_cmd(["git", "push", "origin", "main"])

    print("\n✓ Successfully synced with GitHub!")
    print("Live Website: https://utkarsh-brainstorm.github.io/applied-ai-notes/\n")


def interactive_mode():
    print("=" * 60)
    print("     BS APPLIED AI & DATA SCIENCE - NOTES UPLOADER")
    print("=" * 60)

    # 1. Week number
    while True:
        try:
            week_in = input("\nEnter Week number (e.g. 1, 2, ..., 8): ").strip()
            week_num = int(week_in)
            if week_num <= 0:
                print("Please enter a positive week number.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a number.")

    curriculum = load_curriculum()
    updated_files = []

    print(f"\nUploading notes for Week {week_num} across 4 subjects:")
    print("(You can drag-and-drop file paths or press Enter to skip if no file)")

    for subj in SUBJECTS:
        print(f"\n--- {subj['prompt']} ---")
        sub_id = subj['id']
        sub_code = subj['code']
        sub_name = subj['name']

        # HTML note
        html_input = input(f"  Path to HTML note for {sub_name}: ").strip()
        html_path = normalize_path(html_input)

        # PDF note
        pdf_input = input(f"  Path to PDF note for {sub_name}: ").strip()
        pdf_path = normalize_path(pdf_input)

        # Title
        custom_title = input(f"  Title/Topic (optional, press Enter to use default): ").strip()

        html_rel = None
        pdf_rel = None

        if html_path:
            if not os.path.exists(html_path):
                print(f"  [!] Warning: File not found at '{html_path}'. Skipping HTML.")
            else:
                out_dir = os.path.join(NOTES_HTML_BASE, sub_id)
                os.makedirs(out_dir, exist_ok=True)
                dst_file = os.path.join(out_dir, f"week{week_num}.html")
                with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                cleaned_content = clean_html(content)
                with open(dst_file, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                html_rel = f"notes/html/sem4/{sub_id}/week{week_num}.html"
                updated_files.append(dst_file)
                print(f"  ✓ Processed & saved HTML -> {html_rel}")

        if pdf_path:
            if not os.path.exists(pdf_path):
                print(f"  [!] Warning: File not found at '{pdf_path}'. Skipping PDF.")
            else:
                out_dir = os.path.join(NOTES_PDF_BASE, sub_id)
                os.makedirs(out_dir, exist_ok=True)
                prefix = PREFIX_MAP.get(sub_id, sub_id.upper())
                pdf_filename = f"{prefix}_Week{week_num}.pdf"
                dst_file = os.path.join(out_dir, pdf_filename)
                shutil.copy2(pdf_path, dst_file)
                pdf_rel = f"notes/pdf/sem4/{sub_id}/{pdf_filename}"
                updated_files.append(dst_file)
                print(f"  ✓ Copied PDF -> {pdf_rel}")

        if html_rel or pdf_rel:
            subj_entry = ensure_subject_in_sem4(curriculum, sub_id, sub_code, sub_name)
            title = custom_title if custom_title else f"{sub_name} - Week {week_num}"
            add_or_update_week(subj_entry, week_num, title, html_rel, pdf_rel)

    save_curriculum(curriculum)
    print("\n✓ Curriculum updated successfully!")

    if not updated_files:
        print("No new files were provided. Nothing to push.")
        return

    # Ask to push to github
    do_push = input("\nDo you want to commit and push to GitHub now? (Y/n): ").strip().lower()
    if do_push != 'n':
        push_to_github(f"Upload Week {week_num} notes for Semester 4")
    else:
        print("Changes saved locally. You can push manually using git push.")


def main():
    parser = argparse.ArgumentParser(description="Upload notes to BS Applied AI & Data Science website")
    parser.add_argument("--week", type=int, help="Week number (1-12)")
    parser.add_argument("--ml2-html", help="Path to ML2 HTML note")
    parser.add_argument("--ml2-pdf", help="Path to ML2 PDF note")
    parser.add_argument("--oop-html", help="Path to OOP HTML note")
    parser.add_argument("--oop-pdf", help="Path to OOP PDF note")
    parser.add_argument("--bdm-html", help="Path to BDM HTML note")
    parser.add_argument("--bdm-pdf", help="Path to BDM PDF note")
    parser.add_argument("--itw-html", help="Path to ITW HTML note")
    parser.add_argument("--itw-pdf", help="Path to ITW PDF note")
    parser.add_argument("--push", action="store_true", help="Automatically commit and push to GitHub")
    parser.add_argument("--no-push", action="store_true", help="Do not push to GitHub")

    args = parser.parse_args()

    if not args.week:
        interactive_mode()
        return

    week_num = args.week
    curriculum = load_curriculum()
    updated = False

    mapping = {
        'ml2': (args.ml2_html, args.ml2_pdf),
        'oop': (args.oop_html, args.oop_pdf),
        'bdm': (args.bdm_html, args.bdm_pdf),
        'itw': (args.itw_html, args.itw_pdf)
    }

    for subj in SUBJECTS:
        sub_id = subj['id']
        html_src, pdf_src = mapping.get(sub_id, (None, None))
        html_rel = None
        pdf_rel = None

        if html_src:
            src = normalize_path(html_src)
            if os.path.exists(src):
                out_dir = os.path.join(NOTES_HTML_BASE, sub_id)
                os.makedirs(out_dir, exist_ok=True)
                dst = os.path.join(out_dir, f"week{week_num}.html")
                with open(src, 'r', encoding='utf-8', errors='ignore') as f:
                    cleaned = clean_html(f.read())
                with open(dst, 'w', encoding='utf-8') as f:
                    f.write(cleaned)
                html_rel = f"notes/html/sem4/{sub_id}/week{week_num}.html"
                updated = True

        if pdf_src:
            src = normalize_path(pdf_src)
            if os.path.exists(src):
                out_dir = os.path.join(NOTES_PDF_BASE, sub_id)
                os.makedirs(out_dir, exist_ok=True)
                prefix = PREFIX_MAP.get(sub_id, sub_id.upper())
                pdf_filename = f"{prefix}_Week{week_num}.pdf"
                dst = os.path.join(out_dir, pdf_filename)
                shutil.copy2(src, dst)
                pdf_rel = f"notes/pdf/sem4/{sub_id}/{pdf_filename}"
                updated = True

        if html_rel or pdf_rel:
            subj_entry = ensure_subject_in_sem4(curriculum, sub_id, subj['code'], subj['name'])
            add_or_update_week(subj_entry, week_num, f"{subj['name']} - Week {week_num}", html_rel, pdf_rel)

    if updated:
        save_curriculum(curriculum)
        print(f"Updated notes for Week {week_num}")
        if args.push or not args.no_push:
            push_to_github(f"Upload Week {week_num} notes for Semester 4")


if __name__ == "__main__":
    main()
