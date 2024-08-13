import os
import sys
import datetime
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import random
import json
import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor
import webbrowser
import threading

# Ensure required packages are installed
required_packages = ['pygame', 'tkinterdnd2', 'mutagen']

def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for package in required_packages:
    install_and_import(package)

from tkinterdnd2 import TkinterDnD, DND_FILES
import pygame
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

# Constants
REQUIRED_PYTHON_VERSION = (3, 6)
LOG_FILE = os.path.join(os.path.expanduser("~"), "script_log.txt")
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), "music_player_settings.json")
ORIGINAL_TITLE = "random.shuffleGUI 1.06.05 BETA"

# Initialize Pygame mixer
pygame.mixer.init()

# Global variables
current_dir = None
song_files = []
current_song = None
song_count = 0
skip_count = 0
start_time = None
prev_songs = []
playlist = []
repeat_enabled = False
music_paused = False
playlist_only_mode = False
playlist_only_not_random_mode = False
dir_select_not_random_mode = False
volume_level = 50
auto_save_job = None
reset_status_job = None
playlist_modified = False

SUPPORTED_FORMATS = ('.mp3', '.wav', '.flac', '.m4a', '.m4b', '.m4p', '.mpc', '.ogg', '.oga', '.mogg', '.raw', '.wma', '.wv', '.webm', '.cda', '.3gp', '.aa', '.aac', '.aax', '.alac', '.aiff', '.dsd', '.mqa')
VIDEO_FORMATS = ('.mp4', '.mkv', '.webm', '.vob', '.avi', '.wmv', '.m2ts', '.ts', '.m4v')

executor = ThreadPoolExecutor(max_workers=os.cpu_count())

def print_and_flush(message):
    print(message, flush=True)

def log_to_file(message):
    with open(LOG_FILE, "a") as file:
        file.write(message + "\n")

def check_python_version():
    if sys.version_info < REQUIRED_PYTHON_VERSION:
        raise Exception(f"Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]} or newer is required. Please consider updating your Python installation.")

def check_pygame_installation():
    try:
        import pygame
        print_and_flush("pygame is installed.")
    except ImportError:
        log_to_file("pygame is not installed. Please install it manually using 'pip install pygame'.")

def check_tkinterdnd2_installation():
    try:
        import tkinterdnd2
        print_and_flush("tkinterdnd2 is installed.")
    except ImportError:
        log_to_file("tkinterdnd2 is not installed. Please install it manually using 'pip install tkinterdnd2'.")
        
def check_mutagen_installation():
    try:
        import mutagen
        print_and_flush("mutagen is installed.")
    except ImportError:
        log_to_file("mutagen is not installed. Please install it manually using 'pip install mutagen'.")

def load_settings():
    global volume_level, current_song, playlist
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            volume_level = settings.get("volume", 50)
            current_song = settings.get("last_played", None)
            playlist = settings.get("playlist", [])
            set_volume(volume_level)
            update_playlist()
    else:
        save_settings()

def save_settings():
    global volume_level, current_song, playlist
    settings = {
        "volume": volume_level,
        "last_played": current_song,
        "playlist": playlist
    }
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

async def auto_load_dir():
    global current_dir, song_files, song_count, skip_count, start_time
    current_dir = '/mnt/HDD/Music'  # Linux directory adjustment
    await load_songs_from_directory(current_dir)

async def load_songs_from_directory(directory):
    global song_files, song_count, skip_count, start_time

    song_files = []
    loop = asyncio.get_event_loop()
    song_files = await loop.run_in_executor(executor, lambda: [
        os.path.abspath(os.path.join(root, file))
        for root, dirs, files in os.walk(directory)
        for file in sorted(files)
        if file.endswith(SUPPORTED_FORMATS)
    ])

    if not song_files:
        update_status_label("No songs found in the selected directory")
        return

    song_count = 0
    skip_count = 0
    start_time = datetime.datetime.now()
    await skip_song()

