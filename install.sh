#!/bin/bash

set -e

# Check if the current user is root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Define the repository URL and the target directory
REPO_URL="https://github.com/toniok2nd/duck_chat.git"
TARGET_DIR="/usr/local/bin/duck_chat"

# Check if the target directory exists
if [ -d "$TARGET_DIR" ]; then
  echo "Directory $TARGET_DIR already exists. Skipping clone."
else
  echo "Directory $TARGET_DIR does not exist. Cloning repository..."
  # Clone the repository
  git clone "$REPO_URL" "$TARGET_DIR"
  echo "Repository cloned successfully to $TARGET_DIR."
fi

# create venv
# delete alod VENV
cd /usr/local/bin/duck_chat/
if [ -d "$TARGET_DIR/VENV/" ]; then
 rm -Rf "$TARGET_DIR/VENV/"
fi 

python3 -m venv VENV
source VENV/bin/activate
pip install -e .
cd -

# var for alias
DIR="/etc/profile.d"
FILE="$DIR/duck_aliases.sh"
BINARY="start_chat.py"

# set alias
if [ -d "$DIR"]; then
  echo "Directory $DIR does not exist. Creating it now."
else:
  mkdir -p "$DIR"
  chmod 755 "$DIR"
  echo "Directory $DIR created successfully." 
fi

# Check if the file exists
if [ -f "$FILE" ]; then
  echo "File $FILE already exists."
else
  echo "File $FILE does not exist. Creating it now."
  # Create the file with appropriate permissions
  touch "$FILE"
  # Set the correct permissions
  chmod 644 "$FILE"
  echo "File $FILE created successfully."
  # Optionally, you can add some default content to the file
  echo "Adding default content to $FILE"
  echo "alias duck_chat=.$TARGET_DIR/$BINARY" | tee -a "$FILE"
fi

source $FILE
