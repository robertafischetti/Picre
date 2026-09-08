"""---------------------------------------------------------------------------------------
Module: picreCore - this file is part of Picre

License = Copyright (c) 2026 Roberta Fischetti
This program is free software; you can redistribute it and/or modify it under
the terms of the MIT License as published by the Open Source Initiative.

Author = Roberta Fischetti - fischetti91@gmail.com

Date = 2026-09-08
---------------------------------------------------------------------------------------"""


import os
import re
import getpass
import subprocess
from pathlib import Path
from dataclasses import dataclass

import maya.cmds as cmds

from picre.config import config
from picre import picreUtils

# DATACLASSES ----------------------------------------------------------------------------
@dataclass
class PlayblastVersion:
    """Represents one exported version of a shot."""
    version: int
    path: Path

@dataclass
class Shot:
    """Represents a shot and all its available playblast versions."""
    name: str
    path: Path
    versions: list[PlayblastVersion]

@dataclass
class Sequence:
    """Represents a sequence and all its shots."""
    name: str
    path: Path
    shots: list[Shot]


# VARIABLES ------------------------------------------------------------------------------
SEQUENCE_PATTERN = re.compile(r"^seq\d{3}$")
SHOT_PATTERN = re.compile(r"^sh\d{4}$")
PLAYBLAST_PATTERN = re.compile(r"^(sh\d{4})_v(\d{3})\.mov$",re.IGNORECASE,)
CONTEXT_REVIEW_PATTERN = re.compile(r"^context_review_v(\d{3})\.mov$",re.IGNORECASE,)


# FUNCTIONS ------------------------------------------------------------------------------
# Folders and Filenames functions        
def get_default_project_root() -> str:
    """
    Maya always has a 'current project' folder set. 
    Using it as the starting value for the Project field.
    """
    return cmds.workspace(query=True, rootDirectory=True)

def get_next_version(folder: str, shot: str) -> int:
    """
    Look inside `folder` for files already named like sh0210_v001.mov,
    sh0210_v002.mov, etc., and return the next number to use.
    """
    if not os.path.isdir(folder):
        return 1 

    highest_found = 0
    prefix = shot + "_v"   # e.g. "sh0210_v"

    for filename in os.listdir(folder): 
        if filename.startswith(prefix) and filename.endswith(".mov"):
            version_text = filename[len(prefix):-len(".mov")]
            if version_text.isdigit():
                version_number = int(version_text)
                if version_number > highest_found:
                    highest_found = version_number

    return highest_found + 1

def resolve_output_path(project: str, sequence: str, shot: str) -> tuple[str, str, int]:
    """Work out the full folder + filename + version for this playblast."""
    if not os.path.isabs(project):      
        raise RuntimeError(
            f"Project needs to be a full folder path, starting from the "
            "very top (e.g. /Users/you/Desktop/dragonfly on Mac, or "
            "C:/projects/dragonfly on Windows) -- not just a name.\n"
            "You entered: '{project}'"
        )
    
    folder = config.playblast.folder_pattern.format(
    project=project,
    sequence=sequence,
    shot=shot,
    )

    shot_name = config.playblast.filename_pattern.format(shot=shot)
    version_padding = config.playblast.version_padding
    version_number = get_next_version(folder, shot_name)
    version_text = "v" + str(version_number).zfill(version_padding)
    filename = f"{shot_name}_{version_text}.mov"

    return folder, filename, version_number


# Playblasts functions
def generate_playblast(project: str, sequence: str, shot: str, burnin_fields: list, artist=None) -> str:
    """
    Works out where to save the file, reads the scene, 
    records a clean raw playblast (no Maya HUDs), 
    burns in the selected fields with ffmpeg, and returns the path it saved to.
    """
    folder, filename, version_number = resolve_output_path(project, sequence, shot)

    if not os.path.isdir(folder):
        try:
            os.makedirs(folder)
        except OSError as error:
            raise RuntimeError(
                f"Couldn't create the output folder:\n{folder}\n\n"
                f"Original error: {error}"
            )

    final_path = os.path.join(folder, filename)
    raw_path = os.path.join(folder, "_raw_" + filename)

    camera = picreUtils.get_active_camera()
    frame_start, frame_end = picreUtils.get_frame_range()
    width, height = picreUtils.get_resolution()
    artist = artist or getpass.getuser()

    saved_hud_state = picreUtils.hide_all_huds()
    try:
        actual_raw_path = cmds.playblast(
            filename=raw_path,
            format="qt",
            startTime=frame_start, endTime=frame_end,
            width=width, height=height,
            percent=100, quality=100,
            showOrnaments=False,
            viewer=False,
        )
    finally:
        picreUtils.restore_huds(saved_hud_state)

    picreUtils.burn_in_with_ffmpeg(
        actual_raw_path, 
        final_path, 
        burnin_fields, 
        filename, 
        camera, 
        artist, 
        frame_start
        )
    
    print(f"Saved playblast (v{version_number}) to: {final_path}.")
          
    return final_path

