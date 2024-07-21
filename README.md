
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
