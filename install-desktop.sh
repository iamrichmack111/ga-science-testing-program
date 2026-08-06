#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ID="ga-science-testing-program"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
DESKTOP_FILE="$HOME/.local/share/applications/$APP_ID.desktop"
cd "$APP_DIR"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
mkdir -p "$HOME/.local/share/applications" "$ICON_DIR" "$HOME/KIDS-HW/grades/ga_science_testing_program/exports"
cp assets/ga-science-logo.svg "$ICON_DIR/$APP_ID.svg"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Georgia Science Testing Program
GenericName=Adaptive Science Assessment
Comment=Georgia standards-aligned adaptive science testing
Exec=$APP_DIR/start-desktop.sh
Path=$APP_DIR
Icon=$ICON_DIR/$APP_ID.svg
Terminal=false
Categories=Education;Science;
Keywords=Science;Georgia;Testing;Grades;Life Science;
StartupNotify=true
EOF
chmod +x start-desktop.sh "$DESKTOP_FILE"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
echo
echo "Installed Georgia Science Testing Program."
echo "Launch from the Pop!_OS application menu or run ./start-desktop.sh"
echo "Default parent PIN: 2468"
