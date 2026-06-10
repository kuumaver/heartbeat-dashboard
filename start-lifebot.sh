#!/bin/bash
# ============================================================
#  LifeBot Dev Launcher
# ============================================================

# --- Kill any stale processes from previous runs ------------
echo "[LifeBot] Cleaning up old processes..."
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "npm run dev"      2>/dev/null
pkill -f "vite"             2>/dev/null
sleep 2  # give camera/hardware time to fully release

# --- Write backend runner -----------------------------------
cat > /tmp/lifebot-backend.sh << EOF
#!/bin/bash
echo "=== LifeBot Backend ==="
cd /home/lifesg/lifesaving/heartbeat-dashboard/backend
source venv/bin/activate
uvicorn main:app --port 8001
echo
read -p "Backend stopped. Press Enter to close..."
EOF
chmod +x /tmp/lifebot-backend.sh

# --- Write frontend runner ----------------------------------
cat > /tmp/lifebot-frontend.sh << EOF
#!/bin/bash
echo "=== LifeBot Frontend ==="
cd /home/lifesg/lifesaving/heartbeat-dashboard/frontend
npm run dev
echo
read -p "Frontend stopped. Press Enter to close..."
EOF
chmod +x /tmp/lifebot-frontend.sh

# --- Launch -------------------------------------------------
if command -v lxterminal &>/dev/null; then
  lxterminal --title="LifeBot Backend" -e "bash /tmp/lifebot-backend.sh" &
  sleep 2
  lxterminal --title="LifeBot Frontend" -e "bash /tmp/lifebot-frontend.sh" &

elif command -v xfce4-terminal &>/dev/null; then
  xfce4-terminal --title="LifeBot Backend" -e "bash /tmp/lifebot-backend.sh" &
  sleep 2
  xfce4-terminal --title="LifeBot Frontend" -e "bash /tmp/lifebot-frontend.sh" &

elif command -v gnome-terminal &>/dev/null; then
  gnome-terminal --title="LifeBot Backend" -- bash /tmp/lifebot-backend.sh &
  sleep 2
  gnome-terminal --title="LifeBot Frontend" -- bash /tmp/lifebot-frontend.sh &

elif command -v xterm &>/dev/null; then
  xterm -title "LifeBot Backend" -e "bash /tmp/lifebot-backend.sh" &
  sleep 2
  xterm -title "LifeBot Frontend" -e "bash /tmp/lifebot-frontend.sh" &

else
  echo "No terminal emulator found. Run: sudo apt install lxterminal"
  exit 1
fi