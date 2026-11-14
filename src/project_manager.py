#!/usr/bin/env python3
"""
Service & Project Manager for Touchpad Command Center.
Supports custom command execution, multi-stack management (many-to-many project to stacks),
and active running queries.
"""

import os
import signal
import json
import subprocess
import threading
import time
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "project-hub"
LEGACY_CONFIG_DIR = Path.home() / ".config" / "touchpad-command-center"
if not CONFIG_DIR.exists() and LEGACY_CONFIG_DIR.exists():
    try:
        import shutil
        shutil.move(str(LEGACY_CONFIG_DIR), str(CONFIG_DIR))
        LEGACY_CONFIG_DIR.symlink_to(CONFIG_DIR)
    except Exception:
        CONFIG_DIR = LEGACY_CONFIG_DIR
PROJECTS_FILE = CONFIG_DIR / "projects.json"
STACKS_FILE = CONFIG_DIR / "stacks.json"
APP_CONFIG_FILE = CONFIG_DIR / "app_config.json"

DEFAULT_STACKS = [
    {
        "name": "Core Services",
        "desc": "Backend Services & Local Databases",
        "repo_url": ""
    }
]

DEFAULT_PROJECTS = [
    {
        "id": "database",
        "name": "PostgreSQL Dev Database",
        "stacks": ["Core Services"],
        "group": "Core Services",
        "path": "~/projects/db",
        "url": "",
        "run_cmd": "docker-compose up -d",
        "stop_cmd": "docker-compose down",
        "build_cmd": "docker-compose up -d --build",
        "desc": "Local PostgreSQL 15 Container",
        "open_vscode": False
    },
    {
        "id": "backend_api",
        "name": "Backend API",
        "stacks": ["Core Services"],
        "group": "Core Services",
        "path": "~/projects/api",
        "url": "http://localhost:8000/docs",
        "run_cmd": "npm run dev",
        "stop_cmd": "pkill -f 'node'",
        "build_cmd": "npm run build",
        "desc": "REST API Service",
        "open_vscode": False
    }
]

