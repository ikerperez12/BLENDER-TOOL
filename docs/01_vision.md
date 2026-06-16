# Product Vision - IP Blender Tool

## 🎯 Goal & Core Purpose
IP Blender Tool is built as a lightweight, professional rendering orchestrator for Blender on Windows. It is designed to act as an invisible assistant: providing a simple, minimal UI on the outside, and high levels of automation and error tolerance on the inside. 

Its main purpose is to eliminate repetitive manual rendering and compositing workflows, allowing developers/artists to queue jobs, walk away, and receive automatic versioned deliverables along with status alerts.

---

## 🔍 In-Scope Features
* **Zero-Impact CLI Execution**: Spawns Blender in background subprocesses. Project files are never modified on disk during rendering.
* **Smart Pre-Flight Ingestion**: Parses `.blend` metadata during queue ingestion rather than mid-render, warning users of missing assets or textures.
* **Fluid UI Threading**: Runs renders on isolated background threads, keeping table grids and logs scrollable.
* **Dynamic Post-Processing**: Swaps composites inside montage projects automatically, and compiles animation sequences to MP4 via FFmpeg.
* **Process Abort Safety**: Guarantees termination of leaked subprocesses on cancel.
* **Notification Outbox**: Queues Telegram/Discord notifications safely, ensuring network connectivity problems never affect rendering execution.

---

## 🚫 Out of Scope (Future Phases)
To maintain the app's lightweight profile and portability, the following are explicitly excluded from Phase 1:
* **Distributed Render Farms**: No local peer-to-peer or remote network rendering.
* **Cloud Integration**: No cloud storage uploads, AWS integrations, or online databases.
* **Material/Texture Editors**: The app does not modify scenes, lights, meshes, or materials.
* **Multi-user authorization**: A local-only, single-user system requiring no logins or credentials database.
