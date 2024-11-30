
# Compress To Discord

This is a tool that allows you to compress videos to fit Discord's file size limitations, making it easy to share large video files in your server or with friends.

The app supports two modes:
- **User Interface**: A user-friendly interface to select video files and compression options.
- **Command Line**: Use commands to compress videos via terminal or script.

## Features
- **Compress videos to fit Discord's file size limits**:
  - **Nitro (500MB)**
  - **Nitro Basic (50MB)**
  - **Normal (10MB)**
  - **Custom Size** (choose your own target size in MB)
- **Supports video compression from the GUI or command line**.

  
 
## Install Stand Alone (Windows and Linux)
Download and extract the package for your platform in the Relases Tab and run the install script

## Install from Git (Linux)

### Requirements
- Python 3.x
- FFmpeg (ensure it's installed and added to your system's PATH)

1.  **Clone the repository**:
	```bash
	git clone https://github.com/YourBoyRory/compress-to-discord.git
	```
2.  **CD to the folder**:
	```bash
	cd compress-to-discord
	```
3.  **Run install script**:
	```bash
	./install.sh
	```

## Usage

### Using the GUI

1.  Run the application with no launch arguments
2. Change compession settings by pressing the cog in the top left corner if desired
3.  In the GUI, drag and drop your source video file
4. Retreive your videos by clicking "Show Output Folder"
    

### Using from Command Line

To compress a video via the command line, use the following syntax:

```bash
compress2cord --nitro <path_to_video>
```

Where `<path_to_video>` is the full path to your source video file. You can also specify other options:

#### Options:

-   **--nitro**: Compress the video to fit Discord Nitro's 500MB limit.
-   **--basic**: Compress the video to fit Discord Nitro Basic's 50MB limit.
-   **--custom** : Compress the video to a custom size in MB (e.g., `--custom 20` for 20MB).

### Example Command:
1.  **Compress to Discord (10MB)**:
    
    ```bash
    compress2cord /path/to/video.mp4
    ```
2.  **Compress to Nitro (500MB)**:
    
    ```bash
    compress2cord --nitro /path/to/video.mp4
    ```
    
3.  **Compress to Nitro Basic (50MB)**:
    
    ```bash
    compress2cord --basic /path/to/video.mp4
    ```
    
4.  **Compress to a Custom Size (20MB)**:
    
    ```bash
    compress2cord --custom 20 /path/to/video.mp4
    ```
    

## How it Works

The app uses FFmpeg to compress videos, adjusting parameters like bitrate, resolution, and audio quality to meet the specified file size limit.
