# Changelog

All notable changes to **IP Blender Tool** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.6.0] - 2026-06-16
### Added
- **AppData Storage Isolation**: Relocated `jobs.sqlite` database, log files, and system preferences to `%APPDATA%/IP Blender Tool/` directory to prevent permission errors on Windows.
- **Windows Path Sanitization**: Implemented robust sanitization in `sanitize_folder_name` (replaces illegal characters, limits path parts to 80 chars, and prefixes Windows reserved keywords like `NUL`, `CON`, `PRN`).
- **Traversal Boundary Check**: Added validation in output planner to assert resolved render subfolders reside strictly inside the project output folder root.
- **Legacy Compatibility Routing**: Re-implemented project directory scanning prioritizing `(PROJECT)*` and camera destination routing folders based on existing folder discovery (`posibles_carpetas`).
- **Naming Style Settings**: Added toggle selector in configuration to switch between legacy Simple (`01.png`/`01.jpg`) and versioned Professional (`0024_Camara_A_v001.png`) naming formats.
- **Verification Script**: Created `verify.py` to test environment health, PySide6, psutil, SQLite WAL, and AppData directories.
- **Documentation Suite**: Added chapters detailing architecture, visions, user manual, and CLI contracts.

## [0.5.0] - 2026-06-16
### Added
- **FFmpeg Integration**: Auto-compilation of image sequences to H.264 MP4 videos using the exact rational framerate parsed from Blender's settings.
- **Thumbnail Previews**: Automatic downscaling of renders using FFmpeg to display thumbnails in logs and notifications.
- **Telegram/Discord Webhooks**: Outbox background worker queue to dispatch alerts with media without stalling renders.

## [0.4.0] - 2026-06-16
### Added
- **Subprocess Runner**: CLI Blender launcher parsing stdout to report live percentage progress for Cycles/Eevee.
- **Safe Abort (psutil)**: Recursive process tree killer ensuring all nested Blender execution threads terminate on cancel.
- **Power Actions**: System power state controls (Shutdown/Sleep) upon queue completion.

## [0.3.0] - 2026-06-16
### Added
- **PySide6 Dark Mode GUI**: Simple 3-zone visual layout with Project ingest, Camera checklists, Render profiles, Queue tables, and Collapsible technical log console.
- **Settings configuration**: Persisted settings panel.

## [0.2.0] - 2026-06-16
### Added
- **Scene Ingestion**: Background Blender scanning utilizing `scan_scene.py` to extract cameras, active settings, frame ranges, and check for missing assets/textures.

## [0.1.0] - 2026-06-16
### Added
- Initial modular Python structure, SQLite configuration with WAL, and basic automation logic.
