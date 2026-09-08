"""---------------------------------------------------------------------------------------
 Module: context_review_core

 Author = Roberta Fischetti

 Date = 2026-09-04

 Description = Join different playblasts together in one review video.
---------------------------------------------------------------------------------------"""

import re
import subprocess
from pathlib import Path
from dataclasses import dataclass

from playblast_manager.ffmpeg_utils import check_ffmpeg_available

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

        # Make sure the movie belongs to this shot folder.
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

    return Shot(
        name=shot_path.name,
        path=shot_path,
        versions=versions,
    )


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

    return Sequence(
        name=sequence_path.name,
        path=sequence_path,
        shots=shots,
    )


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
    ffmpeg_path = check_ffmpeg_available()

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

        subprocess.run(
            command,
            check=True,
        )

    finally:

        if concat_file.exists():
            concat_file.unlink()

    return output_path


    