async def play_song(song_path):
    global current_song, song_count, prev_songs
    try:
        pygame.mixer.music.load(song_path)
        pygame.mixer.music.play()
        current_song = song_path
        prev_songs.append(song_path)
        song_count += 1
        update_playing_label(song_path)
        save_settings()
        update_status_label(f"Playing: {os.path.basename(song_path)}")
    except pygame.error as e:
        update_error_label(f"Error playing song: {str(e)}")
        log_to_file(f"Error playing song: {str(e)}")

def pause_music():
    global music_paused
    try:
        pygame.mixer.music.pause()
        music_paused = True
        pause_button.config(text="Pause: On", fg="green")
        update_status_label("Music Paused")
        update_error_label("Music is paused, cannot skip")
    except Exception as e:
        update_error_label(f"Error pausing music: {str(e)}")
        log_to_file(f"Error pausing music: {str(e)}")

def unpause_music():
    global music_paused
    try:
        if current_song is not None:
            pygame.mixer.music.unpause()
            music_paused = False
            pause_button.config(text="Pause: Off", fg="red")
            update_status_label("Music Resumed")
    except Exception as e:
        update_error_label(f"Error unpausing music: {str(e)}")
        log_to_file(f"Error unpausing music: {str(e)}")

def set_volume(level):
    global volume_level
    try:
        volume_level = int(level)
        pygame.mixer.music.set_volume(volume_level / 100)
        volume_label.config(text=f"Volume: {volume_level}%")
        save_settings()
    except Exception as e:
        update_error_label(f"Error setting volume: {str(e)}")
        log_to_file(f"Error setting volume: {str(e)}")

def increase_volume():
    if volume_level < 120:
        set_volume(volume_level + 5)

def decrease_volume():
    if volume_level > 0:
        set_volume(volume_level - 5)

async def skip_song():
    global song_files, skip_count, prev_songs, playlist, repeat_enabled, playlist_only_mode, playlist_only_not_random_mode, dir_select_not_random_mode

    try:
        if not song_files and not (repeat_enabled and playlist):
            update_status_label("No songs found in the selected directory")
            return

        if not music_paused:
            if playlist_only_mode and playlist:
                song_file = playlist[skip_count % len(playlist)] if playlist_only_not_random_mode else random.choice(playlist)
            elif song_files:
                song_file = song_files[skip_count % len(song_files)] if dir_select_not_random_mode else random.choice(song_files)
            else:
                song_file = random.choice(playlist) if repeat_enabled else random.choice(song_files)
            await play_song(song_file)
            skip_count += 1
        else:
            update_error_label("Music is paused, cannot skip")
    except Exception as e:
        update_error_label(f"Error skipping song: {str(e)}")
        log_to_file(f"Error skipping song: {str(e)}")

def change_dir():
    global current_dir, song_files, song_count, skip_count, start_time
    try:
        current_dir = filedialog.askdirectory()
        asyncio.run(load_songs_from_directory(current_dir))
    except Exception as e:
        update_error_label(f"Error changing directory: {str(e)}")
        log_to_file(f"Error changing directory: {str(e)}")

def update_status_label(text):
    global reset_status_job
    status_label.config(text=text)
    print_and_flush(text)
    if reset_status_job:
        root.after_cancel(reset_status_job)
    reset_status_job = root.after(10000, lambda: status_label.config(text=ORIGINAL_TITLE))

def update_error_label(text):
    error_label.config(text=text, fg="yellow")
    print_and_flush(text)
    root.after(5000, clear_error_label)
    update_status_label(text)

def clear_error_label():
    error_label.config(text="")

def update_info_label():
    if start_time:
        running_time = datetime.datetime.now() - start_time
    else:
        running_time = datetime.timedelta(seconds=0)
    info_text = f"Song Count: {song_count}, Skip Count: {skip_count}, Current Time: {datetime.datetime.now().strftime('%I:%M %p')}, Date: {datetime.datetime.now().strftime('%m/%d/%Y')}, Running Time: {str(running_time).split('.')[0]}"
    info_label.config(text=info_text, fg="lightgray", font=("Courier", 10))
    print_and_flush(info_text)