class ProjectManager:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.app_config = self.load_app_config()
        self.stacks = self.load_stacks()
        self.projects = self.load_projects()
        self.logs_cache = {}
        self.active_processes = {}  # {proj_id: subprocess.Popen}

    def load_app_config(self):
        if APP_CONFIG_FILE.exists():
            try:
                with open(APP_CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {"app_title": "Project Hub"}

    def save_app_config(self, cfg=None):
        if cfg is not None:
            self.app_config = cfg
        with open(APP_CONFIG_FILE, "w") as f:
            json.dump(self.app_config, f, indent=2)

    def get_app_title(self):
        return self.app_config.get("app_title", "Project Hub")

    def set_app_title(self, title):
        title = title.strip() or "Project Hub"
        self.app_config["app_title"] = title
        self.save_app_config()
        return title

    def resolve_path(self, p):
        """Resolves path with case-insensitive fallback (e.g. /work vs /Work)"""
        if not p:
            return Path.home()
        path = Path(p).expanduser()
        if path.exists():
            return path
        
        # Check /Work vs /work case variance
        p_str = str(p)
        if p_str.startswith("/work"):
            alt = Path("/Work" + p_str[5:])
            if alt.exists():
                return alt
        elif p_str.startswith("/Work"):
            alt = Path("/work" + p_str[5:])
            if alt.exists():
                return alt
        return path

    # ------------------ Stack Persistence & Management ------------------
    def load_stacks(self):
        if not STACKS_FILE.exists():
            # Check existing projects file for existing group names
            initial_stacks = []
            if PROJECTS_FILE.exists():
                try:
                    with open(PROJECTS_FILE, "r") as f:
                        data = json.load(f)
                        for item in data:
                            st_list = item.get("stacks") or ([item.get("group")] if item.get("group") else [])
                            for st in st_list:
                                if st and st not in [s["name"] for s in initial_stacks]:
                                    initial_stacks.append({"name": st, "desc": ""})
                except Exception:
                    pass
            if not initial_stacks:
                initial_stacks = list(DEFAULT_STACKS)
            self.save_stacks(initial_stacks)
            return initial_stacks
        
        try:
            with open(STACKS_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    return data
                return list(DEFAULT_STACKS)
        except Exception:
            return list(DEFAULT_STACKS)

    def save_stacks(self, stacks=None):
        if stacks is not None:
            self.stacks = stacks
        with open(STACKS_FILE, "w") as f:
            json.dump(self.stacks, f, indent=2)

    def get_stacks(self):
        return list(self.stacks)

    def get_stack_names(self):
        return [s.get("name") for s in self.stacks if s.get("name")]

    def get_stack(self, name):
        name = name.strip()
        return next((s for s in self.stacks if s.get("name") == name), None)

    def create_stack(self, name, desc="", repo_url=""):
        name = name.strip()
        if not name:
            return None
        existing = next((s for s in self.stacks if s.get("name") == name), None)
        if existing:
            if desc is not None:
                existing["desc"] = desc.strip()
            if repo_url is not None:
                existing["repo_url"] = repo_url.strip()
            self.save_stacks()
            return existing
        
        new_stack = {"name": name, "desc": desc.strip(), "repo_url": (repo_url or "").strip()}
        self.stacks.append(new_stack)
        self.save_stacks()
        return new_stack

    def update_stack(self, old_name, new_name=None, desc=None, repo_url=None):
        old_name = old_name.strip()
        s = next((st for st in self.stacks if st.get("name") == old_name), None)
        if not s:
            return None
        if new_name is not None and new_name.strip() and new_name.strip() != old_name:
            self.rename_stack(old_name, new_name.strip())
            s = next((st for st in self.stacks if st.get("name") == new_name.strip()), s)
        if desc is not None:
            s["desc"] = desc.strip()
        if repo_url is not None:
            s["repo_url"] = repo_url.strip()
        self.save_stacks()
        return s

    def detect_stack_repo(self, stack_name):
        s = self.get_stack(stack_name)
        if s and s.get("repo_url"):
            return s.get("repo_url")
        
        member_paths = [
            self.resolve_path(p.get("path"))
            for p in self.projects
            if stack_name in p.get("stacks", []) and p.get("path")
        ]
        for p in member_paths:
            for d in [p, p.parent]:
                if (d / ".git").exists():
                    try:
                        res = subprocess.run(
                            ["git", "config", "--get", "remote.origin.url"],
                            cwd=str(d), capture_output=True, text=True, timeout=1.0
                        )
                        if res.returncode == 0 and res.stdout.strip():
                            raw = res.stdout.strip()
                            if raw.startswith("git@"):
                                parts = raw.split(":", 1)
                                if len(parts) == 2:
                                    host = parts[0].replace("git@", "")
                                    rem = parts[1].rstrip(".git")
                                    return f"https://{host}/{rem}"
                            return raw
                    except Exception:
                        pass
        return ""

    def rename_stack(self, old_name, new_name):
        old_name = old_name.strip()
        new_name = new_name.strip()
        if not new_name or old_name == new_name:
            return
        for s in self.stacks:
            if s.get("name") == old_name:
                s["name"] = new_name
        for p in self.projects:
            stacks = p.get("stacks", [])
            if old_name in stacks:
                p["stacks"] = [new_name if st == old_name else st for st in stacks]
            if p.get("group") == old_name:
                p["group"] = new_name
        self.save_stacks()
        self.save_projects()

    def delete_stack(self, name):
        name = name.strip()
        self.stacks = [s for s in self.stacks if s.get("name") != name]
        for p in self.projects:
            stacks = p.get("stacks", [])
            if name in stacks:
                p["stacks"] = [st for st in stacks if st != name]
                p["group"] = p["stacks"][0] if p["stacks"] else "Default"
        self.save_stacks()
        self.save_projects()

    def add_project_to_stack(self, proj_id, stack_name):
        stack_name = stack_name.strip()
        if not stack_name:
            return
        if stack_name not in self.get_stack_names():
            self.create_stack(stack_name)
        for p in self.projects:
            if p.get("id") == proj_id:
                stacks = p.get("stacks", [])
                if stack_name not in stacks:
                    stacks.append(stack_name)
                    p["stacks"] = stacks
                    p["group"] = stacks[0]
        self.save_projects()

    def remove_project_from_stack(self, proj_id, stack_name):
        stack_name = stack_name.strip()
        for p in self.projects:
            if p.get("id") == proj_id:
                stacks = p.get("stacks", [])
                if stack_name in stacks:
                    p["stacks"] = [st for st in stacks if st != stack_name]
                    p["group"] = p["stacks"][0] if p["stacks"] else "Default"
        self.save_projects()

    # ------------------ Project Persistence & Management ------------------
    def load_projects(self):
        if not PROJECTS_FILE.exists():
            self.save_projects(DEFAULT_PROJECTS)
            return list(DEFAULT_PROJECTS)
        try:
            with open(PROJECTS_FILE, "r") as f:
                data = json.load(f)
                if not data:
                    data = list(DEFAULT_PROJECTS)

                # Ensure all have "stacks" array and "group" string
                all_stack_names = set(self.get_stack_names())
                dirty = False
                for item in data:
                    st_val = item.get("stacks")
                    if not st_val or not isinstance(st_val, list):
                        grp = item.get("group")
                        if grp:
                            item["stacks"] = [grp.strip()]
                        else:
                            item["stacks"] = ["Default"]
                        dirty = True
                    # Clean empty entries
                    cleaned = [s.strip() for s in item["stacks"] if s and s.strip()]
                    if not cleaned:
                        cleaned = ["Default"]
                    if cleaned != item.get("stacks"):
                        dirty = True
                    item["stacks"] = cleaned
                    item["group"] = item["stacks"][0]
                    item["open_vscode"] = bool(item.get("open_vscode", False))

                    # Auto-register stack if not already in stacks list
                    for st in item["stacks"]:
                        if st not in all_stack_names:
                            self.stacks.append({"name": st, "desc": ""})
                            all_stack_names.add(st)
                            dirty = True
                
                if dirty:
                    self.save_projects(data)
                    self.save_stacks()
                return data
        except Exception:
            return list(DEFAULT_PROJECTS)

    def get_projects(self):
        return self.load_projects()

    def save_projects(self, projects=None):
        if projects is not None:
            self.projects = projects
        with open(PROJECTS_FILE, "w") as f:
            json.dump(self.projects, f, indent=2)

    def get_groups(self):
        """Backward compatible group list alias for get_stack_names"""
        return self.get_stack_names() or ["Default"]

    def rename_group(self, old_name, new_name):
        """Backward compatible alias for rename_stack"""
        self.rename_stack(old_name, new_name)

    def rename_project(self, proj_id, new_name):
        new_name = new_name.strip()
        if not new_name:
            return False
        for p in self.projects:
            if p.get("id") == proj_id:
                p["name"] = new_name
                self.save_projects()
                return True
        return False

    def toggle_project_vscode(self, proj_id, enabled):
        for p in self.projects:
            if p.get("id") == proj_id:
                p["open_vscode"] = bool(enabled)
        self.save_projects()

    def launch_vscode(self, path):
        if not path:
            return False
        resolved = self.resolve_path(path)
        if resolved.exists():
            try:
                subprocess.Popen(["code", str(resolved)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception as e:
                print(f"Error launching VS Code: {e}")
                return False
        return False

    def add_or_update_project(self, name, path, stacks=None, group=None, url="", run_cmd="", stop_cmd="", build_cmd="", desc="", open_vscode=False, proj_id=None):
        name = name.strip()
        if not proj_id:
            proj_id = name.lower().replace(" ", "_")

        # Resolve stacks list
        if stacks is None:
            if group:
                if isinstance(group, list):
                    stacks = group
                else:
                    stacks = [s.strip() for s in group.split(",") if s.strip()]
            else:
                stacks = ["Default"]
        elif isinstance(stacks, str):
            stacks = [s.strip() for s in stacks.split(",") if s.strip()]

        clean_stacks = [s.strip() for s in stacks if s and s.strip()]
        if not clean_stacks:
            clean_stacks = ["Default"]

        # Ensure all assigned stacks are registered in self.stacks
        existing_stack_names = self.get_stack_names()
        for st in clean_stacks:
            if st not in existing_stack_names:
                self.create_stack(st)

        existing = next((p for p in self.projects if p.get("id") == proj_id), None)
        item = {
            "id": proj_id,
            "name": name,
            "stacks": clean_stacks,
            "group": clean_stacks[0],
            "path": path,
            "url": url.strip(),
            "run_cmd": run_cmd.strip(),
            "stop_cmd": stop_cmd.strip(),
            "build_cmd": build_cmd.strip(),
            "desc": desc.strip(),
            "open_vscode": bool(open_vscode)
        }
        if existing:
            self.projects[self.projects.index(existing)] = item
        else:
            self.projects.append(item)

        self.save_projects()
        return item

    def delete_project(self, proj_id):
        self.projects = [p for p in self.projects if p.get("id") != proj_id]
        self.save_projects()

    def check_status(self, proj):
        """Determines if the service is currently running"""
        proj_id = proj.get("id")
        
        # 1. Check if we have an active live process
        proc = self.active_processes.get(proj_id)
        if proc and proc.poll() is None:
            return "RUNNING"

        proj_path = self.resolve_path(proj.get("path", ""))

        # 2. Check docker-compose running status in directory
        if proj_path.exists():
            try:
                res = subprocess.run(
                    ["docker-compose", "ps", "--status", "running", "-q"],
                    cwd=str(proj_path), capture_output=True, text=True, timeout=1.5
                )
                if res.returncode == 0 and res.stdout.strip():
                    return "RUNNING"
            except Exception:
                pass
            try:
                res = subprocess.run(
                    ["docker", "compose", "ps", "--status", "running", "-q"],
                    cwd=str(proj_path), capture_output=True, text=True, timeout=1.5
                )
                if res.returncode == 0 and res.stdout.strip():
                    return "RUNNING"
            except Exception:
                pass

        # 3. Check docker container name match
        pname = proj.get("name", "").lower().replace(" ", "")
        try:
            res = subprocess.run(
                ["docker", "ps", "--filter", f"name={pname}", "--filter", "status=running", "-q"],
                capture_output=True, text=True, timeout=1.5
            )
            if res.returncode == 0 and res.stdout.strip():
                return "RUNNING"
        except Exception:
            pass

        return "STOPPED"

    def execute_action(self, proj_id, action, on_done_callback=None):
        proj = next((p for p in self.projects if p.get("id") == proj_id), None)
        if not proj:
            if on_done_callback:
                on_done_callback(False, "Service not found")
            return

        proj_path = self.resolve_path(proj.get("path", ""))
        cwd = str(proj_path) if proj_path.exists() else None

        if action == "run":
            cmd_str = proj.get("run_cmd", "./up.sh")
            open_vscode = proj.get("open_vscode", False)
            self._start_service_async(proj_id, proj.get("name"), cmd_str, cwd, on_done_callback, open_vscode=open_vscode)
        elif action == "stop":
            cmd_str = proj.get("stop_cmd", "./down.sh")
            self._stop_service_async(proj_id, proj.get("name"), cmd_str, cwd, on_done_callback)
        elif action == "build":
            cmd_str = proj.get("build_cmd", "docker-compose up --build")
            self._build_service_async(proj_id, proj.get("name"), cmd_str, cwd, on_done_callback)

    def execute_stack_action(self, stack_name, action, on_done_callback=None):
        """Runs the action on all projects belonging to the stack"""
        targets = [p for p in self.projects if stack_name in p.get("stacks", [])]
        if not targets:
            targets = [p for p in self.projects if (p.get("group") or "Default") == stack_name]
        
        if not targets:
            if on_done_callback:
                on_done_callback(False, f"No services found in stack '{stack_name}'")
            return

        def stack_worker():
            # If starting, put databases first (mysql/postgres), then web app
            if action == "run":
                sorted_targets = sorted(
                    targets,
                    key=lambda p: 0 if any(db in p.get("name", "").lower() for db in ["mysql", "postgres", "redis", "mongo", "db"]) else 1
                )
            else:
                # If stopping, reverse
                sorted_targets = list(reversed(targets))

            for p in sorted_targets:
                pid = p.get("id")
                proj_path = self.resolve_path(p.get("path", ""))
                cwd = str(proj_path) if proj_path.exists() else None

                if action == "run":
                    cmd_str = p.get("run_cmd", "./up.sh")
                    open_vscode = p.get("open_vscode", False)
                    self._start_service_async(pid, p.get("name"), cmd_str, cwd, None, open_vscode=open_vscode)
                    time.sleep(1.0)
                elif action == "stop":
                    cmd_str = p.get("stop_cmd", "./down.sh")
                    self._stop_service_async(pid, p.get("name"), cmd_str, cwd, None)
                    time.sleep(0.5)

            time.sleep(1.0)
            if on_done_callback:
                on_done_callback(True, f"Stack {action} completed for {stack_name}")

        threading.Thread(target=stack_worker, daemon=True).start()

    def execute_group_action(self, group_name, action, on_done_callback=None):
        """Backward compatibility alias for execute_stack_action"""
        self.execute_stack_action(group_name, action, on_done_callback)

    def _start_service_async(self, proj_id, name, cmd_str, cwd, callback, open_vscode=False):
        def worker():
            log_lines = [f"=== Starting {name} ==="]
            log_lines.append(f"Directory: {cwd}")
            log_lines.append(f"Command: {cmd_str}\n")
            
            if cmd_str.startswith("./") and cwd:
                script_path = Path(cwd) / cmd_str[2:].split()[0]
                if script_path.exists():
                    os.chmod(script_path, 0o755)

            try:
                proc = subprocess.Popen(
                    cmd_str,
                    shell=True,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    preexec_fn=os.setsid,
                    env=os.environ.copy()
                )
                self.active_processes[proj_id] = proc
                
                def read_output():
                    for line in iter(proc.stdout.readline, ''):
                        log_lines.append(line.rstrip())
                        self.logs_cache[proj_id] = "\n".join(log_lines[-200:])
                    proc.stdout.close()
                
                threading.Thread(target=read_output, daemon=True).start()

                # If open_vscode is requested, launch VS Code for this project folder
                if open_vscode and cwd:
                    self.launch_vscode(cwd)
                
                time.sleep(1.5)
                self.logs_cache[proj_id] = "\n".join(log_lines)
                if callback:
                    callback(True, f"{name} started")
            except Exception as e:
                err = f"Failed to start: {e}"
                log_lines.append(err)
                self.logs_cache[proj_id] = "\n".join(log_lines)
                if callback:
                    callback(False, err)

        threading.Thread(target=worker, daemon=True).start()

    def _stop_service_async(self, proj_id, name, cmd_str, cwd, callback):
        def worker():
            log_lines = self.logs_cache.get(proj_id, "").split("\n")
            log_lines.append(f"\n=== Stopping {name} ===")

            # 1. Terminate running process group
            proc = self.active_processes.pop(proj_id, None)
            if proc:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    time.sleep(0.5)
                except Exception:
                    pass

            # 2. Run stop command
            actual_cmd = cmd_str
            if cmd_str.startswith("./") and cwd:
                script_file = Path(cwd) / cmd_str[2:].split()[0]
                if not script_file.exists():
                    actual_cmd = "docker-compose down"
                else:
                    os.chmod(script_file, 0o755)

            try:
                subprocess.run(
                    actual_cmd,
                    shell=True,
                    cwd=cwd,
                    timeout=30,
                    capture_output=True,
                    text=True,
                    env=os.environ.copy()
                )
                log_lines.append(f"Executed: {actual_cmd}")
            except Exception as e:
                log_lines.append(f"Stop command warning: {e}")

            self.logs_cache[proj_id] = "\n".join(log_lines[-200:])
            time.sleep(1.0)
            if callback:
                callback(True, f"{name} stopped")

        threading.Thread(target=worker, daemon=True).start()

    def _build_service_async(self, proj_id, name, cmd_str, cwd, callback):
        def worker():
            log_lines = [f"=== Building {name} ==="]
            log_lines.append(f"Command: {cmd_str}\n")
            try:
                proc = subprocess.Popen(
                    cmd_str,
                    shell=True,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    preexec_fn=os.setsid,
                    env=os.environ.copy()
                )
                self.active_processes[proj_id] = proc
                
                for line in iter(proc.stdout.readline, ''):
                    log_lines.append(line.rstrip())
                    self.logs_cache[proj_id] = "\n".join(log_lines[-200:])
                proc.stdout.close()
                proc.wait()
                
                if callback:
                    callback(True, f"{name} build finished")
            except Exception as e:
                log_lines.append(f"Build error: {e}")
                self.logs_cache[proj_id] = "\n".join(log_lines)
                if callback:
                    callback(False, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def get_logs(self, proj_id, tail=200):
        proj = next((p for p in self.projects if p.get("id") == proj_id), None)
        cached = self.logs_cache.get(proj_id, "").strip()
        docker_logs = ""

        if proj:
            p_path = self.resolve_path(proj.get("path", ""))
            if p_path.exists():
                compose_files = ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]
                has_compose = any((p_path / cf).exists() for cf in compose_files)
                if has_compose:
                    try:
                        res = subprocess.run(
                            ["docker-compose", "logs", f"--tail={tail}", "--no-color"],
                            cwd=str(p_path), capture_output=True, text=True, timeout=2.5
                        )
                        if res.returncode == 0 and res.stdout.strip():
                            docker_logs = res.stdout.strip()
                    except Exception:
                        pass
                    
                    if not docker_logs:
                        try:
                            res = subprocess.run(
                                ["docker", "compose", "logs", f"--tail={tail}", "--no-color"],
                                cwd=str(p_path), capture_output=True, text=True, timeout=2.5
                            )
                            if res.returncode == 0 and res.stdout.strip():
                                docker_logs = res.stdout.strip()
                        except Exception:
                            pass

        if docker_logs:
            if cached and cached != docker_logs:
                return f"{cached}\n\n=== Live Container Logs (tail {tail}) ===\n{docker_logs}"
            return docker_logs

        if cached:
            return cached

        proc = self.active_processes.get(proj_id)
        if proc and proc.poll() is None:
            return f"Process is running (PID {proc.pid}), waiting for output stream..."

        return "No logs recorded for this service yet.\nStart the service or run a build to capture live output."

    def clear_logs(self, proj_id):
        self.logs_cache[proj_id] = ""
