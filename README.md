
![Screenshot 2024-07-21 081038](https://github.com/user-attachments/assets/09259a8a-15af-4b0c-a736-445e53919cd2)


# Media Player

This is my custom media player I created just for fun. The auto-play directory is hardcoded due to permission issues when trying to seek any drive on the computer with a folder named "Music." Hardcoding was the easier and simplest way.

This script can do a lot of stuff:
- Randomly play music
- Play music in order from a picked directory or the playlist (the playlist non-random feature is kind of buggy; it may or may not work, but the non-random feature from selecting the directory works fine)
- Play videos (requires ffmpeg installed)

You can fork this and do whatever you want with it. I don't care; it was just a project I started to see if I could make something, and it turned into something a little bit bigger than I could imagine creating. I couldn't really think of anything else to add to it.

The script obviously requires Python installed. Like with all my scripts, the modules for the pips should automatically install. I never included a feature to upgrade your pip manager, though, but it'll tell you if it's outdated.

## Directory Management

```python
async def auto_load_dir():
    global current_dir, song_files, song_count, skip_count, start_time
    current_dir = 'D:\\Music'
    await load_songs_from_directory(current_dir)
```

![Image_Linux](https://github.com/user-attachments/assets/268d5313-3264-41e9-bbc1-4ce4189e8b34)


## random.shuffleGUI 1.06.05 BETA_Linux.py

# Installing Python 3.12.5 from Source

Follow these steps to install Python 3.12.5 from source on a Linux system.

## 1. Update Your Package List

First, make sure your package list is up to date by running:

```
sudo apt update
sudo apt upgrade
```

## 2. Install Prerequisites

You'll need some development tools and libraries required for building Python from source:

```
sudo apt install -y build-essential libssl-dev zlib1g-dev libncurses5-dev libncursesw5-dev libreadline-dev libsqlite3-dev libgdbm-dev libdb5.3-dev libbz2-dev libexpat1-dev liblzma-dev tk-dev libffi-dev wget
```

## 3. Download the Python Source

Download the Python 3.12.5 source tarball:

```bash
wget https://www.python.org/ftp/python/3.12.5/Python-3.12.5.tgz
```

## 4. Extract the Downloaded Archive

Extract the tarball:

```
tar -xf Python-3.12.5.tgz
```

## 5. Build and Install Python

Change into the Python source directory, then configure the build environment, compile, and install:

```
cd Python-3.12.5
./configure --enable-optimizations
make -j $(nproc)
sudo make altinstall
```

The `--enable-optimizations` flag optimizes the Python binary by running multiple tests. The `make altinstall` command is used instead of `make install` to avoid overwriting the default Python version installed by the system.

## 6. Verify the Installation

Verify that Python 3.12.5 was installed successfully:

```
python3.12 --version
```

## Check Installation Path

Ensure Python 3.12.5 was installed in a directory that’s in your system's PATH. The make altinstall command typically installs Python binaries in /usr/local/bin/. You can verify this by running
```
which python3.12
```
## If it returns a path like /usr/local/bin/python3.12, then Python is correctly installed.

## Create a Symlink (if needed)

If the Python binary isn't found or is in an unexpected location, you can create a symlink in /usr/bin/
```
sudo ln -s /usr/local/bin/python3.12 /usr/bin/python3.12
```
Replace /usr/local/bin/python3.12 with the correct path if it's different.

## Make Python 3.12.5 Available in "Open With"

To ensure Python 3.12.5 is available in the "Open With" dialog:

    Manual Add to "Open With" Menu: You can manually add Python 3.12.5 to the "Open With" menu by creating a .desktop file.

        Create the .desktop File:
```
sudo nano /usr/share/applications/python3.12.desktop
```

## Add the Following Content
```
[Desktop Entry]
Name=Python 3.12
Comment=Run Python 3.12 Scripts
Exec=/usr/local/bin/python3.12 %f
Icon=python3
Terminal=true
Type=Application
MimeType=text/x-python;
Categories=Development;Programming;
```
Save and Exit (Ctrl+X, Y, Enter)

```
sudo update-desktop-database
```

Right-click on a Python script.
Select Properties.
Go to the Open With tab.
Choose Python 3.12 from the list.
Click Set as default.

## Directory Management

```python
async def auto_load_dir():
    global current_dir, song_files, song_count, skip_count, start_time
    current_dir = '/mnt/HDD/Music'  # Linux directory adjustment
    await load_songs_from_directory(current_dir)
```