def prev_song():
    global prev_songs
    try:
        if len(prev_songs) > 1:
            prev_songs.pop()
            asyncio.run(play_song(prev_songs[-1]))
    except Exception as e:
        update_error_label(f"Error playing previous song: {str(e)}")
        log_to_file(f"Error playing previous song: {str(e)}")

def save_song():
    global current_song, playlist, playlist_modified
    try:
        if current_song:
            playlist.append(current_song)
            playlist_modified = True
            update_playlist()
            save_settings()
            update_status_label("Song Saved")
    except Exception as e:
        update_error_label(f"Error saving song: {str(e)}")
        log_to_file(f"Error saving song: {str(e)}")

def clear_playlist():
    global playlist, playlist_modified
    try:
        playlist = []
        playlist_modified = True
        update_playlist()
        save_settings()
        update_status_label("Playlist Cleared")
    except Exception as e:
        update_error_label(f"Error clearing playlist: {str(e)}")
        log_to_file(f"Error clearing playlist: {str(e)}")

def shuffle_playlist():
    global playlist, playlist_modified
    try:
        random.shuffle(playlist)
        playlist_modified = True
        update_playlist()
        save_settings()
        update_status_label("Playlist Shuffled")
    except Exception as e:
        update_error_label(f"Error shuffling playlist: {str(e)}")
        log_to_file(f"Error shuffling playlist: {str(e)}")

def toggle_repeat():
    global repeat_enabled
    try:
        repeat_enabled = not repeat_enabled
        repeat_button.config(text="Repeat: On" if repeat_enabled else "Repeat: Off", fg="green" if repeat_enabled else "red")
        update_status_label("Repeat " + ("Enabled" if repeat_enabled else "Disabled"))
    except Exception as e:
        update_error_label(f"Error toggling repeat: {str(e)}")
        log_to_file(f"Error toggling repeat: {str(e)}")

def toggle_playlist_only_mode():
    global playlist_only_mode
    try:
        playlist_only_mode = not playlist_only_mode
        playlist_only_button.config(text="Playlist Only: On" if playlist_only_mode else "Playlist Only: Off", fg="green" if playlist_only_mode else "red")
        update_status_label("Playlist Only " + ("Enabled" if playlist_only_mode else "Disabled"))
    except Exception as e:
        update_error_label(f"Error toggling playlist-only mode: {str(e)}")
        log_to_file(f"Error toggling playlist-only mode: {str(e)}")

def toggle_playlist_only_not_random_mode():
    global playlist_only_not_random_mode
    try:
        playlist_only_not_random_mode = not playlist_only_not_random_mode
        playlist_only_not_random_button.config(text="Playlist Only Not Random: On" if playlist_only_not_random_mode else "Playlist Only Not Random: Off", fg="green" if playlist_only_not_random_mode else "red")
        if playlist_only_not_random_mode:
            auto_save_playlist()
        else:
            root.after_cancel(auto_save_job)
        update_status_label("Playlist Only Not Random " + ("Enabled" if playlist_only_not_random_mode else "Disabled"))
    except Exception as e:
        update_error_label(f"Error toggling playlist-only not random mode: {str(e)}")
        log_to_file(f"Error toggling playlist-only not random mode: {str(e)}")

def auto_save_playlist():
    global auto_save_job
    if playlist_only_not_random_mode:
        save_playlist_to_file()
        auto_save_job = root.after(30000, auto_save_playlist)