def scan_shot(shot_path: Path) -> Shot | None:
    """Scan a shot folder and return its available playblast versions."""
    if not SHOT_PATTERN.match(shot_path.name):
        return None

    versions = []

    for movie_path in shot_path.iterdir():
        if not movie_path.is_file():
            continue

        match = PLAYBLAST_PATTERN.match(movie_path.name)

        if not match:
            continue

        shot_name = match.group(1)
        version_number = int(match.group(2))

        if shot_name != shot_path.name:
            continue

        versions.append(
            PlayblastVersion(
                version=version_number,
                path=movie_path,
            )
        )

    versions.sort(key=lambda item: item.version)

    if not versions:
        return None

    return Shot(name=shot_path.name, path=shot_path, versions=versions)

def scan_sequence(sequence_path: Path) -> Sequence | None:
    """Scan a sequence folder and return its shots."""
    if not SEQUENCE_PATTERN.match(sequence_path.name):
        return None

    shots = []

    for shot_path in sequence_path.iterdir():
        if not shot_path.is_dir():
            continue

        shot = scan_shot(shot_path)

        if shot is not None:
            shots.append(shot)

    shots.sort(key=lambda item: item.name)

    if not shots:
        return None

    return Sequence(name=sequence_path.name, path=sequence_path, shots=shots)

def scan_movies_folder(movies_path: Path) -> list[Sequence]:
    """Scan the movies folder for sequences, shots and playblast versions."""
    if not movies_path.exists():
        raise FileNotFoundError(
            f"Movies folder does not exist: {movies_path}"
        )

    if not movies_path.is_dir():
        raise NotADirectoryError(
            f"Expected a folder, got: {movies_path}"
        )

    sequences = []

    for sequence_path in movies_path.iterdir():
        if not sequence_path.is_dir():
            continue

        sequence = scan_sequence(sequence_path)

        if sequence is not None:
            sequences.append(sequence)

    sequences.sort(key=lambda item: item.name)

    return sequences

def create_concat_file(movie_paths: list[Path],output_path: Path,) -> Path:
    """Create an FFmpeg concat list file."""
    concat_file = output_path.with_suffix(".txt")

    with concat_file.open("w", encoding="utf-8") as file:
        for movie_path in movie_paths:
            file.write(f"file '{movie_path.as_posix()}'\n")

    return concat_file

def get_next_context_review_path(movies_path: Path) -> Path:
    """Return the next available context review output path."""
    context_reviews_path = movies_path / "context_reviews"

    # Create the folder if it doesn't exist.
    context_reviews_path.mkdir(parents=True,exist_ok=True,)

    existing_versions = []

    for file_path in context_reviews_path.iterdir():
        if not file_path.is_file():
            continue

        match = CONTEXT_REVIEW_PATTERN.match(file_path.name)

        if not match:
            continue

        version_number = int(match.group(1))
        existing_versions.append(version_number)

    # Work out the next version number.
    if existing_versions:
        next_version = max(existing_versions) + 1
    else:
        next_version = 1

    filename = f"context_review_v{next_version:03d}.mov"

    return context_reviews_path / filename

def create_context_review(movie_paths: list[Path],movies_path: Path,) -> Path:
    """Create a versioned context review movie."""
    ffmpeg_path = picreUtils.check_ffmpeg_available()
    output_path = get_next_context_review_path(movies_path)
    concat_file = create_concat_file(movie_paths,output_path,)

    try:
        command = [
            ffmpeg_path,
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(output_path),
        ]

        subprocess.run(command, check=True)

    finally:
        if concat_file.exists():
            concat_file.unlink()

    return output_path