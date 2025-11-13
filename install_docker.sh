#!/bin/bash
set -e

echo "--- Starting Docker and Docker Compose installation ---"

# 1. UPDATE PACKAGES
echo "[1/6] Updating package lists..."
sudo apt-get update

# 2. INSTALL PREREQUISITES
echo "[2/6] Installing prerequisite packages..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

# 3. ADD DOCKER'S GPG KEY
echo "[3/6] Adding Docker's official GPG key..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 4. SET UP DOCKER REPOSITORY
echo "[4/6] Setting up Docker's stable repository..."
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# 5. INSTALL DOCKER ENGINE & DOCKER COMPOSE
echo "[5/6] Installing Docker Engine and Docker Compose..."
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
COMPOSE_VERSION="1.29.2" # You can check for the latest version on https://github.com/docker/compose/releases
sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 6. ADD USER TO DOCKER GROUP
echo "[6/6] Adding current user to the 'docker' group..."
sudo usermod -aG docker ${USER}

echo "--- Installation Complete! ---"
echo "SUCCESS: Docker and Docker Compose have been installed."
echo "IMPORTANT: Please log out and log back in for the group changes to take effect."
echo "After logging back in, you can run 'docker run hello-world' to test."