def toggle_dir_select_not_random_mode():
    global dir_select_not_random_mode
    try:
        dir_select_not_random_mode = not dir_select_not_random_mode
        dir_select_not_random_button.config(text="Dir Select Not Random: On" if dir_select_not_random_mode else "Dir Select Not Random: Off", fg="green" if dir_select_not_random_mode else "red")
        update_status_label("Dir Select Not Random " + ("Enabled" if dir_select_not_random_mode else "Disabled"))
    except Exception as e:
        update_error_label(f"Error toggling directory-select not random mode: {str(e)}")
        log_to_file(f"Error toggling directory-select not random mode: {str(e)}")

def save_playlist_to_file():
    global playlist, playlist_modified
    try:
        if playlist_modified:
            documents_dir = os.path.expanduser("~/Documents")
            with open(os.path.join(documents_dir, 'playlist.json'), 'w') as f:
                json.dump(playlist, f)
            playlist_modified = False
            update_status_label("Playlist saved to file")
    except Exception as e:
        update_error_label(f"Error saving playlist: {str(e)}")
        log_to_file(f"Error saving playlist: {str(e)}")

def load_playlist_from_file():
    global playlist
    try:
        documents_dir = os.path.expanduser("~/Documents")
        with open(os.path.join(documents_dir, 'playlist.json'), 'r') as f:
            playlist = json.load(f)
        update_playlist()
        update_status_label("Playlist loaded from file")
    except Exception as e:
        update_error_label(f"Error loading playlist: {str(e)}")
        log_to_file(f"Error loading playlist: {str(e)}")

def play_selected_song(event):
    try:
        if playlist_listbox.curselection():
            selected_song = playlist_listbox.get(playlist_listbox.curselection())
            asyncio.run(play_song(selected_song))
    except Exception as e:
        update_error_label(f"Error playing selected song: {str(e)}")
        log_to_file(f"Error playing selected song: {str(e)}")

def update_playlist():
    global playlist

    try:
        scrollbar_position = scrollbar_y.get()
        playlist_listbox.config(bg='black', fg='lightgray')
        playlist_listbox.delete(0, tk.END)
        for song in playlist:
            playlist_listbox.insert(tk.END, song)
        playlist_listbox.yview_moveto(scrollbar_position[0])
    except Exception as e:
        update_error_label(f"Error updating playlist: {str(e)}")
        log_to_file(f"Error updating playlist: {str(e)}")

def update_labels():
    try:
        if pygame.mixer.music.get_busy():
            update_info_label()
            update_playlist()
        else:
            asyncio.run(skip_song())
    except Exception as e:
        update_error_label(f"Error updating labels: {str(e)}")
        log_to_file(f"Error updating labels: {str(e)}")
    root.after(1000, update_labels)

def on_close():
    try:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        root.destroy()
        save_settings()
    except Exception as e:
        update_error_label(f"Error closing application: {str(e)}")
        log_to_file(f"Error closing application: {str(e)}")

# Function to update the playing label without showing drive letter, 'Music' folder, or file extension
def update_playing_label(song_path):
    sections = song_path.split('/')
    filtered_sections = [section for section in sections if section.lower() != 'mnt' and section.lower() != 'hdd' and section.lower() != 'music']
    song_name = filtered_sections[-1].rsplit('.', 1)[0]
    playing_text = " > ".join(filtered_sections[:-1] + [song_name])
    playing_label.config(text=playing_text)
    print_and_flush(f"Playing: {playing_text}")

def drop(event):
    files = root.tk.splitlist(event.data)
    for file in files:
        if os.path.isdir(file):
            process_directory(file)
        elif file.endswith(SUPPORTED_FORMATS):
            playlist.append(file)
    playlist.sort()
    update_playlist()
    save_settings()

def process_directory(directory):
    global playlist
    song_files = []
    for root, dirs, files in os.walk(directory):
        for file in sorted(files):
            if file.endswith(SUPPORTED_FORMATS):
                song_files.append(os.path.abspath(os.path.join(root, file)))

    if song_files:
        documents_dir = os.path.expanduser("~/Documents")
        playlist_file = os.path.join(documents_dir, 'dropped_playlist.json')
        with open(playlist_file, 'w') as f:
            json.dump(song_files, f)
        playlist.extend(song_files)
        update_playlist()
        save_settings()

