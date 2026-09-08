"""---------------------------------------------------------------------------------------
 Module: playblast_manager_ui

 Author = Roberta Fischetti

 Date = 2026-09-01

 Description = Playblast Manager UI designed with Qt Designer
---------------------------------------------------------------------------------------"""

import os
import sys
import getpass
import webbrowser

from Qt import QtWidgets, QtGui, QtCompat

from playblast_manager.playblast_core import generate_playblast, get_default_project_root


# VARIABLES ------------------------------------------------------------------------------
TITLE = os.path.splitext(os.path.basename(__file__))[0]
CURRENT_PATH = os.path.dirname(__file__)
IMG_PATH = CURRENT_PATH + "/ui/img/{}.png"

window = None


# CLASS ------------------------------------------------------------------------------
class PlayblastManagerUI(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Playblast Manager")
        
        # BUILD and LOAD local ui path
        path_ui = "/".join([os.path.dirname(__file__), "ui", TITLE + ".ui"])
        self.wgPlayblast = QtCompat.loadUi(path_ui)

        # LOAD Button Icon
        self.wgPlayblast.btn_help.setIcon(QtGui.QPixmap(IMG_PATH.format("btn_help")))

        # SET starting values 
        self.wgPlayblast.le_project.setText(get_default_project_root())
        self.wgPlayblast.le_sequence.setText("seq010")
        self.wgPlayblast.le_shot.setText("sh0230")
        self.wgPlayblast.le_artist.setText(getpass.getuser())

        # SIGNAL
        self.wgPlayblast.btn_generatePlayblast.clicked.connect(self.press_btn_generatePlayblast)
        self.wgPlayblast.btn_help.clicked.connect(self.press_help)

        # SHOW the UI
        self.wgPlayblast.show()

    # PRESS
    def press_btn_generatePlayblast(self):
        """
        read which burn-in boxes are ticked
        """
        enabled_fields = []
        if self.wgPlayblast.cb_shotName.isChecked():
            enabled_fields.append("shot_name")
        if self.wgPlayblast.cb_frameNumber.isChecked():
            enabled_fields.append("frame")
        if self.wgPlayblast.cb_artist.isChecked():
            enabled_fields.append("artist")
        if self.wgPlayblast.cb_date.isChecked():
            enabled_fields.append("date")
        if self.wgPlayblast.cb_camera.isChecked():
            enabled_fields.append("camera_name")

        try:
            generate_playblast(
                project=self.wgPlayblast.le_project.text(),
                sequence=self.wgPlayblast.le_sequence.text(),
                shot=self.wgPlayblast.le_shot.text(),
                burnin_fields=enabled_fields,
                artist=self.wgPlayblast.le_artist.text(),
            )
        except RuntimeError as error:
            QtWidgets.QMessageBox.warning(self.wgPlayblast, "Playblast Manager", str(error))

    def press_help(self):
        """
        open wiki on Gitub when pressing the help button
        """
        webbrowser.open("https://github.com/robertafischetti/PythonAdvancedAssignments/wiki")


