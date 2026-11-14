#!/usr/bin/env python3
"""
Docker Manager module for Touchpad Command Center.
Discovers containers and extracts mapped web ports for browser redirect.
"""

import json
import re
import subprocess
import threading

class DockerManager:
    def __init__(self):
        pass

    def list_containers(self):
        """Fetches all containers on the host with extracted redirect URLs"""
        cmd = ["docker", "ps", "-a", "--format", "{{json .}}"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=3)
            containers = []
            for line in res.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        c = json.loads(line)
                        # Extract redirect URL from Ports string or inspect
                        url = self._extract_url_from_ports(c.get("Ports", ""))
                        if not url:
                            url = self._inspect_container_url(c.get("ID"))
                        c["url"] = url
                        c["type"] = "docker"
                        containers.append(c)
                    except Exception:
                        pass
            return containers
        except Exception:
            return []

    def _extract_url_from_ports(self, ports_str):
        # e.g. 0.0.0.0:8080->80/tcp or 127.0.0.1:3000->3000/tcp
        m = re.search(r':(\d+)->', ports_str)
        if m:
            port = m.group(1)
            return f"http://localhost:{port}"
        return ""

    def _inspect_container_url(self, cid):
        try:
            cmd = ["docker", "inspect", cid, "--format", "{{json .HostConfig.PortBindings}}"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=1)
            if res.returncode == 0 and res.stdout.strip() and res.stdout.strip() != "null":
                bindings = json.loads(res.stdout.strip())
                for port_proto, host_list in bindings.items():
                    if host_list and isinstance(host_list, list):
                        host_port = host_list[0].get("HostPort")
                        if host_port:
                            return f"http://localhost:{host_port}"
                        # If container port is e.g. 8025 or 3000, fallback
                        container_port = port_proto.split("/")[0]
                        if container_port in ["3000", "8080", "8000", "8025", "5173", "80"]:
                            return f"http://localhost:{container_port}"
        except Exception:
            pass
        return ""

    def execute_container_action(self, cid, action, callback=None):
        def worker():
            try:
                res = subprocess.run(["docker", action, cid], capture_output=True, text=True, check=True)
                if callback:
                    callback(True, res.stdout.strip())
            except subprocess.CalledProcessError as e:
                err = e.stderr.strip() if e.stderr else str(e)
                if callback:
                    callback(False, err)
            except Exception as e:
                if callback:
                    callback(False, str(e))
        threading.Thread(target=worker, daemon=True).start()

    def get_container_logs(self, cid, lines=100):
        try:
            res = subprocess.run(["docker", "logs", "--tail", str(lines), cid], capture_output=True, text=True, timeout=5)
            return res.stdout or res.stderr or "No logs available"
        except Exception as e:
            return f"Error retrieving logs: {e}"
