"""---------------------------------------------------------------------------------------
Module: install - this file is part of Picre

License = Copyright (c) 2026 Roberta Fischetti
This program is free software; you can redistribute it and/or modify it under
the terms of the MIT License as published by the Open Source Initiative.

Author = Roberta Fischetti - fischetti91@gmail.com

Date = 2026-09-08
---------------------------------------------------------------------------------------"""

from pathlib import Path

import maya.mel as mel
import maya.cmds as cmds


# VARIABLES ------------------------------------------------------------------------------
SHELF_NAME = "Picre"

MANAGER_TOOL = "PlayblastManager"
REVIEWER_TOOL = "PlayblastReviewer"

MANAGER_BUTTON_NAME = "PlayblastManagerButton"
REVIEWER_BUTTON_NAME = "PlayblastReviewerButton"

MANAGER_ICON_PATH = Path(__file__).parent / "images" / "playblast_manager_icon_64.png"
REVIEWER_ICON_PATH = Path(__file__).parent / "images" / "playblast_reviewer_icon_64.png"


# FUNCTIONS ------------------------------------------------------------------------------
def install_picre_shelf() -> None:
    """Install the Picre shelf tab."""
    # Get the current Maya shelf layout
    shelf_top_level = mel.eval("$temp = $gShelfTopLevel")

    # Check whether our shelf already exists
    if not cmds.shelfLayout(SHELF_NAME, exists=True):
        cmds.shelfLayout(SHELF_NAME,parent=shelf_top_level)

def install_manager() -> None:
    """Install the Playblast Manager shelf button."""
    # Remove existing button
    if cmds.shelfButton(MANAGER_BUTTON_NAME, exists=True):
        cmds.deleteUI(MANAGER_BUTTON_NAME)

    # Create the shelf button
    cmds.shelfButton(
        MANAGER_BUTTON_NAME,
        parent=SHELF_NAME,
        label=MANAGER_TOOL,
        annotation="Open Playblast Manager",
        image=str(MANAGER_ICON_PATH),
        command="""import playblast_manager.playblast_manager_ui 
classVar = playblast_manager.playblast_manager_ui.PlayblastManagerUI()""",
        sourceType="python"
    )

    print("Playblast Manager installed successfully!")

def install_reviewer() -> None:
    """Install the Playblast Reviewer shelf button."""
    # Remove existing button
    if cmds.shelfButton(REVIEWER_BUTTON_NAME, exists=True):
        cmds.deleteUI(REVIEWER_BUTTON_NAME)

    # Create the shelf button
    cmds.shelfButton(
        REVIEWER_BUTTON_NAME,
        parent=SHELF_NAME,
        label=REVIEWER_TOOL,
        annotation="Open Playblast Reviewer",
        image=str(REVIEWER_ICON_PATH),
        command="""import playblast_manager.playblast_reviewer_ui 
classVar = playblast_manager.playblast_reviewer_ui.PlayblastReviewerUI()""",
        sourceType="python"
    )

    print("Playblast In-Context Reviewer installed successfully!")
