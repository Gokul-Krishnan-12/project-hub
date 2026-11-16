#!/usr/bin/env python3
"""
Command Center — Modern Desktop Developer Tool UI
Inspired by Docker Desktop, Linear, and Raycast.

Architecture & Features:
- Clean, compact dark theme with subtle elevation and borders
- Dual Navigation Modes: Grouped Stacks View and Full Projects (Flat) View
- Visual group containers with collapsible headers & one-click lifecycle controls
- Rich service rows with intelligent hierarchy (primary Start/Stop, link Open App, secondary actions)
- In-progress operational feedback (STARTING / STOPPING states)
- Dedicated VS Code integration (Auto-open on start + manual trigger)
- Safe delete confirmation dialogs
- Smart search across groups, services, paths, and URLs
"""

import sys
import os
import re
import subprocess
import threading
import webbrowser
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, GLib, Gio, Pango

from project_manager import ProjectManager
from docker_manager import DockerManager

CSS = """
/* ==========================================================================
   COMMAND CENTER - MODERN DEVELOPER DESIGN SYSTEM (Linear / Docker / Raycast)
   ========================================================================== */

window {
    background-color: #0c0d10;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", "Ubuntu", sans-serif;
}

/* 1. Header Bar */
.app-header {
    background-color: #121418;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    padding: 10px 20px;
}

.brand-icon {
    font-size: 16px;
    padding-right: 2px;
}

.brand-title {
    font-size: 15px;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.3px;
}

.brand-dot {
    color: #ff5722;
    font-weight: 900;
}

.header-stat-pill {
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 9999px;
    padding: 2px 9px;
    font-size: 11px;
    font-weight: 600;
    color: #94a3b8;
}

.header-stat-pill.running {
    background-color: rgba(16, 185, 129, 0.12);
    border-color: rgba(16, 185, 129, 0.28);
    color: #34d399;
}

/* 2. Subheader Toolbar */
.toolbar-box {
    background-color: #0f1115;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding: 8px 20px;
}

/* Segmented View Switcher (Grouped vs Flat) */
.view-switcher-box {
    background-color: #16191f;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 2px;
}

.view-switch-btn {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    color: #94a3b8;
    padding: 4px 12px;
    font-size: 11.5px;
    font-weight: 600;
}

.view-switch-btn:hover {
    color: #f8fafc;
    background-color: rgba(255, 255, 255, 0.04);
}

.view-switch-btn.active {
    background-color: #242932;
    color: #ffffff;
    font-weight: 700;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
}

/* Status Filter Pills */
.filter-pill {
    background-color: transparent;
    border: 1px solid transparent;
    color: #94a3b8;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
}

.filter-pill:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #f1f5f9;
}

.filter-pill.active {
    background-color: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.12);
    color: #ffffff;
}

/* Search Bar */
.search-input {
    background-color: #16191f;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    color: #f8fafc;
    padding: 5px 12px;
    font-size: 12.5px;
    min-width: 250px;
}

.search-input:focus {
    border-color: #ff5722;
    box-shadow: 0 0 0 2px rgba(255, 87, 34, 0.2);
}

/* Header & Action Buttons */
.btn-primary {
    background-color: #ff5722;
    color: #ffffff;
    border: 1px solid #ff5722;
    border-radius: 7px;
    padding: 5px 12px;
    font-size: 11.5px;
    font-weight: 600;
}

.btn-primary:hover {
    background-color: #f4511e;
    border-color: #f4511e;
}

.btn-secondary {
    background-color: #171a20;
    color: #cbd5e1;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 7px;
    padding: 5px 12px;
    font-size: 11.5px;
    font-weight: 500;
}

.btn-secondary:hover {
    background-color: #21252d;
    color: #f8fafc;
    border-color: rgba(255, 255, 255, 0.15);
}

.btn-icon {
    background-color: transparent;
    border: 1px solid transparent;
    color: #94a3b8;
    border-radius: 6px;
    padding: 4px 7px;
}

.btn-icon:hover {
    background-color: rgba(255, 255, 255, 0.07);
    color: #f8fafc;
    border-color: rgba(255, 255, 255, 0.1);
}

.btn-icon-danger:hover {
    background-color: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border-color: rgba(239, 68, 68, 0.3);
}

.btn-icon-subtle {
    background-color: transparent;
    border: 1px solid transparent;
    color: #64748b;
    border-radius: 5px;
    padding: 2px 5px;
    min-height: 20px;
    min-width: 20px;
}

.btn-icon-subtle:hover {
    background-color: rgba(255, 255, 255, 0.08);
    color: #f1f5f9;
    border-color: rgba(255, 255, 255, 0.14);
}

/* Service Actions */
.btn-start {
    background-color: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.28);
    color: #34d399;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
}

.btn-start:hover {
    background-color: #10b981;
    color: #0c0d10;
    border-color: #10b981;
}

.btn-stop {
    background-color: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.28);
    color: #f87171;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
}

.btn-stop:hover {
    background-color: #ef4444;
    color: #ffffff;
    border-color: #ef4444;
}

.btn-in-progress {
    background-color: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.28);
    color: #fbbf24;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
}

.btn-open-url {
    background-color: rgba(255, 87, 34, 0.08);
    border: 1px solid rgba(255, 87, 34, 0.25);
    color: #ff7043;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 600;
    font-family: "JetBrains Mono", monospace;
}

.btn-open-url:hover {
    background-color: #ff5722;
    color: #ffffff;
    border-color: #ff5722;
}

.btn-repo-url {
    background-color: rgba(59, 130, 246, 0.09);
    border: 1px solid rgba(59, 130, 246, 0.28);
    color: #60a5fa;
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 11px;
    font-weight: 500;
    font-family: "JetBrains Mono", monospace;
}

.btn-repo-url:hover {
    background-color: rgba(59, 130, 246, 0.22);
    border-color: rgba(59, 130, 246, 0.5);
    color: #93c5fd;
}

/* Logs Modal Terminal System */
.logs-modal-window {
    background-color: #0c0d10;
}

.logs-modal-header {
    background-color: #121519;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding: 12px 18px;
}

.logs-modal-toolbar {
    background-color: #101216;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding: 8px 18px;
}

.logs-terminal-box {
    background-color: #08090c;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 8px;
    margin: 8px 18px;
}

.logs-terminal-view {
    background-color: #08090c;
    color: #cbd5e1;
    font-family: "JetBrains Mono", "DejaVu Sans Mono", monospace;
    font-size: 11px;
    padding: 10px 14px;
}

.logs-modal-footer {
    background-color: #121519;
    border-top: 1px solid rgba(255, 255, 255, 0.07);
    padding: 10px 18px;
}

.logs-count-pill {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #94a3b8;
    border-radius: 5px;
    padding: 3px 8px;
    font-size: 11px;
    font-family: "JetBrains Mono", monospace;
    font-weight: 500;
}

.logs-live-active {
    background-color: rgba(16, 185, 129, 0.14);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #34d399;
}

.logs-live-active:hover {
    background-color: rgba(16, 185, 129, 0.22);
    border-color: rgba(16, 185, 129, 0.5);
    color: #6ee7b7;
}

.logs-filter-pill {
    background-color: transparent;
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #94a3b8;
    border-radius: 5px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 500;
}

.logs-filter-pill:hover {
    background-color: rgba(255, 255, 255, 0.06);
    color: #f8fafc;
}

.logs-filter-pill.active {
    background-color: rgba(255, 255, 255, 0.14);
    border-color: rgba(255, 255, 255, 0.25);
    color: #ffffff;
    font-weight: 600;
}

/* 3. Group Container Card */
.group-wrapper {
    background-color: #13161a;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    margin: 8px 18px 14px 18px;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.28);
}

.group-header {
    background-color: #171a20;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    padding: 8px 14px;
}

.group-header.collapsed {
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
    border-bottom: none;
}

.group-title {
    font-size: 14.5px;
    font-weight: 600;
    color: #f8fafc;
    letter-spacing: -0.2px;
}

.group-desc {
    font-size: 11px;
    color: #94a3b8;
}

.group-badge {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #94a3b8;
    border-radius: 9999px;
    padding: 1px 8px;
    font-size: 10.5px;
    font-weight: 600;
}

.group-badge.active {
    background-color: rgba(16, 185, 129, 0.12);
    border-color: rgba(16, 185, 129, 0.25);
    color: #34d399;
}

.group-content {
    background-color: #0e1014;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
    padding: 6px 10px 10px 10px;
}

/* 4. Service Row Item (Linear / Docker Desktop style) */
.service-row {
    background-color: #14171c;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 9px 14px;
    margin-top: 6px;
    transition: all 120ms ease-in-out;
}

.service-row:hover {
    background-color: #191c22;
    border-color: rgba(255, 255, 255, 0.12);
}

.service-name {
    font-size: 13.5px;
    font-weight: 600;
    color: #f8fafc;
    letter-spacing: -0.2px;
}

.service-path {
    font-size: 11px;
    color: #94a3b8;
    font-family: "JetBrains Mono", monospace;
}

.service-desc {
    font-size: 11px;
    color: #64748b;
}

.tag-pill {
    background-color: rgba(255, 87, 34, 0.08);
    border: 1px solid rgba(255, 87, 34, 0.2);
    color: #ff7043;
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 10px;
    font-weight: 600;
}

/* Status Badges */
.status-badge-running {
    background-color: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.25);
    color: #34d399;
    border-radius: 5px;
    padding: 1px 6px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.3px;
}

.status-badge-stopped {
    background-color: rgba(113, 113, 122, 0.12);
    border: 1px solid rgba(113, 113, 122, 0.2);
    color: #a1a1aa;
    border-radius: 5px;
    padding: 1px 6px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.3px;
}

.status-badge-starting {
    background-color: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.25);
    color: #fbbf24;
    border-radius: 5px;
    padding: 1px 6px;
    font-size: 10px;
    font-weight: 700;
}

.empty-state-box {
    padding: 30px 20px;
}

.empty-state-title {
    font-size: 14px;
    font-weight: 600;
    color: #94a3b8;
}

.empty-state-sub {
    font-size: 12px;
    color: #64748b;
}

/* 5. Footer Bar */
.app-footer {
    background-color: #101216;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    padding: 7px 20px;
}

.footer-text {
    font-size: 11.5px;
    color: #8b949e;
}

.kbd-shortcut {
    background-color: #1a1c22;
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #94a3b8;
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 10px;
    font-family: monospace;
    font-weight: 600;
}

/* 6. Modal Dialogs */
.modal-window {
    background-color: #131519;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 22px;
    color: #f8fafc;
}

.modal-input {
    background-color: #0b0c0f;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 7px;
    color: #f8fafc;
    padding: 7px 11px;
    font-size: 12.5px;
}

.modal-input:focus {
    border-color: #ff5722;
}

checkbutton {
    color: #cbd5e1;
    font-size: 12px;
}

checkbutton:checked label {
    color: #f8fafc;
    font-weight: 600;
}
"""

class CommandCenterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.proj_mgr = ProjectManager()
        self.set_title("Project Hub")
        
        # Desktop dev tool floating dimensions (940x660 px)
        self.set_default_size(940, 660)
        self.view_mode = "grouped"  # "grouped" or "flat"
        self.status_filter = "all"   # "all", "running", "stopped"
        self.search_query = ""
        self.unified_items = []
        self.in_progress = {}       # {proj_id: "starting" | "stopping"}
        self.expanded_groups = set() # Closed by default in stacks view

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_ctrl)
        
        self.build_ui()
        self.refresh_all()
        GLib.timeout_add_seconds(3, self.on_heartbeat_tick)

    def build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # 1. Header Bar
        main_box.append(self.build_header())

        # 2. Subheader Toolbar (Navigation Tabs, Status Filters, Search)
        main_box.append(self.build_toolbar())
        
        # 3. Scrolled Main Area
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_vexpand(True)
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.content_box.set_margin_top(6)
        self.content_box.set_margin_bottom(14)
        self.scrolled.set_child(self.content_box)
        main_box.append(self.scrolled)
        
        # 4. Footer Bar
        main_box.append(self.build_footer())
        
        self.set_child(main_box)

    def build_header(self):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.add_css_class("app-header")
        
        # Brand & Glyph
        brand_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon_lbl = Gtk.Label(label="⚡")
        icon_lbl.add_css_class("brand-icon")
        brand_box.append(icon_lbl)

        self.app_title_lbl = Gtk.Label(label="Project Hub", xalign=0)
        self.app_title_lbl.add_css_class("brand-title")
        brand_box.append(self.app_title_lbl)

        dot = Gtk.Label(label=".", xalign=0)
        dot.add_css_class("brand-title")
        dot.add_css_class("brand-dot")
        brand_box.append(dot)

        header.append(brand_box)

        # Overall Service Statistics Pills
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.stat_running = Gtk.Label(label="● 0 Running")
        self.stat_running.add_css_class("header-stat-pill")
        self.stat_running.add_css_class("running")
        stats_box.append(self.stat_running)

        self.stat_stopped = Gtk.Label(label="○ 0 Stopped")
        self.stat_stopped.add_css_class("header-stat-pill")
        stats_box.append(self.stat_stopped)

        self.stat_total = Gtk.Label(label="0 Services")
        self.stat_total.add_css_class("header-stat-pill")
        stats_box.append(self.stat_total)

        header.append(stats_box)

        sp = Gtk.Box()
        sp.set_hexpand(True)
        header.append(sp)

        # Primary Action: New Group
        new_grp_btn = Gtk.Button()
        new_grp_btn.add_css_class("btn-secondary")
        b1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        b1.append(Gtk.Image.new_from_icon_name("folder-new-symbolic"))
        b1.append(Gtk.Label(label="New Group"))
        new_grp_btn.set_child(b1)
        new_grp_btn.set_tooltip_text("Create a new group / stack")
        new_grp_btn.connect("clicked", lambda _: self.show_create_stack_dialog())
        header.append(new_grp_btn)

        # Primary Action: New Service
        new_srv_btn = Gtk.Button()
        new_srv_btn.add_css_class("btn-primary")
        b2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        b2.append(Gtk.Image.new_from_icon_name("list-add-symbolic"))
        b2.append(Gtk.Label(label="New Service"))
        new_srv_btn.set_child(b2)
        new_srv_btn.set_tooltip_text("Add or configure a new service")
        new_srv_btn.connect("clicked", lambda _: self.show_add_dialog())
        header.append(new_srv_btn)

        # Secondary: Choose Folder
        browse_btn = Gtk.Button()
        browse_btn.add_css_class("btn-secondary")
        b3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        b3.append(Gtk.Image.new_from_icon_name("folder-symbolic"))
        b3.append(Gtk.Label(label="Browse..."))
        browse_btn.set_child(b3)
        browse_btn.set_tooltip_text("Pick project folder from file system")
        browse_btn.connect("clicked", lambda _: self.open_direct_folder_picker())
        header.append(browse_btn)

        # Refresh Icon
        ref_btn = Gtk.Button()
        ref_btn.add_css_class("btn-icon")
        ref_btn.set_child(Gtk.Image.new_from_icon_name("view-refresh-symbolic"))
        ref_btn.set_tooltip_text("Refresh Status")
        ref_btn.connect("clicked", lambda _: self.refresh_all())
        header.append(ref_btn)

        # Close Icon
        cls_btn = Gtk.Button()
        cls_btn.add_css_class("btn-icon")
        cls_btn.set_child(Gtk.Image.new_from_icon_name("window-close-symbolic"))
        cls_btn.set_tooltip_text("Close (Esc)")
        cls_btn.connect("clicked", lambda _: self.close_window())
        header.append(cls_btn)

        return header

    def build_toolbar(self):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        toolbar.add_css_class("toolbar-box")

        # 1. Navigation Mode Switcher: Grouped View vs Flat Full Projects View
        switcher_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        switcher_box.add_css_class("view-switcher-box")

        self.btn_view_grouped = Gtk.Button(label="⊞ Grouped Stacks")
        self.btn_view_grouped.add_css_class("view-switch-btn")
        self.btn_view_grouped.add_css_class("active")
        self.btn_view_grouped.connect("clicked", lambda _: self.switch_view_mode("grouped"))
        switcher_box.append(self.btn_view_grouped)

        self.btn_view_flat = Gtk.Button(label="📁 All Projects (Flat)")
        self.btn_view_flat.add_css_class("view-switch-btn")
        self.btn_view_flat.connect("clicked", lambda _: self.switch_view_mode("flat"))
        switcher_box.append(self.btn_view_flat)

        toolbar.append(switcher_box)

        # 2. Status Filters
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.filter_all = Gtk.Button(label="All")
        self.filter_all.add_css_class("filter-pill")
        self.filter_all.add_css_class("active")
        self.filter_all.connect("clicked", lambda _: self.switch_status_filter("all"))
        filter_box.append(self.filter_all)

        self.filter_running = Gtk.Button(label="● Running")
        self.filter_running.add_css_class("filter-pill")
        self.filter_running.connect("clicked", lambda _: self.switch_status_filter("running"))
        filter_box.append(self.filter_running)

        self.filter_stopped = Gtk.Button(label="○ Stopped")
        self.filter_stopped.add_css_class("filter-pill")
        self.filter_stopped.connect("clicked", lambda _: self.switch_status_filter("stopped"))
        filter_box.append(self.filter_stopped)

        toolbar.append(filter_box)

        sp = Gtk.Box()
        sp.set_hexpand(True)
        toolbar.append(sp)

        # 3. Compact Search Bar
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.add_css_class("search-input")
        self.search_entry.set_placeholder_text("Search services, groups, paths, URLs...")
        self.search_entry.connect("search-changed", self.on_search_changed)
        toolbar.append(self.search_entry)

        return toolbar

    def build_footer(self):
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        footer.add_css_class("app-footer")
        
        self.status_msg = Gtk.Label(label="Ready", xalign=0)
        self.status_msg.add_css_class("footer-text")
        self.status_msg.set_hexpand(True)
        footer.append(self.status_msg)
        
        h1 = Gtk.Label(label="Win + K")
        h1.add_css_class("kbd-shortcut")
        footer.append(h1)
        
        h2 = Gtk.Label(label="Esc to close")
        h2.add_css_class("kbd-shortcut")
        footer.append(h2)
        
        return footer

    def switch_view_mode(self, mode):
        self.view_mode = mode
        self.btn_view_grouped.remove_css_class("active")
        self.btn_view_flat.remove_css_class("active")
        if mode == "grouped":
            self.btn_view_grouped.add_css_class("active")
        else:
            self.btn_view_flat.add_css_class("active")
        self.render_view()

    def switch_status_filter(self, status):
        self.status_filter = status
        self.filter_all.remove_css_class("active")
        self.filter_running.remove_css_class("active")
        self.filter_stopped.remove_css_class("active")
        if status == "all":
            self.filter_all.add_css_class("active")
        elif status == "running":
            self.filter_running.add_css_class("active")
        elif status == "stopped":
            self.filter_stopped.add_css_class("active")
        self.render_view()

    def on_search_changed(self, entry):
        self.search_query = entry.get_text().strip().lower()
        self.render_view()

    def on_key_pressed(self, ctrl, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.close_window()
            return True
        return False

    def close_window(self):
        self.get_application().quit()

    def set_status(self, text):
        GLib.idle_add(lambda: self.status_msg.set_text(text))

    def on_heartbeat_tick(self):
        if self.get_visible() and not self.in_progress:
            self.refresh_all(silent=True)
        return True

    def refresh_all(self, silent=False):
        if not silent:
            self.set_status("Scanning services & containers...")
        def worker():
            projects = self.proj_mgr.projects
            combined = []
            running_cnt = 0
            changed = False
            old_states = {it.get("id"): it.get("is_running") for it in self.unified_items}
            
            for p in projects:
                status = self.proj_mgr.check_status(p)
                is_running = (status == "RUNNING")
                if is_running:
                    running_cnt += 1
                p_copy = dict(p)
                p_copy["is_running"] = is_running
                combined.append(p_copy)
                if old_states.get(p.get("id")) != is_running:
                    changed = True
                
            if len(self.unified_items) != len(combined):
                changed = True

            self.unified_items = combined
            total_cnt = len(combined)
            stopped_cnt = total_cnt - running_cnt
            stacks_cnt = len(self.proj_mgr.get_stacks())
            
            def update_ui():
                self.stat_running.set_label(f"● {running_cnt} Running")
                self.stat_stopped.set_label(f"○ {stopped_cnt} Stopped")
                self.stat_total.set_label(f"{total_cnt} Services")
                if changed or not silent:
                    self.render_view()
                if not silent or changed:
                    self.set_status(f"✓ Ready • {running_cnt} of {total_cnt} services active across {stacks_cnt} groups")

            GLib.idle_add(update_ui)
            
        threading.Thread(target=worker, daemon=True).start()

    def toggle_group_expanded(self, group_name):
        if group_name in self.expanded_groups:
            self.expanded_groups.remove(group_name)
        else:
            self.expanded_groups.add(group_name)
        self.render_view()

    def toggle_group_collapsed(self, group_name):
        """Backward compatible alias"""
        self.toggle_group_expanded(group_name)

    def render_view(self):
        while child := self.content_box.get_first_child():
            self.content_box.remove(child)

        all_stacks = self.proj_mgr.get_stacks()
        all_stack_names = [s.get("name") for s in all_stacks]

        # 1. Filter items based on search and status filter
        filtered_items = []
        for item in self.unified_items:
            is_running = item.get("is_running", False)
            if self.status_filter == "running" and not is_running:
                continue
            if self.status_filter == "stopped" and is_running:
                continue

            stacks_str = " ".join(item.get("stacks", []))
            text = f"{item.get('name')} {stacks_str} {item.get('path')} {item.get('url')} {item.get('desc', '')}".lower()
            if self.search_query and self.search_query not in text:
                continue
            filtered_items.append(item)

        # ==============================================================
        # VIEW MODE 1: GROUPED STACKS VIEW
        # ==============================================================
        if self.view_mode == "grouped":
            displayed_groups = 0

            # Render named stacks
            for stack in all_stacks:
                stack_name = stack.get("name")
                desc = stack.get("desc", "")

                # Member services belonging to this stack
                member_services = [
                    p for p in filtered_items
                    if stack_name in p.get("stacks", [])
                ]

                repo_url = (stack.get("repo_url") or "").strip()

                # If searching and search matches stack name, desc, or repo_url, show all matching members
                if self.search_query and (self.search_query in stack_name.lower() or self.search_query in desc.lower() or (repo_url and self.search_query in repo_url.lower())):
                    member_services = [
                        p for p in self.unified_items
                        if stack_name in p.get("stacks", [])
                    ]
                    if self.status_filter == "running":
                        member_services = [p for p in member_services if p.get("is_running")]
                    elif self.status_filter == "stopped":
                        member_services = [p for p in member_services if not p.get("is_running")]

                # Only hide stack if empty AND filtering is active or search is active
                if not member_services and (self.search_query or self.status_filter != "all"):
                    continue

                card = self.create_group_card(stack_name, desc, member_services, is_standalone=False, repo_url=repo_url)
                self.content_box.append(card)
                displayed_groups += 1

            # Render Standalone Services (services not belonging to any registered stack)
            standalone_services = [
                p for p in filtered_items
                if not any(s in all_stack_names for s in p.get("stacks", []))
            ]
            if standalone_services:
                std_card = self.create_group_card(
                    stack_name="📁 Standalone Services",
                    desc="Individual services without stack assignment",
                    member_services=standalone_services,
                    is_standalone=True
                )
                self.content_box.append(std_card)
                displayed_groups += 1

            if displayed_groups == 0:
                self.render_empty_state("No groups or services found matching your filters.")

        # ==============================================================
        # VIEW MODE 2: FULL PROJECTS (FLAT) VIEW
        # ==============================================================
        elif self.view_mode == "flat":
            if filtered_items:
                for item in filtered_items:
                    row = self.create_service_row(item, current_stack=None, is_flat=True)
                    row.set_margin_start(20)
                    row.set_margin_end(20)
                    self.content_box.append(row)
            else:
                self.render_empty_state("No services matching the active search or status filter.")

    def render_empty_state(self, message):
        empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        empty_box.add_css_class("empty-state-box")
        lbl = Gtk.Label(label=message, xalign=0.5)
        lbl.add_css_class("empty-state-title")
        sub = Gtk.Label(label="Try adjusting your search query, or click '+ New Service' to add one.", xalign=0.5)
        sub.add_css_class("empty-state-sub")
        empty_box.append(lbl)
        empty_box.append(sub)
        self.content_box.append(empty_box)

    def create_group_card(self, stack_name, desc, member_services, is_standalone=False, repo_url=""):
        wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        wrapper.add_css_class("group-wrapper")

        # Closed by default in stacks tab, unless user expanded it or search query is active
        is_collapsed = (stack_name not in self.expanded_groups) and not bool(self.search_query.strip())

        # Header Bar
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header.add_css_class("group-header")
        if is_collapsed:
            header.add_css_class("collapsed")

        # Chevron expand/collapse toggle
        toggle_btn = Gtk.Button(label="▶" if is_collapsed else "▼")
        toggle_btn.add_css_class("btn-icon")
        toggle_btn.set_tooltip_text("Collapse group" if not is_collapsed else "Expand group")
        toggle_btn.connect("clicked", lambda _, sn=stack_name: self.toggle_group_expanded(sn))
        header.append(toggle_btn)

        # Title & Meta Box (clicking title also toggles accordion)
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_box.set_hexpand(True)
        title_click = Gtk.GestureClick()
        title_click.connect("released", lambda *_: self.toggle_group_expanded(stack_name))
        title_box.add_controller(title_click)

        if not is_standalone:
            g_icon = Gtk.Image.new_from_icon_name("folder-symbolic")
            title_box.append(g_icon)

        title = Gtk.Label(label=stack_name, xalign=0)
        title.add_css_class("group-title")
        title_box.append(title)

        running_cnt = sum(1 for it in member_services if it.get("is_running"))
        total_cnt = len(member_services)

        badge = Gtk.Label(label=f"{running_cnt}/{total_cnt} active")
        badge.add_css_class("group-badge")
        if running_cnt == total_cnt and total_cnt > 0:
            badge.add_css_class("active")
        title_box.append(badge)

        if desc:
            d_lbl = Gtk.Label(label=f"• {desc}", xalign=0)
            d_lbl.add_css_class("group-desc")
            d_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            d_lbl.set_max_width_chars(35)
            title_box.append(d_lbl)

        header.append(title_box)

        # Monorepo / Repository Link (e.g. Turborepo root URL/path)
        if repo_url and not is_standalone:
            repo_btn = Gtk.Button()
            repo_btn.add_css_class("btn-repo-url")
            
            clean_display = repo_url
            for pfx in ["https://github.com/", "http://github.com/", "https://", "http://"]:
                if clean_display.startswith(pfx):
                    clean_display = clean_display[len(pfx):]
                    break
            clean_display = clean_display.rstrip("/")
            if len(clean_display) > 28:
                clean_display = clean_display[:26] + "…"
            
            b_r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            b_r.append(Gtk.Label(label="💻"))
            b_r.append(Gtk.Label(label=f"Code: {clean_display}"))
            repo_btn.set_child(b_r)
            repo_btn.set_tooltip_text(f"Open monorepo in VS Code: {repo_url}")
            repo_btn.connect("clicked", lambda _, u=repo_url, sn=stack_name: self.open_repo_target(u, stack_name=sn))
            header.append(repo_btn)

        # Group Lifecycle Actions
        if not is_standalone:
            # Start All
            start_grp_btn = Gtk.Button()
            start_grp_btn.add_css_class("btn-start")
            b_s = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            b_s.append(Gtk.Image.new_from_icon_name("media-playback-start-symbolic"))
            b_s.append(Gtk.Label(label="Start All"))
            start_grp_btn.set_child(b_s)
            start_grp_btn.set_tooltip_text(f"Start all {total_cnt} services in {stack_name}")
            start_grp_btn.connect("clicked", lambda _, sn=stack_name: self.execute_stack(sn, "run"))
            header.append(start_grp_btn)

            # Stop All
            stop_grp_btn = Gtk.Button()
            stop_grp_btn.add_css_class("btn-stop")
            b_p = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            b_p.append(Gtk.Image.new_from_icon_name("media-playback-stop-symbolic"))
            b_p.append(Gtk.Label(label="Stop All"))
            stop_grp_btn.set_child(b_p)
            stop_grp_btn.set_tooltip_text(f"Stop all services in {stack_name}")
            stop_grp_btn.connect("clicked", lambda _, sn=stack_name: self.execute_stack(sn, "stop"))
            header.append(stop_grp_btn)

            # Add Service to Group
            add_srv_btn = Gtk.Button()
            add_srv_btn.add_css_class("btn-secondary")
            b_a = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            b_a.append(Gtk.Image.new_from_icon_name("list-add-symbolic"))
            b_a.append(Gtk.Label(label="Add Service"))
            add_srv_btn.set_child(b_a)
            add_srv_btn.set_tooltip_text(f"Add a service to '{stack_name}'")
            add_srv_btn.connect("clicked", lambda _, sn=stack_name: self.show_add_to_stack_picker(sn))
            header.append(add_srv_btn)

            # Edit Group Settings (Name, Description, Repo URL)
            ren_btn = Gtk.Button()
            ren_btn.add_css_class("btn-icon")
            ren_btn.set_child(Gtk.Image.new_from_icon_name("document-edit-symbolic"))
            ren_btn.set_tooltip_text(f"Edit group / stack settings for '{stack_name}'")
            ren_btn.connect("clicked", lambda _, sn=stack_name: self.show_edit_stack_dialog(sn))
            header.append(ren_btn)

            # Delete Group (with confirmation)
            del_btn = Gtk.Button()
            del_btn.add_css_class("btn-icon")
            del_btn.add_css_class("btn-icon-danger")
            del_btn.set_child(Gtk.Image.new_from_icon_name("user-trash-symbolic"))
            del_btn.set_tooltip_text(f"Delete group '{stack_name}'")
            del_btn.connect("clicked", lambda _, sn=stack_name: self.show_delete_stack_dialog(sn))
            header.append(del_btn)
        else:
            add_std_btn = Gtk.Button(label="+ New Service")
            add_std_btn.add_css_class("btn-primary")
            add_std_btn.connect("clicked", lambda _: self.show_add_dialog())
            header.append(add_std_btn)

        wrapper.append(header)

        # Body (Member Service Rows)
        if not is_collapsed:
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            content.add_css_class("group-content")

            if member_services:
                for item in member_services:
                    content.append(self.create_service_row(item, current_stack=stack_name, is_flat=False))
            else:
                emp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                emp_box.add_css_class("empty-state-box")
                emp_lbl = Gtk.Label(label="No services in this group yet. Click '+ Add Service' above to add one.", xalign=0)
                emp_lbl.add_css_class("empty-state-sub")
                emp_box.append(emp_lbl)
                content.append(emp_box)

            wrapper.append(content)

        return wrapper

    def create_service_row(self, item, current_stack=None, is_flat=False):
        """Builds a refined Linear / Docker Desktop style service item row"""
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        row.add_css_class("service-row")

        is_running = item.get("is_running", False)
        pid = item.get("id")
        in_prog_state = self.in_progress.get(pid)  # "starting" | "stopping" | None

        # ROW 1: Status Dot, Service Name, Stack Pills, URL Action Link, Status Badge
        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Status Indicator Dot & Label
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        if in_prog_state:
            s_badge = Gtk.Label(label=f"◌ {in_prog_state.upper()}...")
            s_badge.add_css_class("status-badge-starting")
        elif is_running:
            s_badge = Gtk.Label(label="● RUNNING")
            s_badge.add_css_class("status-badge-running")
        else:
            s_badge = Gtk.Label(label="○ STOPPED")
            s_badge.add_css_class("status-badge-stopped")
        status_box.append(s_badge)
        row1.append(status_box)

        # Service / Project Name
        name_lbl = Gtk.Label(label=item.get("name", "Unnamed"), xalign=0)
        name_lbl.add_css_class("service-name")
        row1.append(name_lbl)

        # Quick Rename Project Button
        ren_proj_btn = Gtk.Button()
        ren_proj_btn.add_css_class("btn-icon-subtle")
        ren_proj_btn.set_child(Gtk.Image.new_from_icon_name("document-edit-symbolic"))
        ren_proj_btn.set_tooltip_text(f"Rename project '{item.get('name')}'")
        ren_proj_btn.connect("clicked", lambda _, it=item: self.show_rename_project_dialog(it))
        row1.append(ren_proj_btn)

        # If flat view or belongs to multiple stacks, show subtle pills
        all_item_stacks = item.get("stacks", [])
        if is_flat:
            for st in all_item_stacks:
                pill = Gtk.Label(label=st)
                pill.add_css_class("tag-pill")
                row1.append(pill)
        elif current_stack:
            other_stacks = [s for s in all_item_stacks if s != current_stack]
            for ost in other_stacks:
                pill = Gtk.Label(label=ost)
                pill.add_css_class("tag-pill")
                pill.set_tooltip_text(f"Also in group '{ost}'")
                row1.append(pill)

        # VS Code auto-open badge if configured
        if item.get("open_vscode"):
            vc_pill = Gtk.Label(label="💻 Code on Start")
            vc_pill.add_css_class("tag-pill")
            vc_pill.set_tooltip_text("Opens in VS Code automatically when started")
            row1.append(vc_pill)

        sp1 = Gtk.Box()
        sp1.set_hexpand(True)
        row1.append(sp1)

        # Application URL Action Link
        url = item.get("url", "").strip()
        if url:
            url_btn = Gtk.Button(label=f"{url} ↗")
            url_btn.add_css_class("btn-open-url")
            url_btn.set_tooltip_text(f"Open {url} in Browser")
            url_btn.connect("clicked", lambda _, u=url: self.open_browser(u))
            row1.append(url_btn)

        row.append(row1)

        # ROW 2: Directory Path & Optional Description
        row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        f_icon = Gtk.Image.new_from_icon_name("folder-symbolic")
        f_icon.set_opacity(0.6)
        row2.append(f_icon)

        raw_path = item.get("path", "")
        path_lbl = Gtk.Label(label=raw_path, xalign=0)
        path_lbl.add_css_class("service-path")
        path_lbl.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        path_lbl.set_max_width_chars(50)
        path_lbl.set_tooltip_text(raw_path)
        row2.append(path_lbl)

        desc = item.get("desc", "").strip()
        if desc:
            d_lbl = Gtk.Label(label=f"• {desc}", xalign=0)
            d_lbl.add_css_class("service-desc")
            d_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            d_lbl.set_max_width_chars(45)
            row2.append(d_lbl)

        row.append(row2)

        # ROW 3: Intelligently Organized Actions Toolbar
        actions_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actions_row.set_margin_top(2)

        # 1. Primary Action: Start / Stop
        if in_prog_state:
            prog_btn = Gtk.Button(label=f"{in_prog_state.capitalize()}...")
            prog_btn.add_css_class("btn-in-progress")
            prog_btn.set_sensitive(False)
            actions_row.append(prog_btn)
        elif not is_running:
            start_btn = Gtk.Button()
            start_btn.add_css_class("btn-start")
            c = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            c.append(Gtk.Image.new_from_icon_name("media-playback-start-symbolic"))
            c.append(Gtk.Label(label="Start"))
            start_btn.set_child(c)
            start_btn.connect("clicked", lambda _, it=item: self.execute_action(it, "run"))
            actions_row.append(start_btn)
        else:
            stop_btn = Gtk.Button()
            stop_btn.add_css_class("btn-stop")
            c = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            c.append(Gtk.Image.new_from_icon_name("media-playback-stop-symbolic"))
            c.append(Gtk.Label(label="Stop"))
            stop_btn.set_child(c)
            stop_btn.connect("clicked", lambda _, it=item: self.execute_action(it, "stop"))
            actions_row.append(stop_btn)

        # 2. Open App Button (only if running and has URL)
        if url:
            open_app_btn = Gtk.Button(label="Open App ↗")
            open_app_btn.add_css_class("btn-secondary")
            open_app_btn.set_tooltip_text(f"Redirect to {url}")
            open_app_btn.connect("clicked", lambda _, u=url: self.open_browser(u))
            actions_row.append(open_app_btn)

        # 3. Build Action (Secondary)
        if item.get("build_cmd"):
            build_btn = Gtk.Button(label="Build")
            build_btn.add_css_class("btn-secondary")
            build_btn.set_tooltip_text(f"Run: {item.get('build_cmd')}")
            build_btn.connect("clicked", lambda _, it=item: self.execute_action(it, "build"))
            actions_row.append(build_btn)

        # 4. View Logs Action
        logs_btn = Gtk.Button(label="Logs")
        logs_btn.add_css_class("btn-secondary")
        logs_btn.set_tooltip_text("View live service output logs")
        logs_btn.connect("clicked", lambda _, it=item: self.show_logs_dialog(it))
        actions_row.append(logs_btn)

        # 5. VS Code Action Button
        vscode_btn = Gtk.Button()
        vscode_btn.add_css_class("btn-secondary")
        vc_c = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        vc_c.append(Gtk.Label(label="💻"))
        vc_c.append(Gtk.Label(label="Code"))
        vscode_btn.set_child(vc_c)
        vscode_btn.set_tooltip_text(f"Open {raw_path} in VS Code now")
        vscode_btn.connect("clicked", lambda _, p=raw_path: self.proj_mgr.launch_vscode(p))
        actions_row.append(vscode_btn)

        # 6. Checkbox to toggle VS Code on start
        card_vscode_cb = Gtk.CheckButton(label="Open on start")
        card_vscode_cb.set_active(item.get("open_vscode", False))
        card_vscode_cb.set_tooltip_text("If checked, starting this project will automatically open VS Code")
        card_vscode_cb.connect("toggled", lambda cb, p=pid: self.on_vscode_toggled(cb, p))
        actions_row.append(card_vscode_cb)

        sp2 = Gtk.Box()
        sp2.set_hexpand(True)
        actions_row.append(sp2)

        # 7. Edit Service Icon
        edit_btn = Gtk.Button()
        edit_btn.add_css_class("btn-icon")
        edit_btn.set_child(Gtk.Image.new_from_icon_name("document-edit-symbolic"))
        edit_btn.set_tooltip_text("Edit service configuration")
        edit_btn.connect("clicked", lambda _, it=item: self.show_add_dialog(existing_item=it))
        actions_row.append(edit_btn)

        # 8. Remove from this group (only if inside a named group)
        if current_stack and not is_flat:
            rem_btn = Gtk.Button()
            rem_btn.add_css_class("btn-icon")
            rem_btn.add_css_class("btn-icon-danger")
            rem_btn.set_child(Gtk.Image.new_from_icon_name("window-close-symbolic"))
            rem_btn.set_tooltip_text(f"Remove from group '{current_stack}' (keeps project intact)")
            rem_btn.connect("clicked", lambda _, p=pid, sn=current_stack: self.remove_from_stack(p, sn))
            actions_row.append(rem_btn)

        # 9. Delete Service Icon (with confirmation)
        del_btn = Gtk.Button()
        del_btn.add_css_class("btn-icon")
        del_btn.add_css_class("btn-icon-danger")
        del_btn.set_child(Gtk.Image.new_from_icon_name("user-trash-symbolic"))
        del_btn.set_tooltip_text("Delete service completely")
        del_btn.connect("clicked", lambda _, it=item: self.show_delete_service_dialog(it))
        actions_row.append(del_btn)

        row.append(actions_row)
        return row

    def resolve_monorepo_dir(self, target, stack_name=None):
        """Resolve a target (which may be a local path, git URL, or repo name) to a local directory path."""
        target = (target or "").strip()
        if not target:
            return None

        # 1. Direct local path check (absolute or relative)
        try:
            p = self.proj_mgr.resolve_path(target)
            if p.exists() and p.is_dir():
                return p
        except Exception:
            pass

        # 2. Extract repository name from target (e.g. https://github.com/org/repo -> repo)
        clean = target.rstrip("/")
        if clean.endswith(".git"):
            clean = clean[:-4]

        if "/" in clean:
            repo_name = clean.split("/")[-1]
        elif ":" in clean:
            repo_name = clean.split(":")[-1]
        else:
            repo_name = clean

        repo_name_lower = repo_name.lower()

        # 3. Check ancestor directories of projects belonging to this stack or all projects
        projects = self.proj_mgr.get_projects()
        stack_projects = []
        other_projects = []
        for proj in projects:
            if stack_name and stack_name in proj.get("stacks", []):
                stack_projects.append(proj)
            else:
                other_projects.append(proj)

        for proj in stack_projects + other_projects:
            raw_p = proj.get("path", "")
            if not raw_p:
                continue
            try:
                curr = Path(raw_p).resolve()
                while curr and curr != curr.parent and str(curr) != "/":
                    if curr.name.lower() == repo_name_lower and curr.is_dir():
                        return curr
                    git_cfg = curr / ".git" / "config"
                    if git_cfg.exists():
                        try:
                            cfg_text = git_cfg.read_text()
                            if repo_name_lower in cfg_text.lower() or clean.lower() in cfg_text.lower():
                                return curr
                        except Exception:
                            pass
                    curr = curr.parent
            except Exception:
                pass

        # 4. Check common developer directories on system
        common_dirs = [
            Path("/Work") / repo_name,
            Path("/work") / repo_name,
            Path.home() / "Work" / repo_name,
            Path.home() / "work" / repo_name,
            Path.home() / "Projects" / repo_name,
            Path.home() / "projects" / repo_name,
            Path.home() / "workspace" / repo_name,
            Path.home() / "Development" / repo_name,
            Path.home() / repo_name
        ]
        for cd in common_dirs:
            try:
                if cd.exists() and cd.is_dir():
                    return cd
            except Exception:
                pass

        return None

    def open_repo_target(self, target, stack_name=None, close_window=False):
        target = (target or "").strip()
        if not target:
            return
        
        # 1. Attempt to resolve to a local directory and open in VS Code
        local_dir = self.resolve_monorepo_dir(target, stack_name=stack_name)
        if local_dir:
            try:
                subprocess.Popen(["code", str(local_dir)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.set_status(f"✓ Opened monorepo in VS Code: {local_dir}")
                return
            except Exception as e:
                self.set_status(f"✗ Failed to open VS Code: {e}")
                return

        # 2. If no local directory is found and it is a remote web/git URL, open in browser
        if target.startswith("http://") or target.startswith("https://") or target.startswith("git@"):
            browser_url = target
            if browser_url.startswith("git@"):
                parts = browser_url.split(":", 1)
                if len(parts) == 2:
                    host = parts[0].replace("git@", "")
                    rem = parts[1].rstrip(".git")
                    browser_url = f"https://{host}/{rem}"
            self.set_status(f"ℹ No local directory found for {target}, opening repository page...")
            self.open_browser(browser_url, close_window=close_window)
        else:
            self.set_status(f"✗ Directory path does not exist: {target}")

    def open_browser(self, url, close_window=True):
        webbrowser.open(url)
        if close_window:
            self.close_window()

    def execute_action(self, item, action):
        name = item.get("name")
        pid = item.get("id")

        if action == "run":
            self.in_progress[pid] = "starting"
        elif action == "stop":
            self.in_progress[pid] = "stopping"

        self.set_status(f"Executing {action} on {name}...")
        self.render_view()

        def on_done(success, msg):
            self.in_progress.pop(pid, None)
            self.set_status(f"✓ {name}: {action} completed" if success else f"✗ {name}: {msg}")
            self.refresh_all()

        self.proj_mgr.execute_action(pid, action, on_done_callback=on_done)

    def execute_stack(self, stack_name, action):
        self.set_status(f"Executing {action} across group: {stack_name}...")
        
        # If action is 'run' (Start All):
        # If repo_url is added in this stack group, open it on start! If left empty, don't open!
        if action == "run":
            stack_obj = self.proj_mgr.get_stack(stack_name)
            repo_url = ""
            if stack_obj:
                repo_url = (stack_obj.get("repo_url") or "").strip()
            
            if repo_url:
                self.open_repo_target(repo_url, stack_name=stack_name, close_window=False)
                self.set_status(f"✓ Opened monorepo in VS Code for '{stack_name}' • Starting services...")

        # Mark member services as in progress
        for it in self.unified_items:
            if stack_name in it.get("stacks", []):
                self.in_progress[it.get("id")] = "starting" if action == "run" else "stopping"
        self.render_view()

        def on_done(success, msg):
            for it in self.unified_items:
                if stack_name in it.get("stacks", []):
                    self.in_progress.pop(it.get("id"), None)
            self.set_status(f"✓ {stack_name}: {action} finished" if success else f"✗ {msg}")
            self.refresh_all()

        self.proj_mgr.execute_stack_action(stack_name, action, on_done_callback=on_done)

    def remove_from_stack(self, proj_id, stack_name):
        self.proj_mgr.remove_project_from_stack(proj_id, stack_name)
        self.refresh_all()
        self.set_status(f"✓ Removed service from group '{stack_name}'")

    def on_vscode_toggled(self, cb, pid):
        is_active = cb.get_active()
        self.proj_mgr.toggle_project_vscode(pid, is_active)
        self.set_status(f"✓ VS Code auto-open {'enabled' if is_active else 'disabled'}")

    # ==============================================================
    # DIALOGS & MODALS
    # ==============================================================
    def show_create_stack_dialog(self):
        dialog = Gtk.Window(transient_for=self)
        dialog.set_title("Create New Group")
        dialog.set_default_size(500, 320)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.add_css_class("modal-window")
        
        title_lbl = Gtk.Label(label="Create New Group / Stack", xalign=0)
        title_lbl.add_css_class("brand-title")
        box.append(title_lbl)
        
        box.append(Gtk.Label(label="Group Name (e.g. Core Databases, Web Services):", xalign=0))
        name_entry = Gtk.Entry()
        name_entry.add_css_class("modal-input")
        name_entry.set_placeholder_text("e.g. Core Services or Web Apps")
        box.append(name_entry)

        box.append(Gtk.Label(label="Description (Optional):", xalign=0))
        desc_entry = Gtk.Entry()
        desc_entry.add_css_class("modal-input")
        desc_entry.set_placeholder_text("e.g. Turborepo Monorepo & Microservices")
        box.append(desc_entry)

        box.append(Gtk.Label(label="Repository / Monorepo Path or URL (Opens in VS Code on Start):", xalign=0))
        repo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        repo_entry = Gtk.Entry()
        repo_entry.add_css_class("modal-input")
        repo_entry.set_hexpand(True)
        repo_entry.set_placeholder_text("e.g. ~/projects/my-monorepo or https://github.com/org/repo")
        repo_box.append(repo_entry)

        browse_repo_btn = Gtk.Button(label="📁 Browse...")
        browse_repo_btn.add_css_class("btn-secondary")
        browse_repo_btn.connect("clicked", lambda _: self.choose_folder_dialog(dialog, lambda p: repo_entry.set_text(p)))
        repo_box.append(browse_repo_btn)
        box.append(repo_box)
        
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_margin_top(8)
        
        save_btn = Gtk.Button(label="Create Group")
        save_btn.add_css_class("btn-primary")
        
        def save():
            name = name_entry.get_text().strip()
            desc = desc_entry.get_text().strip()
            repo_url = repo_entry.get_text().strip()
            if name:
                self.proj_mgr.create_stack(name, desc, repo_url=repo_url)
                dialog.close()
                self.refresh_all()
                self.set_status(f"✓ Created group '{name}'")
                
        save_btn.connect("clicked", lambda _: save())
        name_entry.connect("activate", lambda _: save())
        repo_entry.connect("activate", lambda _: save())
        
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.add_css_class("btn-secondary")
        cancel_btn.connect("clicked", lambda _: dialog.close())
        
        btn_box.append(save_btn)
        btn_box.append(cancel_btn)
        box.append(btn_box)
        
        dialog.set_child(box)
        dialog.present()


    def show_edit_stack_dialog(self, old_name):
        dialog = Gtk.Window(transient_for=self)
        dialog.set_title(f"Edit Group Settings")
        dialog.set_default_size(500, 340)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.add_css_class("modal-window")
        
        title_lbl = Gtk.Label(label=f"Edit Group: {old_name}", xalign=0)
        title_lbl.add_css_class("brand-title")
        box.append(title_lbl)

        stack_obj = self.proj_mgr.get_stack(old_name) or {}
        curr_desc = stack_obj.get("desc", "")
        curr_repo = (stack_obj.get("repo_url") or "").strip()
        
        box.append(Gtk.Label(label="Group Name:", xalign=0))
        entry = Gtk.Entry()
        entry.add_css_class("modal-input")
        entry.set_text(old_name)
        box.append(entry)

        box.append(Gtk.Label(label="Description (Optional):", xalign=0))
        desc_entry = Gtk.Entry()
        desc_entry.add_css_class("modal-input")
        desc_entry.set_text(curr_desc)
        desc_entry.set_placeholder_text("e.g. Turborepo Monorepo & Microservices")
        box.append(desc_entry)

        box.append(Gtk.Label(label="Repository / Monorepo Path or URL (Opens in VS Code on Start):", xalign=0))
        repo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        repo_entry = Gtk.Entry()
        repo_entry.add_css_class("modal-input")
        repo_entry.set_hexpand(True)
        repo_entry.set_text(curr_repo)
        repo_entry.set_placeholder_text("e.g. ~/projects/my-monorepo or https://github.com/org/repo")
        repo_box.append(repo_entry)

        browse_repo_btn = Gtk.Button(label="📁 Browse...")
        browse_repo_btn.add_css_class("btn-secondary")
        browse_repo_btn.connect("clicked", lambda _: self.choose_folder_dialog(dialog, lambda p: repo_entry.set_text(p)))
        repo_box.append(browse_repo_btn)
        box.append(repo_box)
        
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_margin_top(8)
        
        save_btn = Gtk.Button(label="Save Settings")
        save_btn.add_css_class("btn-primary")
        
        def save():
            new_name = entry.get_text().strip()
            new_desc = desc_entry.get_text().strip()
            new_repo = repo_entry.get_text().strip()
            if new_name:
                self.proj_mgr.update_stack(old_name, new_name=new_name, desc=new_desc, repo_url=new_repo)
                dialog.close()
                self.refresh_all()
                self.set_status(f"✓ Updated group settings for '{new_name}'")
                
        save_btn.connect("clicked", lambda _: save())
        entry.connect("activate", lambda _: save())
        repo_entry.connect("activate", lambda _: save())
        
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.add_css_class("btn-secondary")
        cancel_btn.connect("clicked", lambda _: dialog.close())
        
        btn_box.append(save_btn)
        btn_box.append(cancel_btn)
        box.append(btn_box)
        
        dialog.set_child(box)
        dialog.present()

    def show_rename_stack_dialog(self, old_name):
        self.show_edit_stack_dialog(old_name)


    def show_rename_project_dialog(self, item):
        dialog = Gtk.Window(transient_for=self)
        dialog.set_title("Rename Project")
        dialog.set_default_size(440, 200)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.add_css_class("modal-window")

        old_name = item.get("name", "")
        pid = item.get("id")

        title_lbl = Gtk.Label(label=f"Rename Project: {old_name}", xalign=0)
        title_lbl.add_css_class("brand-title")
        box.append(title_lbl)

        box.append(Gtk.Label(label="New Project Name:", xalign=0))
        entry = Gtk.Entry()
        entry.add_css_class("modal-input")
        entry.set_text(old_name)
        box.append(entry)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_margin_top(8)

        save_btn = Gtk.Button(label="Rename Project")
        save_btn.add_css_class("btn-primary")

        def save():
            new_name = entry.get_text().strip()
            if new_name:
                self.proj_mgr.rename_project(pid, new_name)
                dialog.close()
                self.refresh_all()
                self.set_status(f"✓ Renamed project to '{new_name}'")

        save_btn.connect("clicked", lambda _: save())
        entry.connect("activate", lambda _: save())

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.add_css_class("btn-secondary")
        cancel_btn.connect("clicked", lambda _: dialog.close())

        btn_box.append(save_btn)
        btn_box.append(cancel_btn)
        box.append(btn_box)

        dialog.set_child(box)
        dialog.present()

    def show_delete_stack_dialog(self, stack_name):
        dialog = Gtk.Window(transient_for=self)
        dialog.set_title(f"Delete Group Confirmation")
        dialog.set_default_size(440, 180)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.add_css_class("modal-window")

        title_lbl = Gtk.Label(label=f"Delete Group '{stack_name}'?", xalign=0)
        title_lbl.add_css_class("brand-title")
        box.append(title_lbl)

        msg = Gtk.Label(label="Member services will NOT be deleted, but will become ungrouped.", xalign=0)
        msg.add_css_class("service-desc")
        msg.set_wrap(True)
        box.append(msg)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_margin_top(10)

        del_btn = Gtk.Button(label="Delete Group")
        del_btn.add_css_class("btn-stop")

        def do_delete():
            self.proj_mgr.delete_stack(stack_name)
            dialog.close()
            self.refresh_all()
            self.set_status(f"✓ Group '{stack_name}' deleted")

        del_btn.connect("clicked", lambda _: do_delete())

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.add_css_class("btn-secondary")
        cancel_btn.connect("clicked", lambda _: dialog.close())

        btn_box.append(del_btn)
        btn_box.append(cancel_btn)
        box.append(btn_box)

        dialog.set_child(box)
        dialog.present()


    def show_delete_service_dialog(self, item):
        name = item.get("name")
        pid = item.get("id")

        dialog = Gtk.Window(transient_for=self)
        dialog.set_title("Delete Project Confirmation")
        dialog.set_default_size(440, 180)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.add_css_class("modal-window")

        title_lbl = Gtk.Label(label=f"Delete Project '{name}'?", xalign=0)
        title_lbl.add_css_class("brand-title")
        box.append(title_lbl)

        msg = Gtk.Label(label="This removes the project from this workspace. Files on disk will remain untouched.", xalign=0)
        msg.add_css_class("service-desc")
        msg.set_wrap(True)
        box.append(msg)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_margin_top(10)

        del_btn = Gtk.Button(label="Delete Project")
        del_btn.add_css_class("btn-stop")

        def do_delete():
            self.proj_mgr.delete_project(pid)
            dialog.close()
            self.refresh_all()
            self.set_status(f"✓ Project '{name}' deleted")

        del_btn.connect("clicked", lambda _: do_delete())

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.add_css_class("btn-secondary")
        cancel_btn.connect("clicked", lambda _: dialog.close())

        btn_box.append(del_btn)
        btn_box.append(cancel_btn)
        box.append(btn_box)

        dialog.set_child(box)
        dialog.present()


    def show_add_to_stack_picker(self, stack_name):
        dialog = Gtk.Window(transient_for=self)
        dialog.set_title(f"Add Service to Group: {stack_name}")
        dialog.set_default_size(520, 420)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.add_css_class("modal-window")

        title_lbl = Gtk.Label(label=f"Add Service to '{stack_name}'", xalign=0)
        title_lbl.add_css_class("brand-title")
        box.append(title_lbl)

        desc = Gtk.Label(label="Select an existing service to include in this group, or configure a new one:", xalign=0)
        desc.add_css_class("service-desc")
        box.append(desc)

        candidates = [p for p in self.unified_items if stack_name not in p.get("stacks", [])]

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        if candidates:
            for p in candidates:
                r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                r.add_css_class("service-row")

                ibox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                ibox.append(Gtk.Label(label=p.get("name"), xalign=0))
                p_lbl = Gtk.Label(label=p.get("path", ""), xalign=0)
                p_lbl.add_css_class("service-path")
                ibox.append(p_lbl)
                ibox.set_hexpand(True)
                r.append(ibox)

                add_p_btn = Gtk.Button(label="+ Add to Group")
                add_p_btn.add_css_class("btn-start")
                pid = p.get("id")
                add_p_btn.connect("clicked", lambda _, pid=pid, sn=stack_name: self.on_picker_add(dialog, pid, sn))
                r.append(add_p_btn)
                list_box.append(r)
        else:
            empty_lbl = Gtk.Label(label="All registered services are already inside this group.", xalign=0)
            empty_lbl.add_css_class("empty-state-sub")
            list_box.append(empty_lbl)

        scrolled.set_child(list_box)
        box.append(scrolled)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_margin_top(8)

        create_new_btn = Gtk.Button(label="+ Create New Service for this Group")
        create_new_btn.add_css_class("btn-primary")
        create_new_btn.connect("clicked", lambda _: (dialog.close(), self.show_add_dialog(default_stack=stack_name)))
        btn_box.append(create_new_btn)

        close_btn = Gtk.Button(label="Close")
        close_btn.add_css_class("btn-secondary")
        close_btn.connect("clicked", lambda _: dialog.close())
        btn_box.append(close_btn)

        box.append(btn_box)
        dialog.set_child(box)
        dialog.present()


    def on_picker_add(self, dialog, pid, stack_name):
        self.proj_mgr.add_project_to_stack(pid, stack_name)
        dialog.close()
        self.refresh_all()
        self.set_status(f"✓ Added service to group '{stack_name}'")

    # ------------------ Add / Edit Service Dialog ------------------
    def show_add_dialog(self, existing_item=None, detected_item=None, default_stack=None):
        dialog = Gtk.Window(transient_for=self)
        dialog.set_title("Configure Project")
        dialog.set_default_size(600, 680)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.add_css_class("modal-window")
        
        title_lbl = Gtk.Label(label="Configure Project & Groups", xalign=0)
        title_lbl.add_css_class("brand-title")
        box.append(title_lbl)
        
        item_data = existing_item or detected_item or {}

        # 1. Groups Multi-Selector
        box.append(Gtk.Label(label="Assign to Groups (Select one or multiple groups):", xalign=0))
        
        stack_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        stack_container.add_css_class("service-row")

        checks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        check_buttons = {}

        current_assigned = set()
        if existing_item:
            current_assigned = set(existing_item.get("stacks", []))
            if not current_assigned and existing_item.get("group"):
                current_assigned.add(existing_item["group"])
        elif detected_item:
            current_assigned = set(detected_item.get("stacks", []))
        if default_stack:
            current_assigned.add(default_stack)

        available_stacks = self.proj_mgr.get_stacks()
        if not available_stacks:
            available_stacks = [{"name": "Default", "desc": "Default Stack"}]

        for s in available_stacks:
            s_name = s.get("name")
            cb = Gtk.CheckButton(label=s_name)
            if s_name in current_assigned:
                cb.set_active(True)
            check_buttons[s_name] = cb
            checks_box.append(cb)

        stack_container.append(checks_box)

        # Inline Quick-Create Group Row
        inline_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        inline_row.set_margin_top(6)
        
        new_stack_entry = Gtk.Entry()
        new_stack_entry.add_css_class("modal-input")
        new_stack_entry.set_hexpand(True)
        new_stack_entry.set_placeholder_text("Create new group name (e.g. Core DBs)...")
        inline_row.append(new_stack_entry)

        add_stack_btn = Gtk.Button(label="+ Add Group")
        add_stack_btn.add_css_class("btn-secondary")
        
        def on_inline_add_stack():
            val = new_stack_entry.get_text().strip()
            if not val:
                return
            self.proj_mgr.create_stack(val)
            if val not in check_buttons:
                new_cb = Gtk.CheckButton(label=val)
                new_cb.set_active(True)
                check_buttons[val] = new_cb
                checks_box.append(new_cb)
            else:
                check_buttons[val].set_active(True)
            new_stack_entry.set_text("")

        add_stack_btn.connect("clicked", lambda _: on_inline_add_stack())
        new_stack_entry.connect("activate", lambda _: on_inline_add_stack())
        inline_row.append(add_stack_btn)

        stack_container.append(inline_row)
        box.append(stack_container)

        # 2. Directory Path with Browse Button
        box.append(Gtk.Label(label="Project Directory / Path:", xalign=0))
        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        path_entry = Gtk.Entry()
        path_entry.add_css_class("modal-input")
        path_entry.set_hexpand(True)
        path_entry.set_placeholder_text("e.g. ~/projects/backend-api")
        if item_data.get("path"):
            path_entry.set_text(item_data.get("path"))
        path_box.append(path_entry)
        
        browse_btn = Gtk.Button()
        browse_btn.add_css_class("btn-secondary")
        b_c = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        b_c.append(Gtk.Image.new_from_icon_name("folder-symbolic"))
        b_c.append(Gtk.Label(label="Browse..."))
        browse_btn.set_child(b_c)
        browse_btn.set_tooltip_text("Choose folder from file system")
        
        def on_browse_clicked():
            def on_picked(selected_path):
                path_entry.set_text(selected_path)
                detected = self.inspect_folder(selected_path)
                if not name_entry.get_text().strip():
                    name_entry.set_text(detected.get("name", ""))
                if not run_entry.get_text().strip():
                    run_entry.set_text(detected.get("run_cmd", ""))
                if not stop_entry.get_text().strip():
                    stop_entry.set_text(detected.get("stop_cmd", ""))
                if not build_entry.get_text().strip():
                    build_entry.set_text(detected.get("build_cmd", ""))
                if not url_entry.get_text().strip() and detected.get("url"):
                    url_entry.set_text(detected.get("url", ""))

            self.choose_folder_dialog(dialog, on_picked)

        browse_btn.connect("clicked", lambda _: on_browse_clicked())
        path_box.append(browse_btn)
        box.append(path_box)

        # 3. Project Name
        box.append(Gtk.Label(label="Project Name:", xalign=0))
        name_entry = Gtk.Entry()
        name_entry.add_css_class("modal-input")
        name_entry.set_placeholder_text("e.g. PostgreSQL Database, Client App, API Gateway")
        if item_data.get("name"):
            name_entry.set_text(item_data.get("name"))
        box.append(name_entry)
        
        # 4. Browser Redirect URL
        box.append(Gtk.Label(label="Browser Redirect URL (Optional):", xalign=0))
        url_entry = Gtk.Entry()
        url_entry.add_css_class("modal-input")
        url_entry.set_placeholder_text("e.g. https://local.pix.city:8000/admin")
        if item_data.get("url"):
            url_entry.set_text(item_data.get("url"))
        box.append(url_entry)
        
        # 5. Run Command
        box.append(Gtk.Label(label="Run Command:", xalign=0))
        run_entry = Gtk.Entry()
        run_entry.add_css_class("modal-input")
        run_entry.set_placeholder_text("e.g. ./up.sh")
        if item_data.get("run_cmd"):
            run_entry.set_text(item_data.get("run_cmd"))
        box.append(run_entry)
        
        # 6. Stop Command
        box.append(Gtk.Label(label="Stop Command:", xalign=0))
        stop_entry = Gtk.Entry()
        stop_entry.add_css_class("modal-input")
        stop_entry.set_placeholder_text("e.g. ./down.sh")
        if item_data.get("stop_cmd"):
            stop_entry.set_text(item_data.get("stop_cmd"))
        box.append(stop_entry)
        
        # 7. Build Command
        box.append(Gtk.Label(label="Build Command:", xalign=0))
        build_entry = Gtk.Entry()
        build_entry.add_css_class("modal-input")
        build_entry.set_placeholder_text("e.g. docker-compose up --build")
        if item_data.get("build_cmd"):
            build_entry.set_text(item_data.get("build_cmd"))
        box.append(build_entry)

        # 8. Open in VS Code Checkbox
        vscode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        vscode_box.set_margin_top(6)
        vscode_cb = Gtk.CheckButton(label="Open project in VS Code automatically when started")
        if item_data.get("open_vscode"):
            vscode_cb.set_active(True)
        vscode_box.append(vscode_cb)
        box.append(vscode_box)
        
        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_margin_top(14)
        
        save_btn = Gtk.Button(label="Save Project")
        save_btn.add_css_class("btn-primary")
        
        def save():
            name = name_entry.get_text().strip()
            path = path_entry.get_text().strip()
            url = url_entry.get_text().strip()
            run_cmd = run_entry.get_text().strip()
            stop_cmd = stop_entry.get_text().strip()
            build_cmd = build_entry.get_text().strip()
            open_vscode = vscode_cb.get_active()
            if not name:
                return

            selected_stacks = [s_name for s_name, cb in check_buttons.items() if cb.get_active()]
            if not selected_stacks:
                selected_stacks = ["Default"]

            pid = item_data.get("id")
            self.proj_mgr.add_or_update_project(
                name=name,
                path=path,
                stacks=selected_stacks,
                url=url,
                run_cmd=run_cmd,
                stop_cmd=stop_cmd,
                build_cmd=build_cmd,
                desc=item_data.get("desc", ""),
                open_vscode=open_vscode,
                proj_id=pid
            )
            dialog.close()
            self.refresh_all()
            self.set_status(f"✓ Saved {name} (Groups: {', '.join(selected_stacks)})")
            
        save_btn.connect("clicked", lambda _: save())
        
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.add_css_class("btn-secondary")
        cancel_btn.connect("clicked", lambda _: dialog.close())
        
        btn_box.append(save_btn)
        btn_box.append(cancel_btn)
        box.append(btn_box)
        
        scrolled.set_child(box)
        dialog.set_child(scrolled)
        dialog.present()

    def show_logs_dialog(self, item):
        name = item.get("name", "Unnamed")
        pid = item.get("id")
        raw_path = item.get("path", "")
        is_running = self.proj_mgr.check_status(item) == "RUNNING"

        dialog = Gtk.Window(transient_for=self)
        dialog.set_title(f"Logs • {name}")
        dialog.set_default_size(920, 600)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.add_css_class("logs-modal-window")

        # State tracking
        timer_id = [None]
        auto_refresh = [True]
        active_level = ["all"]       # "all", "error", "warn", "info"
        search_kw = [""]
        raw_lines = [""]
        current_tail = [250]
        is_fetching = [False]

        # ------------------ 1. Header Bar ------------------
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.add_css_class("logs-modal-header")

        # Left: Icon, Title, Status & Path
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_box.set_hexpand(True)

        row_t = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        t_icon = Gtk.Image.new_from_icon_name("utilities-terminal-symbolic")
        row_t.append(t_icon)

        t_lbl = Gtk.Label(label=f"Logs • {name}", xalign=0)
        t_lbl.add_css_class("brand-title")
        row_t.append(t_lbl)

        s_badge = Gtk.Label(label="● RUNNING" if is_running else "○ STOPPED")
        s_badge.add_css_class("status-badge-running" if is_running else "status-badge-stopped")
        row_t.append(s_badge)

        title_box.append(row_t)

        sub_lbl = Gtk.Label(label=f"📂 {raw_path}", xalign=0)
        sub_lbl.add_css_class("service-path")
        sub_lbl.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        sub_lbl.set_max_width_chars(60)
        title_box.append(sub_lbl)
        header_box.append(title_box)

        # Right: Action Controls
        # Live Tail Toggle Button
        live_btn = Gtk.Button()
        live_btn.add_css_class("btn-secondary")
        live_btn.add_css_class("logs-live-active")
        b_live = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        live_dot = Gtk.Label(label="●")
        b_live.append(live_dot)
        live_lbl = Gtk.Label(label="Live Tail (2s)")
        b_live.append(live_lbl)
        live_btn.set_child(b_live)
        live_btn.set_tooltip_text("Toggle automatic 2-second background refresh")
        header_box.append(live_btn)

        # Refresh Button
        refresh_btn = Gtk.Button()
        refresh_btn.add_css_class("btn-icon")
        refresh_btn.set_child(Gtk.Image.new_from_icon_name("view-refresh-symbolic"))
        refresh_btn.set_tooltip_text("Refresh logs now")
        header_box.append(refresh_btn)

        # Copy Logs Button
        copy_btn = Gtk.Button()
        copy_btn.add_css_class("btn-secondary")
        b_copy = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        b_copy.append(Gtk.Image.new_from_icon_name("edit-copy-symbolic"))
        copy_lbl = Gtk.Label(label="Copy All")
        b_copy.append(copy_lbl)
        copy_btn.set_child(b_copy)
        copy_btn.set_tooltip_text("Copy full log output to clipboard")
        header_box.append(copy_btn)

        # Clear View Button
        clear_btn = Gtk.Button()
        clear_btn.add_css_class("btn-icon")
        clear_btn.set_child(Gtk.Image.new_from_icon_name("edit-clear-symbolic"))
        clear_btn.set_tooltip_text("Clear current log buffer")
        header_box.append(clear_btn)

        # Close Button
        x_btn = Gtk.Button()
        x_btn.add_css_class("btn-icon")
        x_btn.set_child(Gtk.Image.new_from_icon_name("window-close-symbolic"))
        header_box.append(x_btn)

        main_box.append(header_box)

        # ------------------ 2. Filter & Search Toolbar ------------------
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar.add_css_class("logs-modal-toolbar")

        # Level Filters
        pills_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        btn_all = Gtk.Button(label="All Logs")
        btn_all.add_css_class("logs-filter-pill")
        btn_all.add_css_class("active")
        pills_box.append(btn_all)

        btn_err = Gtk.Button(label="⛔ Errors")
        btn_err.add_css_class("logs-filter-pill")
        pills_box.append(btn_err)

        btn_warn = Gtk.Button(label="⚠️ Warnings")
        btn_warn.add_css_class("logs-filter-pill")
        pills_box.append(btn_warn)

        btn_info = Gtk.Button(label="ℹ Info")
        btn_info.add_css_class("logs-filter-pill")
        pills_box.append(btn_info)

        toolbar.append(pills_box)

        # Search Entry
        search_entry = Gtk.Entry()
        search_entry.add_css_class("modal-input")
        search_entry.set_hexpand(True)
        search_entry.set_placeholder_text("🔍 Filter logs (type keyword to search)...")
        toolbar.append(search_entry)

        # Tail Selector
        tail_combo = Gtk.DropDown.new_from_strings(["Last 100", "Last 250", "Last 500", "Last 1000"])
        tail_combo.set_selected(1) # Default 250
        toolbar.append(tail_combo)

        # Line Count Badge
        count_pill = Gtk.Label(label="0 lines")
        count_pill.add_css_class("logs-count-pill")
        toolbar.append(count_pill)

        main_box.append(toolbar)

        # ------------------ 3. Terminal Log Viewport ------------------
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.add_css_class("logs-terminal-box")

        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.set_monospace(True)
        tv.set_wrap_mode(Gtk.WrapMode.NONE)
        tv.add_css_class("logs-terminal-view")

        buffer = tv.get_buffer()
        tt = buffer.get_tag_table()

        # Tag Definitions for Colorized Terminal Syntax
        t_err = Gtk.TextTag.new("error")
        t_err.set_property("foreground", "#f87171")
        t_err.set_property("weight", 600)
        tt.add(t_err)

        t_warn = Gtk.TextTag.new("warn")
        t_warn.set_property("foreground", "#fbbf24")
        tt.add(t_warn)

        t_info = Gtk.TextTag.new("info")
        t_info.set_property("foreground", "#38bdf8")
        tt.add(t_info)

        t_succ = Gtk.TextTag.new("success")
        t_succ.set_property("foreground", "#34d399")
        tt.add(t_succ)

        t_mut = Gtk.TextTag.new("muted")
        t_mut.set_property("foreground", "#64748b")
        tt.add(t_mut)

        t_norm = Gtk.TextTag.new("normal")
        t_norm.set_property("foreground", "#cbd5e1")
        tt.add(t_norm)

        scrolled.set_child(tv)
        main_box.append(scrolled)

        # ------------------ 4. Footer Bar ------------------
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        footer.add_css_class("logs-modal-footer")

        status_lbl = Gtk.Label(label="● Connected to live log stream", xalign=0)
        status_lbl.add_css_class("service-desc")
        footer.append(status_lbl)

        f_sp = Gtk.Box()
        f_sp.set_hexpand(True)
        footer.append(f_sp)

        scroll_btn = Gtk.Button(label="⬇ Scroll to Bottom")
        scroll_btn.add_css_class("btn-secondary")
        footer.append(scroll_btn)

        close_btn = Gtk.Button(label="Close")
        close_btn.add_css_class("btn-secondary")
        footer.append(close_btn)

        main_box.append(footer)

        # ------------------ Interaction Logic ------------------
        def scroll_to_bottom():
            adj = scrolled.get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())

        scroll_btn.connect("clicked", lambda _: scroll_to_bottom())

        def render_logs():
            raw = raw_lines[0]
            lines = raw.split("\n") if raw else []
            kw = search_kw[0].strip().lower()
            lvl = active_level[0]

            filtered = []
            for line in lines:
                lower = line.lower()
                if lvl == "error":
                    if not any(k in lower for k in ["error", "fatal", "exception", "failed", "crash", "err:"]):
                        continue
                elif lvl == "warn":
                    if not any(k in lower for k in ["warn", "warning", "deprecated"]):
                        continue
                elif lvl == "info":
                    if not any(k in lower for k in ["info", "note", "system", "notice", "ready", "started"]):
                        continue

                if kw and kw not in lower:
                    continue

                filtered.append(line)

            buffer.set_text("")
            iter_end = buffer.get_end_iter()

            for line in filtered:
                lower = line.lower()
                if any(k in lower for k in ["error", "fatal", "exception", "failed", "crash", "err:"]):
                    tag = "error"
                elif any(k in lower for k in ["warn", "warning", "deprecated"]):
                    tag = "warn"
                elif any(k in lower for k in ["ready", "started", "listening", "connected", "success", "✔"]):
                    tag = "success"
                elif line.startswith("===") or line.startswith("---") or line.startswith(">>>"):
                    tag = "muted"
                elif any(k in lower for k in ["info", "note", "system", "notice"]):
                    tag = "info"
                else:
                    tag = "normal"

                buffer.insert_with_tags_by_name(iter_end, line + "\n", tag)
                iter_end = buffer.get_end_iter()

            total_l = len(lines)
            shown_l = len(filtered)
            if shown_l == total_l:
                count_pill.set_text(f"{total_l} lines")
            else:
                count_pill.set_text(f"{shown_l} of {total_l} lines")

            scroll_to_bottom()

        def fetch_logs_async():
            if is_fetching[0]:
                return
            is_fetching[0] = True

            def worker():
                try:
                    text = self.proj_mgr.get_logs(pid, tail=current_tail[0])
                except Exception as e:
                    text = f"Error reading logs: {e}"

                def apply():
                    raw_lines[0] = text
                    render_logs()
                    is_fetching[0] = False
                    status_lbl.set_text(f"● Updated at {time.strftime('%H:%M:%S')}")

                GLib.idle_add(apply)

            threading.Thread(target=worker, daemon=True).start()

        def on_copy_clicked():
            text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
            try:
                clip = Gdk.Display.get_default().get_clipboard()
                clip.set(text)
                copy_lbl.set_text("✓ Copied")
                GLib.timeout_add(1500, lambda: (copy_lbl.set_text("Copy All"), False))
            except Exception as e:
                pass

        copy_btn.connect("clicked", lambda _: on_copy_clicked())

        def on_clear_clicked():
            self.proj_mgr.clear_logs(pid)
            raw_lines[0] = ""
            buffer.set_text("")
            count_pill.set_text("0 lines")
            status_lbl.set_text("○ Logs cleared")

        clear_btn.connect("clicked", lambda _: on_clear_clicked())

        def on_tail_changed(dd, _):
            idx = dd.get_selected()
            tails = [100, 250, 500, 1000]
            current_tail[0] = tails[idx]
            fetch_logs_async()

        tail_combo.connect("notify::selected", on_tail_changed)

        def set_level(lvl, active_btn):
            active_level[0] = lvl
            for b in [btn_all, btn_err, btn_warn, btn_info]:
                b.remove_css_class("active")
            active_btn.add_css_class("active")
            render_logs()

        btn_all.connect("clicked", lambda b: set_level("all", b))
        btn_err.connect("clicked", lambda b: set_level("error", b))
        btn_warn.connect("clicked", lambda b: set_level("warn", b))
        btn_info.connect("clicked", lambda b: set_level("info", b))

        search_entry.connect("changed", lambda e: (search_kw.__setitem__(0, e.get_text()), render_logs()))

        def toggle_live():
            auto_refresh[0] = not auto_refresh[0]
            if auto_refresh[0]:
                live_btn.add_css_class("logs-live-active")
                live_dot.set_text("●")
                live_lbl.set_text("Live Tail (2s)")
                status_lbl.set_text("● Live streaming active")
            else:
                live_btn.remove_css_class("logs-live-active")
                live_dot.set_text("○")
                live_lbl.set_text("Live Paused")
                status_lbl.set_text("○ Live stream paused")

        live_btn.connect("clicked", lambda _: toggle_live())
        refresh_btn.connect("clicked", lambda _: fetch_logs_async())

        def on_dialog_close(*_):
            if timer_id[0]:
                GLib.source_remove(timer_id[0])
                timer_id[0] = None
            dialog.close()
            return False

        x_btn.connect("clicked", lambda _: on_dialog_close())
        close_btn.connect("clicked", lambda _: on_dialog_close())
        dialog.connect("close-request", on_dialog_close)

        def timer_tick():
            if not dialog.get_visible():
                return False
            if auto_refresh[0]:
                fetch_logs_async()
            return True

        timer_id[0] = GLib.timeout_add(2000, timer_tick)

        # Initial fetch
        fetch_logs_async()

        dialog.set_child(main_box)
        dialog.present()


    # ------------------ File System Inspector Helper ------------------
    def inspect_folder(self, folder_path):
        p = Path(folder_path)
        if not p.is_dir():
            return {}

        suggested_stacks = ["Default"]

        info = {
            "name": p.name.replace("-", " ").replace("_", " ").title(),
            "stacks": suggested_stacks,
            "path": str(p),
            "run_cmd": "",
            "stop_cmd": "",
            "build_cmd": "",
            "url": ""
        }

        try:
            files = [f.name for f in p.iterdir() if f.is_file()]
        except Exception:
            files = []

        if "up.sh" in files:
            info["run_cmd"] = "./up.sh"
            try:
                content = (p / "up.sh").read_text()
                m = re.search(r'(https?://[^\s\"\'\>]+)', content)
                if m:
                    info["url"] = m.group(1).rstrip('/')
            except Exception:
                pass

        if "down.sh" in files:
            info["stop_cmd"] = "./down.sh"

        if "docker-compose.yml" in files or "compose.yaml" in files:
            if not info["run_cmd"]:
                info["run_cmd"] = "docker-compose up -d"
            if not info["stop_cmd"]:
                info["stop_cmd"] = "docker-compose down"
            info["build_cmd"] = "docker-compose up --build"

            if not info["url"]:
                try:
                    compose_file = p / ("docker-compose.yml" if "docker-compose.yml" in files else "compose.yaml")
                    content = compose_file.read_text()
                    m = re.search(r'["\']?(\d{4,5}):(\d+)["\']?', content)
                    if m:
                        info["url"] = f"http://localhost:{m.group(1)}"
                except Exception:
                    pass

        elif "package.json" in files:
            if not info["run_cmd"]:
                info["run_cmd"] = "npm run dev"
            if not info["stop_cmd"]:
                info["stop_cmd"] = "pkill -f node"
            if not info["build_cmd"]:
                info["build_cmd"] = "npm run build"
            if not info["url"]:
                info["url"] = "http://localhost:3000"

        return info

    def choose_folder_dialog(self, parent_window, on_chosen):
        try:
            dialog = Gtk.FileDialog(title="Select Project Folder")
            init_dir = Path("/Work") if Path("/Work").exists() else Path.home()
            dialog.set_initial_folder(Gio.File.new_for_path(str(init_dir)))

            def callback(source, result):
                try:
                    gfile = source.select_folder_finish(result)
                    if gfile:
                        path = gfile.get_path()
                        if path:
                            GLib.idle_add(lambda: on_chosen(path))
                except Exception:
                    pass

            dialog.select_folder(parent_window, None, callback)
        except Exception:
            def zenity_worker():
                try:
                    init_dir = "/Work" if Path("/Work").exists() else str(Path.home())
                    res = subprocess.run(
                        ["zenity", "--file-selection", "--directory", f"--filename={init_dir}/", "--title=Select Project Folder"],
                        capture_output=True, text=True
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        selected = res.stdout.strip()
                        GLib.idle_add(lambda: on_chosen(selected))
                except Exception:
                    pass
            threading.Thread(target=zenity_worker, daemon=True).start()

    def open_direct_folder_picker(self):
        def on_folder_selected(folder_path):
            detected = self.inspect_folder(folder_path)
            self.show_add_dialog(detected_item=detected)
        self.choose_folder_dialog(self, on_folder_selected)

class CommandCenterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.github.touchpad.commandcenter")
        self.css_loaded = False

    def load_css(self):
        if not self.css_loaded:
            provider = Gtk.CssProvider()
            provider.load_from_data(CSS.encode('utf-8'))
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            self.css_loaded = True

    def do_activate(self):
        self.load_css()
        windows = self.get_windows()
        if windows:
            win = windows[0]
            win.present()
            win.refresh_all(silent=True)
            return

        win = CommandCenterWindow(self)
        win.present()

if __name__ == "__main__":
    app = CommandCenterApp()
    app.run(sys.argv)
