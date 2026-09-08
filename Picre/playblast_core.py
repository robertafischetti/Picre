"""---------------------------------------------------------------------------------------
 Module: playblast

 Author = Roberta Fischetti

 Date = 2026-08-06

 Description = Generates the playblast with burnins.
---------------------------------------------------------------------------------------"""
import os
import getpass

import maya.cmds as cmds

from .maya_utils import *
from .ffmpeg_utils import burn_in_with_ffmpeg
from playblast_manager.config import config


# FUNCTIONS ------------------------------------------------------------------------------
# Folders and Filenames Functions: where the file goes and what version it should be.              
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
        return 1 # : Exits the current function, returning an error status code 

    highest_found = 0
    prefix = shot + "_v"   # e.g. "sh0210_v"

    for filename in os.listdir(folder): # list all files and directories in folder
        if filename.startswith(prefix) and filename.endswith(".mov"):
            # A matching filename looks like "sh0210_v003.mov".
            # Chop off the prefix ("sh0210_v") and the ending (".mov"),
            # leaving just the number part, e.g. "003".
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


# Playblast Functions
def generate_playblast(project: str, sequence: str, shot: str, burnin_fields: list, artist=None) -> str:
    """
    The main function. Works out where to save the file, reads the
    scene, records a clean raw playblast (no HUDs at all), burns in the
    selected fields with ffmpeg, and returns the path it saved to.
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

    camera = get_active_camera()
    frame_start, frame_end = get_frame_range()
    width, height = get_resolution()
    artist = artist or getpass.getuser()

    saved_hud_state = hide_all_huds()
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
        restore_huds(saved_hud_state)

    burn_in_with_ffmpeg(actual_raw_path, final_path, burnin_fields, filename, camera, artist, frame_start)

    print(f"Saved playblast (v{version_number}) to: {final_path}.")
          
    return final_path