def search_playlist(event):
    search_term = search_entry.get().lower()
    playlist_listbox.delete(0, tk.END)
    matched_items = []

    for index, song in enumerate(playlist):
        if search_term in song.lower():
            start_idx = song.lower().index(search_term)
            end_idx = start_idx + len(search_term)
            highlighted_song = f"{song[:start_idx]}[{song[start_idx:end_idx]}]{song[end_idx:]}"
            playlist_listbox.insert(tk.END, highlighted_song)
            matched_items.append(index)
        else:
            playlist_listbox.insert(tk.END, song)

    if matched_items:
        playlist_listbox.selection_set(matched_items[0])
        playlist_listbox.see(matched_items[0])
    else:
        playlist_listbox.selection_clear(0, tk.END)

def play_video():
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mkv *.webm *.vob *.avi *.wmv *.m2ts *.ts *.m4v")])
    if file_path:
        ffplay_command = ["ffplay", "-autoexit", "-fs", file_path]
        process = subprocess.Popen(ffplay_command)

        def on_key(event):
            if event.keysym == 'Escape':
                process.terminate()
            elif event.keysym == 'Return' and event.state & 0x0004:
                process.terminate()
                new_ffplay_command = ["ffplay", file_path]
                subprocess.Popen(new_ffplay_command)

        root.bind('<Key>', on_key)

def show_help():
    help_window = tk.Toplevel()
    help_window.title("Help Desk")
    help_window.configure(bg="#1e1e1e")
    
    font_style_label = ("Courier", 10)
    font_style_button = ("Courier", 12, "bold")
    font_style_bold = ("Courier", 12, "bold")

    help_texts = {
        "Pause": "Pauses the currently playing media. Use 'Unpause' to resume playback.",
        "Unpause": "Resumes playback if media is paused.",
        "Skip": "Skips to the next song in your playlist or directory.",
        "Change Dir": "Allows you to select a new directory where your music is located. "
                      "Once selected, you can navigate through this directory to play audio files.",
        "Prev": "Goes back to the previous song in your playlist or directory.",
        "Clear Playlist": "Clears everything from your current playlist. This action cannot be undone.",
        "Shuffle Playlist": "Randomizes the order of songs in your current playlist. "
                            "Use this to mix up your playback sequence.",
        "Repeat": "Repeats the currently playing song until turned off. Use again to toggle off repeat mode.",
        "Save Playlist to File": "Saves your current playlist (including song directory and order) to a JSON file. "
                                 "This allows you to reload your playlist later.",
        "Load Playlist from File": "Loads a saved JSON playlist file. This restores your previously saved playlist, "
                                   "including the directory and order of songs.",
        "Playlist Only": "Enables playback of songs only from your saved playlist. "
                         "Songs outside the playlist will not be played.",
        "Playlist Only Not Random": "Plays songs from your playlist in the order they are listed. "
                                    "This disregards shuffle settings for the playlist.",
        "Dir Select Not Random": "Plays songs from the selected directory in the correct order. "
                                 "This ensures that files are played sequentially as they appear in the directory.",
        "Play Video": "Plays a video media file using FFmpeg. This is the only button that interacts with videos. "
                      "You can use [Right-Click Mouse drag] to seek and [P] for Pause during video playback.",
        "Look Up Currently Playing Song": "Displays information about the currently playing song, "
                                          "such as title, artist, duration, etc.",
        "Play": "Starts playing music from the saved playlist in JSON order. "
                "This button initiates playback based on the order of songs stored in your playlist file."
    }

    help_text = tk.Text(help_window, bg="#1e1e1e", fg="lightgray", font=font_style_label, wrap=tk.WORD, height=50)
    help_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    help_text.tag_configure('bold', font=font_style_bold, foreground="red")
    help_text.tag_configure('underline', underline=False)
    
    for main_word, description in help_texts.items():
        help_text.insert(tk.END, main_word + ":\n", 'bold')
        help_text.insert(tk.END, description + "\n\n", 'underline')

    help_text.config(state=tk.DISABLED)

    back_button = tk.Button(help_window, text="Main", command=help_window.destroy, bg="#3a3a3a", fg="white", font=font_style_button)
    back_button.pack(pady=10)

