# Simple Drive

Simple Drive is a Django file-sharing application inspired by Google Drive and Dropbox. It focuses on a clean files-only workflow with folders, storage quotas, expiring public share links, QR codes, trash recovery, and a modern server-rendered UI powered by DaisyUI and HTMX.

The app keeps the stack intentionally simple: Django renders the pages and partials, HTMX handles small interactions without full-page reloads, and DaisyUI/Tailwind are loaded from CDNs without a Node build step.

## Features

- Public landing page with plan information
- User signup, login, and logout
- Dashboard with drive totals, recent items, largest files, and storage usage
- File Explorer with folders and breadcrumbs
- Drag-and-drop upload modal with selected file previews
- File and folder rename and move actions
- Search across files and folders in the current location
- File downloads with the original filename preserved
- Expiring share links with QR code generation
- Share modal copy buttons for share page and direct download URLs
- Visible expiration countdown for shared files and public share pages
- Unshare controls for active shares
- Soft delete to Trash, restore, permanent delete, and empty trash
- Storage quota plans managed through Django admin
- Light/dark theme switch
- DaisyUI toast notifications for uploads, errors, deletes, and other actions

## Tech Stack

- Python
- Django 6
- SQLite for local development
- DaisyUI and Tailwind via CDN
- HTMX via CDN
- Lucide icons via CDN
- qrcodejs for QR code rendering

## Project Structure

```text
.
├── README.md
├── app/
│   ├── manage.py              # production settings entrypoint
│   ├── manage_dev.py          # local development settings entrypoint
│   ├── requirements.txt
│   ├── app/                   # project settings and root URLs
│   ├── files/                 # drive, files, folders, shares, trash, quotas
│   ├── landing/               # public home page
│   ├── users/                 # custom user model and auth views
│   └── locale/
└── media/                     # uploaded files in local development
```

## Main Routes

- `/` - landing page
- `/signup` - create an account
- `/login` - sign in
- `/dashboard` - drive dashboard
- `/files` - File Explorer
- `/trash` - Trash
- `/s/<token>` - public share page
- `/s/<token>/download` - public share download
- `/OBzwyYM/` - Django admin

## Local Setup

The project expects a virtual environment at `./venv/` in the repository root.

```bash
cd app
../venv/bin/python manage_dev.py migrate
../venv/bin/python manage_dev.py createsuperuser
../venv/bin/python manage_dev.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

If dependencies need to be installed in a fresh environment:

```bash
../venv/bin/python -m pip install -r requirements.txt
```

## Development Commands

Run Django checks:

```bash
cd app
../venv/bin/python manage.py check
```

Run tests:

```bash
cd app
../venv/bin/python manage.py test
```

Run only the file app tests:

```bash
cd app
../venv/bin/python manage.py test files
```

For local development, prefer `manage_dev.py` when running the server because it loads `app.settings.dev`.

## Configuration

Important settings live in `app/app/settings/base.py`.

- `MAX_FILESIZE` - maximum upload size per file, in MB
- `FILE_SHARE_EXPIRE_HOURS` - default lifetime for public share links
- `DEFAULT_STORAGE_QUOTA_BYTES` - fallback storage quota for users without a plan
- `MEDIA_ROOT` - local uploaded file storage path
- `MEDIA_URL` - URL prefix for uploaded files

Settings modules:

- `app.settings.dev` - development settings, debug enabled
- `app.settings.prod` - production settings, debug disabled

## Storage Plans

Storage plans are managed with the `StorageQuote` model in the `files` app. The current seeded plans are:

- Free: 1 GB
- Standard: 10 GB
- Premium: 1 TB

Users receive the default plan automatically. Staff users can change a user's plan from the Django admin user edit page.

## File Storage Notes

Uploaded files keep the existing `File` model behavior:

- The original filename is stored in `old_file_name`.
- The physical file path uses a generated filename under the user's media directory.
- Existing database rows and uploaded media should continue to work across UI changes.

Deleted files and folders are soft-deleted first and remain in storage until permanently deleted from Trash or removed by Empty Trash.

## Sharing Notes

File shares are stored as `FileShare` rows with generated tokens and expiration timestamps. When a user shares a file that already has an active share, the existing link is reused. A fresh link can be issued from the share modal when needed.

Public share pages show an expiration timer and provide a direct download button. Expired share links return an expired-share page instead of the file.

## UI Notes

The active UI is built with Django templates, DaisyUI, HTMX, and small vanilla JavaScript helpers. There is no Node, npm, webpack, Vite, or Tailwind build process in this version.

HTMX is used for:

- File list refreshes
- Folder navigation without full-page reloads
- Upload, delete, restore, rename, and move responses
- Toast notifications through out-of-band swaps
- Auth login/signup switching

## Current Scope

Simple Drive currently supports personal drive storage, folders, uploads, downloads, search, trash, quotas, and expiring file shares.

Not included yet:

- Team drives
- Per-folder permissions
- Public folders
- Collaborative editing
- File version history
- Cloud object storage backend
