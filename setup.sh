#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
USER_NAME="$(whoami)"

echo "=========================================================="
echo " Setting up Project Hub"
echo "=========================================================="

# 1. Add user to 'input' group for trackpad hardware event reading
if groups "$USER_NAME" | grep -q "\binput\b"; then
    echo "[✔] User '$USER_NAME' is already in the 'input' group."
else
    echo "[!] Adding '$USER_NAME' to the 'input' group..."
    echo "    (You may be prompted for your sudo password)"
    sudo usermod -a -G input "$USER_NAME" 2>/dev/null || echo "[!] Could not add to input group without sudo. You can manually run: sudo usermod -a -G input $USER_NAME"
    echo "[✔] Checked 'input' group."
fi

# 2. Make scripts executable
chmod +x "$DIR/run.sh" "$DIR/src/main.py" "$DIR/src/gesture_daemon.py"

# 3. Create Desktop Launcher
mkdir -p ~/.local/share/applications
cat <<EOF > ~/.local/share/applications/project-hub.desktop
[Desktop Entry]
Name=Project Hub
Comment=Local Development Environment Manager & Stack Runner
Exec=$DIR/run.sh
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Development;Utility;
Keywords=project;hub;docker;runner;build;stop;
EOF
chmod +x ~/.local/share/applications/project-hub.desktop
ln -sf ~/.local/share/applications/project-hub.desktop ~/.local/share/applications/touchpad-command-center.desktop
echo "[✔] Installed desktop application launcher: Project Hub."

# 4. Create CLI symlink
mkdir -p ~/.local/bin
ln -sf "$DIR/run.sh" ~/.local/bin/project-hub
ln -sf "$DIR/run.sh" ~/.local/bin/touchpad-command-center
echo "[✔] Installed command line tool: project-hub (alias: touchpad-command-center)"

# 5. Configure GNOME shortcut to Super + K (Command Palette standard) & Ctrl + Alt + P
echo "[*] Setting global shortcut to Super + K and Ctrl + Alt + P..."
gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/', '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/']" 2>/dev/null || true

gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ name 'Project Hub' 2>/dev/null || true
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ command "$DIR/run.sh" 2>/dev/null || true
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ binding '<Super>k' 2>/dev/null || true

gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ name 'Project Hub (Alt)' 2>/dev/null || true
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ command "$DIR/run.sh" 2>/dev/null || true
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ binding '<Control><Alt>p' 2>/dev/null || true
echo "[✔] Keyboard shortcuts configured: [Super + K] and [Ctrl + Alt + P]"

# 6. Create Systemd Service for Touchpad Gesture
mkdir -p ~/.config/systemd/user
cat <<EOF > ~/.config/systemd/user/touchpad-gesture.service
[Unit]
Description=Touchpad Command Center Gesture Daemon
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $DIR/src/gesture_daemon.py
Restart=always
RestartSec=3
Environment=DISPLAY=:0
Environment=WAYLAND_DISPLAY=wayland-0

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
echo "[✔] Created systemd background service: touchpad-gesture.service"

echo ""
echo "=========================================================="
echo " Setup Finished!"
echo "=========================================================="
echo "Quick Test:"
echo " 1. Press [Super + K] or [Ctrl + Alt + P] to open immediately."
echo " 2. Or run: project-hub"
echo " 3. Test gestures: python3 $DIR/src/gesture_daemon.py --test"
echo " 4. Enable background gesture on login:"
echo "    systemctl --user enable --now touchpad-gesture"
echo "=========================================================="