def look_up_currently_playing_song():
    global current_song
    if current_song:
        try:
            audio = MP3(current_song, ID3=EasyID3)
            song_name = audio.get('title', [os.path.basename(current_song).rsplit('.', 1)[0]])[0]
            band_name = audio.get('artist', [''])[0]
        except Exception as e:
            song_name = os.path.basename(current_song).rsplit('.', 1)[0]
            band_name = ''
            update_error_label(f"Error extracting metadata: {str(e)}")
            log_to_file(f"Error extracting metadata: {str(e)}")
        
        search_query = f"{band_name} {song_name} song"
        webbrowser.open(f"https://www.google.com/search?q={search_query}")

def play_first_song():
    global playlist
    if playlist:
        asyncio.run(play_song(playlist[0]))

# Initialize GUI with TkinterDnD for drag-and-drop
root = TkinterDnD.Tk()
root.title(ORIGINAL_TITLE)
root.configure(bg="#1e1e1e")

font_style_title = ("Courier", 14, "bold")
font_style_label = ("Courier", 11)
font_style_button = ("Courier", 10, "bold")

status_label = tk.Label(root, text=ORIGINAL_TITLE, bg="#1e1e1e", fg="lightgray", font=font_style_title)
status_label.pack(pady=5)
info_label = tk.Label(root, text="", bg="#1e1e1e", fg="lightgray", font=font_style_label)
info_label.pack(pady=5)

buttons_frame1 = tk.Frame(root, bg="#3a3a3a")
buttons_frame1.pack(fill=tk.X, pady=5)
buttons_frame2 = tk.Frame(root, bg="#3a3a3a")
buttons_frame2.pack(fill=tk.X, pady=5)

pause_button = tk.Button(buttons_frame1, text="Pause: Off", bg="#3a3a3a", fg="white", font=font_style_button)
unpause_button = tk.Button(buttons_frame1, text="Unpause", bg="#3a3a3a", fg="white", font=font_style_button)
skip_button = tk.Button(buttons_frame1, text="Skip", bg="#3a3a3a", fg="white", font=font_style_button)
change_dir_button = tk.Button(buttons_frame1, text="Change Dir", bg="#3a3a3a", fg="white", font=font_style_button)
prev_button = tk.Button(buttons_frame1, text="Prev", bg="#3a3a3a", fg="white", font=font_style_button)
save_button = tk.Button(buttons_frame1, text="Save", bg="#3a3a3a", fg="white", font=font_style_button)
clear_button = tk.Button(buttons_frame1, text="Clear Playlist", bg="#3a3a3a", fg="white", font=font_style_button)
shuffle_button = tk.Button(buttons_frame1, text="Shuffle Playlist", bg="#3a3a3a", fg="white", font=font_style_button)
repeat_button = tk.Button(buttons_frame1, text="Repeat: Off", bg="#3a3a3a", fg="white", font=font_style_button)

