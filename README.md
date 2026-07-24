# Kindle Highlights Manager

A self-hosted web app that parses your Kindle's `My Clippings.txt` file and
gives you a searchable library of highlights and notes, with one-click
formatted copy for pasting into OneNote (or anywhere else).

- **Backend:** Python (Flask + SQLite)
- **Frontend:** React + Tailwind CSS
- **Runs as:** a single Docker container
- **Data:** stored entirely on your own volume — nothing leaves the server

## Features

- Drag-and-drop import of `My Clippings.txt` with automatic duplicate detection
- Library grid with cover art (via Google Books), search, sort and filters
- Per-book highlight/note/bookmark view with location and/or page display
- "Copy all" / "copy new only" / individual copy, formatted for OneNote
- Per-user copy history, so "new since last copy" always works
- Multi-user accounts (admin-provisioned, no self-registration), fully isolated
- Per-user SMTP settings — email a book, email selected highlights, weekly digest
- Mobile-first responsive UI with bottom navigation
- Admin panel: user management, storage usage, app-wide SMTP fallback, import logs

## Installing Docker on Windows

If you're running this on Windows 11 (or 10), install Docker Desktop first:

1. Enable WSL2 (Windows Subsystem for Linux), if you haven't already — open
   PowerShell **as Administrator** and run:
   ```powershell
   wsl --install
   ```
   Reboot when prompted.
2. Download and install **Docker Desktop for Windows** from
   [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/).
3. During setup, make sure **"Use WSL 2 based engine"** is enabled (Settings →
   General). This is the default on modern installs and is required — the
   older Hyper-V backend is not recommended.
4. Launch Docker Desktop and wait for it to report "Docker Desktop is
   running" in the system tray.
5. Verify the install by opening PowerShell (a normal, non-admin window) and
   running:
   ```powershell
   docker --version
   docker compose version
   ```
   Both should print a version number.
6. Create the folder Docker will use for app data, e.g.:
   ```powershell
   New-Item -ItemType Directory -Force J:\kindle-highlights
   ```

You can now follow the Quick start steps below using PowerShell instead of
bash — the commands are the same, aside from `curl` and `cp` (PowerShell's
built-in aliases for `Invoke-WebRequest`/`Copy-Item` handle these
transparently, so no changes are needed).

## Quick start

Requires Docker and Docker Compose.

```bash
mkdir kindle-highlights && cd kindle-highlights
curl -O https://raw.githubusercontent.com/roshanarnold91/kindle-highlights/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/roshanarnold91/kindle-highlights/main/.env.example
cp .env.example .env
```

Edit `.env` and set at minimum `SECRET_KEY`, `ADMIN_PASSWORD`, and `DATA_PATH`
(the host folder where your database and uploads will live, e.g.
`J:/kindle-highlights` on Windows).

```bash
docker compose up -d
```

The app is now running at `http://<host>:5000`. Log in with username `admin`
and the password you set in `.env`. From **Admin → Users**, create an
individual account for each person who'll use the app — there's no
self-registration by design.

### Uploading your highlights

1. On your Kindle, connect it via USB and copy `documents/My Clippings.txt`
   to your computer (or phone, if you export it another way).
2. In the app, go to **Upload**, drag the file in (or tap to pick it).
3. Re-uploading the same or an updated file only imports new entries —
   duplicates are detected automatically.

## Configuration reference (`.env`)

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | yes | Random key used to sign session cookies |
| `ADMIN_PASSWORD` | yes | Password for the bootstrap `admin` account |
| `ADMIN_USERNAME` | no | Bootstrap admin username (default `admin`) |
| `DATA_PATH` | no | Host folder mapped to `/data` (default `./data`) |
| `APP_PORT` | no | Host port to expose (default `5000`) |
| `REMEMBER_COOKIE_DURATION_DAYS` | no | "Remember me" session length (default `30`) |
| `GOOGLE_BOOKS_API_KEY` | no | Raises the Google Books rate limit for cover art lookups |
| `APP_SMTP_*` | no | App-wide SMTP fallback for users without their own SMTP settings |

Per-user SMTP settings (Gmail App Passwords, Outlook, or any SMTP provider)
are configured in-app under **Settings**, not in `.env`.

## Data & backups

Everything lives under the folder you mapped to `DATA_PATH`:

```
data/
├── db/highlights.db     # SQLite database
└── uploads/<user_id>/   # raw uploaded clippings files, kept for history
```

Back up that folder however you already back up the rest of your self-hosted
stack (e.g. Backrest). No data is sent anywhere else.

## Local development

```bash
docker compose -f docker-compose.dev.yml up
```

This runs the Flask backend with auto-reload on port 5000 and the Vite dev
server (with hot reload) on port 5173. Open `http://localhost:5173`.

## Building the image yourself

```bash
docker build -t kindle-highlights .
```

## Tech notes

- Single container: the React app is built at image build time and served
  as static files by Flask, so there's nothing else to run or reverse-proxy.
- SQLite is sufficient for personal/family-scale use; the whole app is
  designed to be lightweight enough to sit alongside other self-hosted
  services on modest hardware.
- No built-in HTTPS or reverse proxy — pair it with something like Tailscale,
  or your own reverse proxy, if you need remote access.

## License

MIT
