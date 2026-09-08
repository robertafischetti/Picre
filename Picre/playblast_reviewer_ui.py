"""---------------------------------------------------------------------------------------
 Module: playblast_reviewer_ui

 Author = Roberta Fischetti

 Date = 2026-09-04

 Description = Playblast Reviewer UI made with Qt Designer.
---------------------------------------------------------------------------------------"""

import os
import webbrowser
from pathlib import Path

from Qt import QtWidgets, QtGui, QtCompat, QtCore

from playblast_manager.playblast_core import get_default_project_root
from playblast_manager.context_review_core import scan_movies_folder, create_context_review


# VARIABLES ------------------------------------------------------------------------------
TITLE = os.path.splitext(os.path.basename(__file__))[0]
CURRENT_PATH = os.path.dirname(__file__)
IMG_PATH = CURRENT_PATH + "/ui/img/{}.png"

window = None


# CLASS ------------------------------------------------------------------------------
class PlayblastReviewerUI(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Playblast In-Context Reviewer")

        # BUILD and LOAD local UI path
        path_ui = "/".join([os.path.dirname(__file__),"ui",TITLE + ".ui"])
        self.wgReviewer = QtCompat.loadUi(path_ui)

        # LOAD button icon
        self.wgReviewer.btn_help.setIcon(QtGui.QPixmap(IMG_PATH.format("btn_help")))

        # SET starting values
        self.set_movies_root()

        # SIGNALS
        self.wgReviewer.btn_refresh.clicked.connect(self.refresh_playblasts)
        self.wgReviewer.tw_playblastsTree.itemChanged.connect(self.handle_item_changed)
        self.wgReviewer.btn_createContextReview.clicked.connect(self.press_create_context_review)
        self.wgReviewer.btn_help.clicked.connect(self.press_help)

        # SHOW the UI
        self.wgReviewer.show()


    # FUNCTIONS
    def set_movies_root(self) -> None:
        """Set the movies folder based on the Maya project."""

        project_root = Path(get_default_project_root())
        self.movies_path = project_root / "movies"
        self.wgReviewer.le_moviesRoot.setText(str(self.movies_path))


    def refresh_playblasts(self) -> None:
        """Scan the movies folder and populate the tree."""

        self.wgReviewer.tw_playblastsTree.clear()

        try:
            self.sequences = scan_movies_folder(self.movies_path)
        except (FileNotFoundError, NotADirectoryError) as error:
            QtWidgets.QMessageBox.warning(self.wgReviewer, "Playblast Reviewer", str(error))
            return

        for sequence in self.sequences:
            self.add_sequence_to_tree(sequence)


    def add_sequence_to_tree(self, sequence):
            """Add a sequence and its shots to the tree."""
    
            sequence_item = QtWidgets.QTreeWidgetItem()
            sequence_item.setText(0, sequence.name)
            sequence_item.setFlags(sequence_item.flags() | QtCore.Qt.ItemIsUserCheckable)
    
            sequence_item.setCheckState(0,QtCore.Qt.Unchecked)
    
            self.wgReviewer.tw_playblastsTree.addTopLevelItem(sequence_item)
    
            for shot in sequence.shots:
                self.add_shot_to_tree(sequence_item,shot)
    
            sequence_item.setExpanded(True)


    def add_shot_to_tree(self, sequence_item, shot):
        """Add a shot and its versions to a sequence."""

        shot_item = QtWidgets.QTreeWidgetItem()
        shot_item.setText(0, shot.name)
        shot_item.setFlags(shot_item.flags() | QtCore.Qt.ItemIsUserCheckable)
        shot_item.setCheckState(0,QtCore.Qt.Unchecked)
        sequence_item.addChild(shot_item)

        # Create the version selector
        version_combo = QtWidgets.QComboBox()

        for version in shot.versions:
            version_combo.addItem(f"v{version.version:03d}",str(version.path))

        # Select the latest version
        version_combo.setCurrentIndex(version_combo.count() - 1)

        # Put the combo box into column 1
        self.wgReviewer.tw_playblastsTree.setItemWidget(shot_item,1,version_combo)


    def handle_item_changed(self, item, column):
        """Handle sequence and shot checkbox changes."""

        if column != 0:
            return

        tree = self.wgReviewer.tw_playblastsTree

        # Prevent recursive signal calls while we update states.
        tree.blockSignals(True)

        try:
            # SEQUENCE CHANGED
            if item.parent() is None:
                state = item.checkState(0)
            # If the user clicks a partially checked sequence,
            # treat it as checked or unchecked.
                if state == QtCore.Qt.PartiallyChecked:
                    state = QtCore.Qt.Checked

                for index in range(item.childCount()):
                    shot_item = item.child(index)
                    shot_item.setCheckState(0,state)

            # SHOT CHANGED
            else:
                sequence_item = item.parent()
                checked_shots = 0
                total_shots = sequence_item.childCount()

                for index in range(total_shots):
                    shot_item = sequence_item.child(index)

                    if shot_item.checkState(0) == QtCore.Qt.Checked:
                        checked_shots += 1

                # No shots selected
                if checked_shots == 0:
                    sequence_item.setCheckState(0,QtCore.Qt.Unchecked)

                # All shots selected
                elif checked_shots == total_shots:
                    sequence_item.setCheckState(0,QtCore.Qt.Checked)

                # Some shots selected
                else:
                    sequence_item.setCheckState(0,QtCore.Qt.PartiallyChecked)

        finally:
            tree.blockSignals(False)

        self.update_selected_shots_count()


    def update_selected_shots_count(self):
        """Update the number of selected shots."""

        selected_count = 0
        tree = self.wgReviewer.tw_playblastsTree

        for sequence_index in range(tree.topLevelItemCount()):
            sequence_item = tree.topLevelItem(sequence_index)

            for shot_index in range(sequence_item.childCount()):
                shot_item = sequence_item.child(shot_index)

                if shot_item.checkState(0) == QtCore.Qt.Checked:
                    selected_count += 1

        self.wgReviewer.tl_shotsSelected.setText(f"Selected: {selected_count} shots")


    def get_selected_playblasts(self) -> list[Path]:
        """Return the movie paths selected in the tree."""

        selected_playblasts = []
        tree = self.wgReviewer.tw_playblastsTree

        for sequence_index in range(tree.topLevelItemCount()):
            sequence_item = tree.topLevelItem(sequence_index)

            for shot_index in range(sequence_item.childCount()):
                shot_item = sequence_item.child(shot_index)

                if shot_item.checkState(0) != QtCore.Qt.Checked:
                    continue

                version_combo = tree.itemWidget(shot_item,1,)

                if version_combo is None:
                    continue

                movie_path = Path(version_combo.currentData())
                selected_playblasts.append(movie_path)

        return selected_playblasts


    def press_create_context_review(self):
        """Create a context review from the selected playblasts."""

        selected_playblasts = self.get_selected_playblasts()

        # Make sure the artist selected something.
        if not selected_playblasts:
            QtWidgets.QMessageBox.warning(self.wgReviewer,"Playblast Reviewer",
                                          "Please select at least one shot.",)

            return

        try:
            output_path = create_context_review(
            movie_paths=selected_playblasts,
            movies_path=self.movies_path,
            )
        except Exception as error:
            QtWidgets.QMessageBox.critical(
                self.wgReviewer,"Context Review Failed",
                f"Could not create the context review.\n\n{error}",
                )
            return

        self.show_success_message(output_path)


    def show_success_message(self, output_path: Path):
        """Show a success message after creating a context review."""

        message_box = QtWidgets.QMessageBox(self.wgReviewer)
        message_box.setWindowTitle("Context Review Created")
        message_box.setIcon(QtWidgets.QMessageBox.Information)
        message_box.setText("Your context review was created successfully!")
        message_box.setInformativeText(f"Output:\n{output_path}")
        open_folder_button = message_box.addButton("Open Output Folder",QtWidgets.QMessageBox.ActionRole,)
        message_box.addButton(QtWidgets.QMessageBox.Ok)
        message_box.exec()

        if message_box.clickedButton() == open_folder_button:
            self.open_output_folder(output_path.parent)


    def open_output_folder(self, folder_path: Path):
        """Open a folder in the operating system file browser."""

        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl.fromLocalFile(str(folder_path)))


    def press_help(self):
            """
            open wiki on Gitub when pressing the help button
            """
            webbrowser.open("https://github.com/robertafischetti/PythonAdvancedAssignments/wiki")