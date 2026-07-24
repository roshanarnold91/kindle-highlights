# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-07-24

### Added

- Initial release.
- Clippings import with duplicate detection, location/page format support, and import history.
- Library view with cover art, search, sort, and status filters.
- Book detail view with per-book display preference override, filtering, and search.
- Copy-to-clipboard (all / new only / individual) with OneNote-formatted output and copy history.
- Multi-user accounts with admin-only provisioning and full per-user data isolation.
- Per-user SMTP configuration, test email, book/selection email, weekly digest, copy notifications.
- Mobile-responsive UI with bottom navigation.
- Admin panel: user management, storage usage, app-wide SMTP fallback, cross-user import logs.
- Single-container Docker image with multi-stage build, published to GHCR via GitHub Actions.