save_playlist_button = tk.Button(buttons_frame2, text="Save Playlist to File", bg="#3a3a3a", fg="white", font=font_style_button)
load_playlist_button = tk.Button(buttons_frame2, text="Load Playlist from File", bg="#3a3a3a", fg="white", font=font_style_button)
playlist_only_button = tk.Button(buttons_frame2, text="Playlist Only: Off", bg="#3a3a3a", fg="white", font=font_style_button)
playlist_only_not_random_button = tk.Button(buttons_frame2, text="Playlist Only Not Random: Off", bg="#3a3a3a", fg="white", font=font_style_button)
dir_select_not_random_button = tk.Button(buttons_frame2, text="Dir Select Not Random: Off", bg="#3a3a3a", fg="white", font=font_style_button)
play_video_button = tk.Button(buttons_frame2, text="Play Video", bg="#3a3a3a", fg="white", font=font_style_button)
lookup_button = tk.Button(buttons_frame2, text="Look Up Currently Playing Song", bg="#3a3a3a", fg="white", font=font_style_button)
play_button = tk.Button(buttons_frame2, text="Play", bg="#3a3a3a", fg="white", font=font_style_button)
help_button = tk.Button(buttons_frame2, text="Help", bg="#3a3a3a", fg="white", font=font_style_button)

def make_text_green(button):
    button.config(fg='green')

def handle_pause():
    make_text_green(pause_button)
    pause_music()

def handle_unpause():
    make_text_green(unpause_button)
    unpause_music()

def handle_skip():
    make_text_green(skip_button)
    asyncio.run(skip_song())

def handle_change_dir():
    make_text_green(change_dir_button)
    change_dir()

def handle_prev():
    make_text_green(prev_button)
    prev_song()

def handle_save():
    make_text_green(save_button)
    save_song()

def handle_clear():
    make_text_green(clear_button)
    clear_playlist()

def handle_shuffle():
    make_text_green(shuffle_button)
    shuffle_playlist()

def handle_repeat():
    make_text_green(repeat_button)
    toggle_repeat()

def handle_save_playlist():
    make_text_green(save_playlist_button)
    save_playlist_to_file()

def handle_load_playlist():
    make_text_green(load_playlist_button)
    load_playlist_from_file()

def handle_playlist_only():
    make_text_green(playlist_only_button)
    toggle_playlist_only_mode()

def handle_playlist_only_not_random():
    make_text_green(playlist_only_not_random_button)
    toggle_playlist_only_not_random_mode()

def handle_dir_select_not_random():
    make_text_green(dir_select_not_random_button)
    toggle_dir_select_not_random_mode()

def handle_play_video():
    make_text_green(play_video_button)
    play_video()

def handle_lookup():
    make_text_green(lookup_button)
    look_up_currently_playing_song()

def handle_play():
    make_text_green(play_button)
    play_first_song()

def handle_help():
    make_text_green(help_button)
    show_help()

pause_button.config(command=handle_pause)
unpause_button.config(command=handle_unpause)
skip_button.config(command=handle_skip)
change_dir_button.config(command=handle_change_dir)
prev_button.config(command=handle_prev)
save_button.config(command=handle_save)
clear_button.config(command=handle_clear)
shuffle_button.config(command=handle_shuffle)
repeat_button.config(command=handle_repeat)
save_playlist_button.config(command=handle_save_playlist)
load_playlist_button.config(command=handle_load_playlist)
playlist_only_button.config(command=handle_playlist_only)
playlist_only_not_random_button.config(command=handle_playlist_only_not_random)
dir_select_not_random_button.config(command=handle_dir_select_not_random)
play_video_button.config(command=handle_play_video)
lookup_button.config(command=handle_lookup)
play_button.config(command=handle_play)
help_button.config(command=handle_help)

pause_button.pack(side=tk.LEFT, padx=2, pady=2)
unpause_button.pack(side=tk.LEFT, padx=2, pady=2)
skip_button.pack(side=tk.LEFT, padx=2, pady=2)
change_dir_button.pack(side=tk.LEFT, padx=2, pady=2)
prev_button.pack(side=tk.LEFT, padx=2, pady=2)
save_button.pack(side=tk.LEFT, padx=2, pady=2)
clear_button.pack(side=tk.LEFT, padx=2, pady=2)
shuffle_button.pack(side=tk.LEFT, padx=2, pady=2)
repeat_button.pack(side=tk.LEFT, padx=2, pady=2)

