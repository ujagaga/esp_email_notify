#!/usr/bin/env bash

SERVICE_NAME=email-notify-server.service
SERVICE_FILE=/etc/systemd/system/$SERVICE_NAME
SERVICE_USER=${SUDO_USER:-$(id -un)}

cd "$(dirname "$(realpath "$0")")"

if [[ ! "$SERVICE_USER" =~ ^[a-z_][a-z0-9_-]*[$]?$ ]]; then
  echo "Error: Cannot create services for invalid user: $SERVICE_USER"
  exit 1
fi

# --- Installation Section ---
echo "Installing dependencies..."
if ! sudo apt update -y; then
  echo "Error: Failed to update apt repositories. Aborting installation."
  exit 1
fi

if ! sudo apt install -y python3-pip python3-venv; then
  echo "Error: Failed to install dependencies. Aborting installation."
  exit 1
fi

echo "Creating virtual environment..."
python3 -m venv .venv
if [ $? -ne 0 ]; then
  echo "Error: Failed to create virtual environment. Aborting installation."
  exit 1
fi

echo "Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
  echo "Error: Failed to activate virtual environment. Aborting installation."
  exit 1
fi

echo "Installing Python packages..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
  echo "Error: Failed to install python libraries. Aborting installation."
  exit 1
fi

echo "Deactivating virtual environment..."
deactivate

echo "Making run_server.sh executable..."
chmod +x run_server.sh
if [ $? -ne 0 ]; then
  echo "Error: Failed to make run_server.sh executable. Aborting installation."
  exit 1
fi

# --- Service File Creation ---
echo "Creating systemd service file: $SERVICE_FILE"
cat <<EOT > "$PWD/$SERVICE_NAME"
[Unit]
Description=Email Notify Server
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$SERVICE_USER
ExecStart=$PWD/run_server.sh
WorkingDirectory=$PWD
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOT
if [ $? -ne 0 ]; then
  echo "Error: Failed to create the service file. Aborting installation."
  exit 1
fi
sudo mv "$PWD/$SERVICE_NAME" "$SERVICE_FILE"
if [ $? -ne 0 ]; then
  echo "Error: Failed to move the service file to $SERVICE_FILE. Aborting installation."
  exit 1
fi

# --- Service Management ---
echo "Enabling and starting the service..."
sudo systemctl enable "$SERVICE_NAME"
if [ $? -ne 0 ]; then
  echo "Error: Failed to enable the service. Installation incomplete."
  exit 1
fi
sudo systemctl start "$SERVICE_NAME"
if [ $? -ne 0 ]; then
  echo "Error: Failed to start the service. Installation incomplete."
  exit 1
fi

echo "Email Notify Server installed and started."
echo "If not done yet, sign in once at http://localhost:<PORT>/ on this machine."

exit 0
