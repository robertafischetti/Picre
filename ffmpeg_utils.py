"""---------------------------------------------------------------------------------------
 Module: ffmpeg

 Author = Roberta Fischetti

 Date = 2026-08-06

 Description = Works out the full path to the ffmpeg program and 
                makes sure ffmpeg can actually be found and run.
                Sets up the ffmpeg burn-ins.
---------------------------------------------------------------------------------------"""
import os
import time
import shutil
import subprocess

from playblast_manager.config import config

# VARIABLES ------------------------------------------------------------------------------
font_path = config.platform.font_path
burnins = config.burnins

# FUNCTIONS ------------------------------------------------------------------------------
def find_ffmpeg() -> str:
    """
    Checks ffmpeg_path (from config.yaml), then PATH, then a few common install locations.
    """
    # 1. Explicit path from config
    ffmpeg_path = config.platform.ffmpeg_path
    if ffmpeg_path:
        return ffmpeg_path
    
    # 2. Search PATH
    found = shutil.which("ffmpeg")
    if found:
        return found

    # 3. Search platform defaults
    common_locations = [
        "/opt/homebrew/bin/ffmpeg",   # Homebrew on Apple Silicon Macs
        "/usr/local/bin/ffmpeg",      # Homebrew on Intel Macs
        "/usr/bin/ffmpeg",            # most Linux installs
    ]
    for path in common_locations:
        if os.path.isfile(path):
            return path
 
    raise RuntimeError(
        "Couldn't find ffmpeg anywhere -- not on Maya's PATH, and not in "
        "any of the usual install locations.\n\n"
        "Open a Terminal and run:  which ffmpeg\n"
        "Then either paste the path it prints into ffmpeg_path near the "
        "top of this file, or add it to config.yaml as:\n"
        "    ffmpeg_bin: /the/folder/it/is/in"
    )
 
def check_ffmpeg_available() -> str:
    """
    Make sure ffmpeg can actually be found and run, and return the exact path to use for it.
    """
    ffmpeg_path = find_ffmpeg()
    try:
        subprocess.run(
            [ffmpeg_path, "-version"], 
            capture_output=True, 
            check=True, #if the program exits with an error, raise an exception
        )
    except FileNotFoundError as not_found_error:
        raise RuntimeError(
            "ffmpeg isn't installed, or isn't on your system's PATH.\n"
            "Install it (e.g. 'brew install ffmpeg' on Mac) and try again."
        ) from not_found_error
    except subprocess.CalledProcessError as process_error:
        raise RuntimeError(
            f"ffmpeg is installed but returned an error: {process_error}"
        ) from process_error

    return ffmpeg_path

# Burn-ins Functions (ffmpeg filters)
def escape_drawtext(text: str) -> str:
    """
    ffmpeg's drawtext filter treats backslash, colon, and single-quote
    as special characters -- escape them so a shot/artist name with an
    unusual character in it can't accidentally break the filter string.
    """
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("'", "\\'")
    return text

def one_drawtext(corner: str, literal_text: str) -> str:
    """Build one drawtext filter segment showing literal_text in the given corner."""
    text = escape_drawtext(literal_text)
    position = burnins.corner_positions[corner]
    
    return (
       f"drawtext=fontfile='{font_path}':text='{text}':{position}:fontsize=32:fontcolor=white:"
        "box=1:boxcolor=black@0.5:boxborderw=8"
    )

def build_burnin_filters(enabled_fields: list, shot: str, camera: str, artist: str, maya_frame_start: int) -> str:
    """Build the full ffmpeg -vf filter chain for every enabled burn-in field."""
    filters = []

    if "shot_name" in enabled_fields:
        filters.append(one_drawtext(burnins.corner_fields["shot_name"], shot))
    if "camera_name" in enabled_fields:
        filters.append(one_drawtext(burnins.corner_fields["camera_name"], camera))
    if "artist" in enabled_fields:
        filters.append(one_drawtext(burnins.corner_fields["artist"], artist))
    if "date" in enabled_fields:
        today = time.strftime("%Y-%m-%d")
        filters.append(one_drawtext(burnins.corner_fields["date"], today))
    if "frame" in enabled_fields:
        frame_burnin_position = burnins.corner_positions[burnins.corner_fields["frame"]]#CORNER_POSITIONS[BURNIN_CORNER_FOR_FIELD["frame"]]
        filters.append(
            f"drawtext=fontfile='{font_path}':text='Frame\\: %{{eif\\:n+{maya_frame_start}\\:d}}':{frame_burnin_position}:"
            "fontsize=30:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=8"
        )

    return ",".join(filters)

def burn_in_with_ffmpeg(raw_path: str, final_path: str, enabled_fields: list, shot: str, camera: str, artist: str, frame_start: int) -> None:
    """Run ffmpeg once, drawing every enabled field onto the raw playblast."""
    ffmpeg_path = check_ffmpeg_available()
    filter_chain = build_burnin_filters(enabled_fields, shot, camera, artist, frame_start)

    if not filter_chain:
        # Nothing was ticked -- nothing to draw, just use the raw file as-is.
        # move the file instead of processing it
        os.replace(raw_path, final_path)
        return
    
    codec = config.ffmpeg.codec
    pixel_format = config.ffmpeg.pixel_format
    crf = str(config.ffmpeg.crf)

    command = [
        ffmpeg_path, "-y", "-i", raw_path,                      # -y: overwrite existing file, -i: input file = raw path
        "-vf", filter_chain,                                    # -vf: apply video filter, which is filter chain
        "-c:v", codec, "-pix_fmt", pixel_format, "-crf", crf,   # encoding options and video quality
        final_path,                                             # output
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    # Check if FFmpeg succeeded, 0 means success
    if result.returncode != 0: 
        raise RuntimeError("ffmpeg failed while burning in text:\n" + result.stderr[-1500:])

    os.remove(raw_path)