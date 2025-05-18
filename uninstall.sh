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

# rm git folder
if [ -d "$TARGET_DIR" ]; then
  echo "rm $TARGET_DIR foldet"
  rm -rf $TARGET_DIR
else:
  echo "Directory $TARGET_DIR does not exist"
fi

# rm alias file
DIR="/etc/profile.d"
FILE="$DIR/duck_aliases.sh"

# rm alias file
if [ -f "$FILE" ]; then
  echo "File $FILE exists => rm $FILE"
  rm -f $FILE
fi
