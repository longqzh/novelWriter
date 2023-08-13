"""
novelWriter – Shared Data Class
===============================

File History:
Created: 2023-08-10 [2.1b2]

This file is a part of novelWriter
Copyright 2018–2023, Veronica Berglyd Olsen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations

import logging

from typing import TYPE_CHECKING
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

if TYPE_CHECKING:  # pragma: no cover
    from novelwriter.guimain import GuiMain
    from novelwriter.gui.theme import GuiTheme
    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)


class SharedData(QObject):

    projectStatusChanged = pyqtSignal(bool)
    projectStatusMessage = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._gui = None
        self._theme = None
        self._project = None
        self._lockedBy = None
        return

    @property
    def mainGui(self) -> GuiMain:
        """Return the Main GUI instance."""
        if self._gui is None:
            raise Exception("UserData class not properly initialised")
        return self._gui

    @property
    def theme(self) -> GuiTheme:
        """Return the GUI Theme instance."""
        if self._theme is None:
            raise Exception("UserData class not properly initialised")
        return self._theme

    @property
    def project(self) -> NWProject:
        """Return the active NWProject instance."""
        if self._project is None:
            raise Exception("UserData class not properly initialised")
        return self._project

    @property
    def hasProject(self) -> bool:
        return self.project.isValid

    @property
    def projectLock(self) -> list | None:
        return self._lockedBy

    ##
    #  Methods
    ##

    def initSharedData(self, gui: GuiMain, theme: GuiTheme) -> None:
        """Initialise the UserData instance. This must be called as soon
        as the Main GUI is created to ensure the SHARED singleton has the
        properties needed for operation.
        """
        self._gui = gui
        self._theme = theme
        self._resetProject()
        logger.debug("SharedData instance initialised")
        return

    def openProject(self, path: str | Path) -> bool:
        """Open a project."""
        if self.project.isValid:
            logger.error("A project is already open")
            return False

        self._lockedBy = None
        status = self.project.openProject(path)
        if status is False:
            # We must cache the lock status before resetting the project
            self._lockedBy = self.project.lockStatus
            self._resetProject()

        return status

    def saveProject(self, autoSave: bool = False) -> bool:
        """Save the current project."""
        if not self.project.isValid:
            logger.error("There is no project open")
            return False
        return self.project.saveProject(autoSave=autoSave)

    def closeProject(self, idleTime: float) -> None:
        """Close the current project."""
        self.project.closeProject(idleTime)
        self._resetProject()
        return

    def unlockProject(self) -> bool:
        """Remove the project lock."""
        return self.project.storage.clearLockFile()

    ##
    #  Internal Slots
    ##

    @pyqtSlot(bool)
    def _emitProjectStatusChange(self, state: bool) -> None:
        """Forward the project status slot."""
        self.projectStatusChanged.emit(state)
        return

    @pyqtSlot(str)
    def _emitProjectStatusMeesage(self, message: str) -> None:
        """Forward the project message slot."""
        self.projectStatusMessage.emit(message)
        return

    ##
    #  Internal Functions
    ##

    def _resetProject(self) -> None:
        """Create a new project instance."""
        from novelwriter.core.project import NWProject
        if isinstance(self._project, NWProject):
            self._project.statusChanged.disconnect()
            self._project.statusMessage.disconnect()
            self._project.deleteLater()
        self._project = NWProject(self.mainGui)
        self._project.statusChanged.connect(self._emitProjectStatusChange)
        self._project.statusMessage.connect(self._emitProjectStatusMeesage)
        return

# END Class SharedData
