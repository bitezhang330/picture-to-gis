# GIF Converter 🎥➡️🖼️

A user-friendly tool for converting videos and images into GIF animations. Supports multiple languages and offers a fun, intuitive interface.

## Features 🌟

- Convert videos (MP4, AVI, etc.) to GIFs
- Convert image sequences (JPG, PNG) to GIFs
- Customize frame rate and playback speed
- Adjust output GIF dimensions
- Intuitive user interface
- Real-time conversion progress display

## Installation 🛠️

1. Ensure Python (3.7+) is installed
2. Clone or download this repository
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage 🚀

Run the main program:

```bash
python gif_converter.py
```

### Video to GIF 🎬➡️🖼️

1. Select a video file in the "Video to GIF" tab
2. Set frame rate and speed
3. Optionally, check "Resize" and set target width and height
4. Choose output path (default is the same as the video file path)
5. Click "Start Conversion"

### Images to GIF 🖼️➡️🖼️

1. Select an image folder or multiple image files in the "Images to GIF" tab
2. Set duration per frame and loop count
3. Optionally, check "Resize" and set target width and height
4. Choose output path
5. Click "Start Conversion"

## System Requirements 💻

- Windows, macOS, or Linux
- Python 3.7+
- PyQt5
- Recommended: At least 4GB RAM

## FAQ ❓

**Q: What if the conversion gets stuck on large video files?**  
A: Large video files require more processing time and memory. Try reducing the frame rate to decrease resource usage.

**Q: Why are my images out of order?**  
A: The program uses natural sorting. Ensure image filenames are consistent (e.g., image1.jpg, image2.jpg).

## License 📄

MIT

## Languages 🌐

- [English](en/README.md)
- [中文](zh/README.md) 