# Database Schema - IP Blender Tool

This document outlines the SQLite schema for **IP Blender Tool** located at `%APPDATA%/IP Blender Tool/jobs.sqlite`.

---

## 🏎️ Database Configuration
* **Journal Mode**: `WAL` (Write-Ahead Logging) to prevent readers from blocking writers and vice versa.
* **Busy Timeout**: `5000` (5.0 seconds) to retry queries under high lock contention without raising lock errors.

---

## 📊 Database Tables

### 1. `projects`
Tracks projects that have been ingested in any of the three ingestion modes.
* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `project_code` TEXT (Unique identifier, e.g. `0024`. Optional, can be NULL for generic modes)
* `blend_path` TEXT (Path of the project directory or single blend file depending on mode)
* `output_path` TEXT (Resolved directory where renders go)
* `project_mode` TEXT (Ingestion mode: `IP_LEGACY`, `MANUAL_FOLDER`, `SINGLE_BLEND`)
* `project_root` TEXT (Root directory of the project files)
* `selected_blend_file` TEXT (Path of the selected `.blend` file if in `SINGLE_BLEND` mode, else NULL)
* `renders_root` TEXT (Base renders folder configured for this project)
* `profile_name` TEXT (Active settings profile name under which the project was ingested)
* `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

### 2. `snapshots`
Stores metadata scans of `.blend` files to act as static pre-flight checks.
* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `project_id` INTEGER (Foreign Key referencing `projects.id`)
* `blend_path` TEXT (Path to the specific `.blend` file)
* `blend_size` INTEGER (File size in bytes)
* `blend_modified_at` REAL (Last modification timestamp)
* `blender_version` TEXT (Detected blender package version)
* `scene_name` TEXT (Active scene name)
* `fps` INTEGER (Target framerate)
* `fps_base` INTEGER (Framerate division ratio)
* `resolution_x` INTEGER (X dimension)
* `resolution_y` INTEGER (Y dimension)
* `resolution_percent` INTEGER (Scale multiplier)
* `render_engine` TEXT (Engine configured, e.g. CYCLES, EEVEE)
* `scan_warnings` TEXT (List of warnings, e.g. missing textures)
* `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

### 3. `jobs`
Maintains queue items.
* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `project_id` INTEGER (Foreign Key referencing `projects.id`)
* `snapshot_id` INTEGER (Foreign Key referencing `snapshots.id`)
* `job_type` TEXT (Determines processing logic: `SINGLE_CAMERA_STILL`, `SINGLE_CAMERA_ANIMATION`)
* `scene_name` TEXT (Name of the target scene)
* `camera_name` TEXT (Target camera)
* `frame_start` INTEGER (Starting frame)
* `frame_end` INTEGER (Ending frame)
* `output_root` TEXT (Folder where output goes)
* `output_pattern` TEXT (Path to the target `.blend` file. Historically named `output_pattern` in SQLite but used as `blend_path` in python runner scripts)
* `profile` TEXT (Quality configuration: `Draft`, `Client`, `Final`)
* `resolution_percent` INTEGER (Resolution scale)
* `status` TEXT (Current state: `Pending`, `Running`, `Completed`, `Failed`, `Cancelled`)
* `priority` INTEGER DEFAULT 0 (Higher priority jobs execute first)
* `retry_count` INTEGER DEFAULT 0 (Number of attempts made)
* `max_retries` INTEGER DEFAULT 2 (Maximum retries allowed)
* `started_at` TIMESTAMP
* `finished_at` TIMESTAMP
* `duration_seconds` REAL (Process execution time)
* `output_file` TEXT (Absolute path to the final output file / resolved output file)
* `error_summary` TEXT (Log summary of critical render exceptions)
* `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

### 4. `settings`
Key-value storage for app configurations.
* `key` TEXT PRIMARY KEY
* `value` TEXT
