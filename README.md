# YouTube Media Downloader

A Flask-based web application for downloading YouTube videos and playlists as MP4 videos or MP3 audio files. The application provides real-time download progress updates and supports both single videos and playlists.

## Features

- Download YouTube videos as MP4 files
- Extract audio from YouTube videos as MP3 files
- Support for downloading entire playlists or selected videos from a playlist
- Real-time progress tracking during downloads
- Metadata extraction (title, thumbnail, duration, etc.)
- Simple and intuitive web interface

## Requirements

- Python 3.7+
- yt-dlp
- Flask
- FFmpeg (for audio conversion)

## Installation

1. Clone the repository or download the source code.
2. Install the required dependencies:

```bash
pip install flask yt-dlp
```
3. Ensure FFmpeg is installed on your system and added to your PATH.


## Usage

1. Run the application:

```bash
python main.py
```
2. The application will automatically open in your default web browser at http://127.0.0.1:5001.

In the web interface:

a. Paste a YouTube URL (video or playlist)

b. Select whether to download as video (MP4) or audio (MP3)

c. For playlists, choose specific videos or download all

d. Click "Download" to start the process

