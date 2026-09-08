"""---------------------------------------------------------------------------------------
 Module: maya_utils

 Author = Roberta Fischetti

 Date = 2026-08-06

 Description = Reads the current scene in Maya (camera, frame range, resolution).
                Hides and restore Maya's raw clip.
---------------------------------------------------------------------------------------"""
import maya.cmds as cmds


# FUNCTIONS ------------------------------------------------------------------------------
def get_active_camera() -> str:
    """Return the camera used by whichever viewport currently has focus."""
    panel = cmds.getPanel(withFocus=True)
    if not panel or "modelPanel" not in panel:
        panels = cmds.getPanel(type="modelPanel")
        panel = panels[0] if panels else None 

    if not panel:
        raise RuntimeError("No active viewport found -- click into a viewport first.")

    return cmds.modelPanel(panel, query=True, camera=True)


def get_frame_range() -> tuple[int, int]:
    """Return (start, end) from the current playback range."""
    start = cmds.playbackOptions(query=True, minTime=True)
    end = cmds.playbackOptions(query=True, maxTime=True)
    
    return int(start), int(end)


def get_resolution() -> tuple[int, int]:
    """Return (width, height) from the scene's render settings."""
    width = cmds.getAttr("defaultResolution.width")
    height = cmds.getAttr("defaultResolution.height")

    return int(width), int(height)

def hide_all_huds() -> list:
    """
    Hide every HUD currently on screen, including Maya's own built-in
    ones, so the raw capture is a clean plate.

    Returns a list of (name, was_visible) pairs, so everything can be
    put back exactly how it was afterward.
    """
    existing_huds = cmds.headsUpDisplay(query=True, listHeadsUpDisplays=True) 
    huds_saved_state = []

    for hud_name in existing_huds:
        hud_visibility = cmds.headsUpDisplay(hud_name, query=True, visible=True)
        huds_saved_state.append((hud_name, hud_visibility))

        if hud_visibility:
            cmds.headsUpDisplay(hud_name, edit=True, visible=False) # turn the hud off

    return huds_saved_state


def restore_huds(huds_saved_state) -> None:
    """Put every HUD back exactly how it was before the playblast."""
    for hud_name, hud_visibility in huds_saved_state:
        cmds.headsUpDisplay(hud_name, edit=True, visible=hud_visibility)