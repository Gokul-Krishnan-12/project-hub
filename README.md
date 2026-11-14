# ⚡ Project Hub

<div align="center">

![Linux](https://img.shields.io/badge/Platform-Linux%20%7C%20Wayland%20%7C%20X11-orange?logo=linux)
![Desktop](https://img.shields.io/badge/Desktop-GNOME%20%7C%20KDE%20%7C%20Sway%20%7C%20i3-blue)
![UI](https://img.shields.io/badge/UI-GTK4%20%2B%20Python%203-green?logo=gnome)
![License](https://img.shields.io/badge/License-MIT-purple)

**A spotlight-style desktop developer command center & local environment manager for Linux.**  
Orchestrate microservices, Docker compose stacks, and monorepos from a single keyboard-driven interface.

Triggered instantly with **`Super + K`**, **`Ctrl + Alt + P`**, or a **mousepad edge-swipe**.

</div>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Usage Guide](#-usage-guide)
  - [Keyboard Shortcuts](#keyboard-shortcuts)
  - [Touchpad Gesture](#touchpad-gesture)
  - [Terminal CLI](#terminal-cli)
- [Configuration Reference](#-configuration-reference)
  - [Projects Configuration (`projects.json`)](#projects-configuration-projectsjson)
  - [Stacks Configuration (`stacks.json`)](#stacks-configuration-stacksjson)
- [Troubleshooting & FAQ](#-troubleshooting--faq)
- [License](#-license)

---

## 🎯 Overview

Modern local development often requires juggling multiple services: background databases (PostgreSQL, Redis, MySQL), microservice APIs, message queues, and client frontends. Developers end up with dozens of terminal tabs, forgotten background containers, and manual command memorization.

**Project Hub** consolidates your local development ecosystem into a floating, lightweight command center:
* **Start and Stop** individual services or entire interconnected stacks in dependency order.
* **Stream live Docker & subprocess logs** with syntax highlighting and regex search.
* **Auto-launch VS Code workspaces** for individual services or root monorepos.
* **Direct browser redirect** to localhost web applications.
* **Inspect and manage** your development environment in milliseconds without leaving your active workflow.

---

## 🌟 Key Features

### ⊞ Grouped Stacks & Monorepo Support
* **Visual Stack Enclosure**: Group interdependent services together (e.g. `Backend Microservices`, `Core Databases`, `E-Commerce Stack`).
* **Monorepo / Turborepo Root Link**: Assign a repository URL or local path to any stack group (e.g. `https://github.com/org/repo` or `~/projects/monorepo`).
* **One-Click Orchestration**:
  * **`▶ Start All`**: Boots all member services in smart order (databases first, then applications) and automatically opens the monorepo root in Visual Studio Code.
  * **`⏹ Stop All`**: Gracefully terminates services in reverse order.
* **Collapsible Accordions**: Keep your workspace clean with quick expand/collapse group cards.

### 📁 Dual View Navigation
* **Grouped Stacks View**: Structured tree view grouping projects into their logical domain stacks.
* **All Projects (Flat) View**: Flat, sortable inventory of every configured service on your machine with stack tags and direct controls.
* **Status Filter Badges**: Instant 1-click filtering by `All`, `● Running`, or `○ Stopped`.

### 💻 Automatic VS Code Workspace Launch
* **"Open on Start" Toggle**: Enable the checkbox on any service card or configuration modal.
* **Automated Editor Boot**: Starting the service automatically opens its directory in Visual Studio Code (`code <path>`).
* **Instant Action Button**: Dedicated `💻 Code` action button to open any project in VS Code at any time.

### 📋 Developer-Grade Live Logs Terminal
* **Real Subprocess & Container Output**: Automatically queries live `docker-compose logs --tail=... --no-color` and process stdout/stderr streams.
* **Colorized Syntax Highlighting**:
  * 🔴 **Errors / Exceptions** highlighted in bold red (`#f87171`).
  * 🟡 **Warnings / Deprecations** highlighted in amber (`#fbbf24`).
  * 🟢 **Success / Ready / Connected** highlighted in emerald green (`#34d399`).
  * 🔵 **Info / Protocol** highlighted in sky blue (`#38bdf8`).
  * ⚪ **Timestamps & IDs** formatted in muted grey (`#64748b`).
* **Interactive Live Tail**: Auto-refreshes every 2 seconds with background polling and instant pause toggle.
* **Log Level Filtering**: Filter output by `All Logs`, `⛔ Errors`, `⚠️ Warnings`, or `ℹ Info`.
* **Instant Keyword Search**: Filter lines as you type with real-time matched line counts.
* **Developer Utilities**: 1-click **Copy All** to system clipboard, **Clear**, and **Scroll to Bottom**.

### 🔍 Unified Command Palette & Search
* Instant search across project names, stack groups, filesystem paths, ports, and redirect URLs.
* Press `Escape` to instantly dismiss the launcher.

### 📂 Smart Filesystem Folder Auto-Detection
* Built-in file browser automatically detects:
  * Project names from directory names.
  * `docker-compose.yml` or `docker-compose.yaml` build and run commands.
  * Local scripts like `./up.sh`, `./down.sh`, `start.sh`, `Makefile`.
  * Node.js `package.json` scripts (`npm run dev`, `pnpm dev`, `yarn dev`).
  * Web redirect URLs from exposed container ports.

---

## 🖥️ Architecture

```
                      TRIGGER MECHANISMS
       ┌───────────────────────┬──────────────────────┐
       │                       │                      │
  Super + K (HotKey)     Touchpad Edge-Swipe    CLI (project-hub)
       │                       │                      │
       └───────────────────────┼──────────────────────┘
                               ▼
                   ┌────────────────────────┐
                   │   GTK4 Application     │
                   │     (Project Hub)      │
                   └───────────┬────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
   ┌─────────────────┐                  ┌───────────────────┐
   │ Project Manager │                  │  Docker Manager   │
   │ (Process Runner)│                  │(Compose / Engine) │
   └────────┬────────┘                  └─────────┬─────────┘
            │                                     │
   ┌────────┴────────┐                  ┌─────────┴─────────┐
   ▼                 ▼                  ▼                   ▼
Subprocesses     VS Code Workspace   Containers     Live Log Stream
(Node, Go, Py)  (code /path/to/repo) (Postgres, DB) (stdout / stderr)
```

---

## 📦 Prerequisites

Project Hub runs on any modern Linux distribution with Python 3 and GTK4 installed:

### Ubuntu / Debian / Pop!_OS
```bash
sudo apt update
sudo apt install python3 python3-pip python3-gi gir1.2-gtk-4.0 adwaita-icon-theme
```

### Fedora
```bash
sudo dnf install python3 python3-gobject gtk4 adwaita-icon-theme
```

### Arch Linux / Manjaro
```bash
sudo pacman -S python python-gobject gtk4 adwaita-icon-theme
```

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone git@github.com:Gokul-Krishnan-12/project-hub.git
cd project-hub
```
*(Or via HTTPS: `git clone https://github.com/Gokul-Krishnan-12/project-hub.git`)*

### 2. Run the Setup Script
```bash
./setup.sh
```

The setup script will automatically:
1. Make all execution scripts and daemons executable.
2. Install the desktop launcher (`project-hub.desktop`) in `~/.local/share/applications/`.
3. Create the `project-hub` CLI symlink in `~/.local/bin/`.
4. Configure GNOME global keyboard shortcuts to **`Super + K`** and **`Ctrl + Alt + P`**.
5. Set up the systemd user service for touchpad edge-swipe gestures.

---

## 🎮 Usage Guide

### Keyboard Shortcuts
* **`Super + K`** or **`Ctrl + Alt + P`**: Toggle Project Hub window from anywhere.
* **`Escape`**: Dismiss the window.
* **`Enter`**: Submit search or confirm dialogs.

### Touchpad Gesture
Swipe inward from the **rightmost edge of your laptop touchpad** to toggle the command center.

To test the gesture sensor interactively in terminal:
```bash
python3 src/gesture_daemon.py --test
```

To enable the gesture daemon as a background service on login:
```bash
systemctl --user enable --now touchpad-gesture
```

### Terminal CLI
You can launch Project Hub directly from any terminal:
```bash
project-hub
```
Or run the script directly:
```bash
./run.sh
```

---

## 🛠️ Configuration Reference

All persistent data is stored in standard JSON format under `~/.config/project-hub/`:

### Projects Configuration (`projects.json`)
Location: `~/.config/project-hub/projects.json`

```json
[
  {
    "id": "postgres_db",
    "name": "PostgreSQL Database",
    "stacks": ["Core Services"],
    "group": "Core Services",
    "path": "~/projects/infrastructure/postgres",
    "url": "http://localhost:5432",
    "run_cmd": "docker-compose up -d",
    "stop_cmd": "docker-compose down",
    "build_cmd": "docker-compose up -d --build",
    "desc": "PostgreSQL 15 Local Dev Database",
    "open_vscode": false
  },
  {
    "id": "backend_api",
    "name": "Backend REST API",
    "stacks": ["Core Services", "API Gateway"],
    "group": "Core Services",
    "path": "~/projects/backend-api",
    "url": "http://localhost:8000/docs",
    "run_cmd": "npm run dev",
    "stop_cmd": "pkill -f 'node api'",
    "build_cmd": "npm run build",
    "desc": "Fastify + TypeScript API",
    "open_vscode": true
  },
  {
    "id": "web_frontend",
    "name": "Web Dashboard",
    "stacks": ["Frontend Apps"],
    "group": "Frontend Apps",
    "path": "~/projects/web-dashboard",
    "url": "http://localhost:3000",
    "run_cmd": "pnpm dev",
    "stop_cmd": "pkill -f 'next-server'",
    "build_cmd": "pnpm build",
    "desc": "Next.js 14 Frontend Application",
    "open_vscode": true
  }
]
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `string` | Unique identifier for the service. |
| `name` | `string` | Human-readable title displayed in the dashboard. |
| `stacks` | `array` | List of group/stack names this project belongs to (many-to-many). |
| `path` | `string` | Absolute or home-relative path to the project directory. |
| `url` | `string` | Optional URL (e.g. `http://localhost:3000`) for 1-click browser redirection. |
| `run_cmd` | `string` | Command to start the service (e.g. `./up.sh` or `docker-compose up -d`). |
| `stop_cmd` | `string` | Command to stop the service (e.g. `docker-compose down`). |
| `build_cmd` | `string` | Command to build/rebuild the service (e.g. `docker-compose up --build`). |
| `open_vscode` | `boolean` | If `true`, automatically opens the project in VS Code on service start. |

---

### Stacks Configuration (`stacks.json`)
Location: `~/.config/project-hub/stacks.json`

```json
[
  {
    "name": "Core Services",
    "desc": "Databases, Cache, and Message Brokers",
    "repo_url": ""
  },
  {
    "name": "Microservices Monorepo",
    "desc": "Turborepo Microservices & Shared Packages",
    "repo_url": "https://github.com/org/microservices-monorepo"
  }
]
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | `string` | Name of the stack group. |
| `desc` | `string` | Short description displayed in the group header. |
| `repo_url` | `string` | Optional Git URL or local folder path. If configured, opens in VS Code automatically when **`Start All`** is triggered. |

---

## ❓ Troubleshooting & FAQ

#### Q: How do I change the global keyboard shortcut?
Open GNOME Settings &rarr; **Keyboard** &rarr; **Keyboard Shortcuts** &rarr; **Custom Shortcuts**, and modify the entry named **`Project Hub`**.  
On KDE, XFCE, or i3/Sway, bind your preferred key combination to run the command `project-hub`.

#### Q: The touchpad swipe gesture isn't detecting my swipes.
Make sure your user is in the Linux `input` group to access hardware event devices without root:
```bash
sudo usermod -a -G input $USER
newgrp input
```
Then verify device detection by running:
```bash
python3 src/gesture_daemon.py --test
```

#### Q: How does Project Hub find my monorepo folder when given a GitHub URL?
When a Git repository URL (e.g. `https://github.com/org/repo`) is configured on a stack, Project Hub inspects the directories of all member projects in that stack, walks up their parent folders, and matches the repository name against your local filesystem.

---

## 📄 License

Distributed under the [MIT License](LICENSE).  
Developed with ❤️ by [Gokul Krishnan](https://github.com/Gokul-Krishnan-12).