save_playlist_button.pack(side=tk.LEFT, padx=2, pady=2)
load_playlist_button.pack(side=tk.LEFT, padx=2, pady=2)
playlist_only_button.pack(side=tk.LEFT, padx=2, pady=2)
playlist_only_not_random_button.pack(side=tk.LEFT, padx=2, pady=2)
dir_select_not_random_button.pack(side=tk.LEFT, padx=2, pady=2)
play_video_button.pack(side=tk.LEFT, padx=2, pady=2)
lookup_button.pack(side=tk.LEFT, padx=2, pady=2)
play_button.pack(side=tk.LEFT, padx=2, pady=2)
help_button.pack(side=tk.LEFT, padx=2, pady=2)

playing_frame = tk.Frame(root, bg="#2e2e2e", bd=2, relief=tk.GROOVE)
playing_frame.pack(pady=10, fill=tk.X)

playing_label = tk.Label(playing_frame, text="", bg="#2e2e2e", fg="lightgray", font=font_style_label, anchor="w")
playing_label.pack(fill=tk.X)

playlist_frame = tk.Frame(root, bg="#1e1e1e")
playlist_frame.pack(pady=10, fill=tk.X, expand=True)

scrollbar_y = tk.Scrollbar(playlist_frame, orient='vertical')
scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

playlist_listbox = tk.Listbox(playlist_frame, height=20, yscrollcommand=scrollbar_y.set, bg="#2e2e2e", fg="lightgray", font=("Courier", 10))
playlist_listbox.bind('<<ListboxSelect>>', play_selected_song)
playlist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar_y['command'] = playlist_listbox.yview
playlist_listbox.config(yscrollcommand=scrollbar_y.set)

volume_frame = tk.Frame(root, bg="#1e1e1e")
volume_frame.pack(pady=10)

volume_label = tk.Label(volume_frame, text="Volume: 50%", bg="#1e1e1e", fg="lightgray", font=font_style_label)
volume_label.pack()

volume_buttons_frame = tk.Frame(volume_frame, bg="#1e1e1e")
volume_buttons_frame.pack()

volume_down_button = tk.Button(volume_buttons_frame, text="-", command=decrease_volume, bg="#3a3a3a", fg="white", font=font_style_button)
volume_down_button.pack(side=tk.LEFT, padx=5)

volume_up_button = tk.Button(volume_buttons_frame, text="+", command=increase_volume, bg="#3a3a3a", fg="white", font=font_style_button)
volume_up_button.pack(side=tk.LEFT, padx=5)

error_label_frame = tk.Frame(root, bg="#1e1e1e")
error_label_frame.pack(fill=tk.X, pady=5, padx=5)

error_label = tk.Label(error_label_frame, text="", bg="#1e1e1e", fg="yellow", font=("Courier", 10, "bold"), anchor="w")
error_label.pack(side=tk.LEFT)

search_frame = tk.Frame(root, bg="#1e1e1e")
search_frame.pack(pady=5, fill=tk.X)
search_label = tk.Label(search_frame, text="Search Playlist:", bg="#1e1e1e", fg="lightgray", font=font_style_label)
search_label.pack(side=tk.LEFT, padx=5)
search_entry = tk.Entry(search_frame, bg="#2e2e2e", fg="lightgray", font=font_style_label)
search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
search_entry.bind('<KeyRelease>', search_playlist)

app_label = tk.Label(root, text="randomly play from your own local music library", bg="#1e1e1e", fg="lightgray", font=("Courier", 10))
app_label.pack(pady=5)

root.protocol("WM_DELETE_WINDOW", on_close)

playlist_listbox.drop_target_register(DND_FILES)
playlist_listbox.dnd_bind('<<Drop>>', drop)

load_settings()
asyncio.run(auto_load_dir())
update_labels()
root.mainloop()

if __name__ == "__main__":
    try:
        check_python_version()
        check_pygame_installation()
        check_tkinterdnd2_installation()
    except Exception as e:
        log_to_file(str(e))
        sys.exit(1)
