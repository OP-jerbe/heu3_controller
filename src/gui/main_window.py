from pathlib import Path
from socket import SocketType
from typing import Optional

from PySide6.QtCore import (
    QRegularExpression,
    Qt,
    QThread,
    QTimer,
)
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QIcon,
    QRegularExpressionValidator,
)
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qt_material import apply_stylesheet

from helpers.helpers import get_root_dir

from .bg_thread import Worker


class MainWindow(QMainWindow):
    """
    ...
    """

    def __init__(self, version: str) -> None:
        super().__init__()
        self.version = version
        self.serial_number: str = ''

        # Handle background threading
        self.worker_thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.start)
        self.worker.updated.connect(...)
        self.worker_thread.start()
        self.worker.stopped.connect(self.on_worker_stopped)
        self._ready_to_quit = False

        self.create_gui()

    ####################################################################################
    ###################### Main Window GUI Display Methods #############################
    ####################################################################################

    def create_gui(self) -> None:
        window_width = 330
        window_height = 400
        self.setFixedSize(window_width, window_height)
        root_dir: Path = get_root_dir()
        icon_path: str = str(root_dir / 'assets' / 'hvps_icon.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle(f'HVPS Controller (v{self.version})')
        apply_stylesheet(self, theme='dark_lightgreen.xml', invert_secondary=True)
        self.setStyleSheet(
            self.styleSheet() + """QLineEdit, QTextEdit {color: lightgreen;}"""
        )

        main_layout = QGridLayout()

        container = QWidget()
        container.setLayout(main_layout)

        self.setCentralWidget(container)

    ####################################################################################
    ########################## User Guide Menu Option Method ###########################
    ####################################################################################

    def open_user_guide(self) -> None:
        """
        Open the user guide HTML
        """
        print(get_root_dir())

    ####################################################################################
    ################################ Utility Methods ###################################
    ####################################################################################

    def handle_return_pressed(self) -> None:
        focused_widget = self.focusWidget()

        focused_widget.clearFocus()

    ####################################################################################
    ############################ Close Main Window Methods #############################
    ####################################################################################

    def handle_exit(self) -> None:
        """
        Quits the application
        """
        self.close()

    def on_worker_stopped(self) -> None:
        self.worker_thread.quit()
        self.worker_thread.wait()
        self._ready_to_quit = True
        self.close()  # Now close safely

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handles what happens when the main window is closed.
        If self._ready_to_quit is True, close the socket and accept the close event.
        Otherwise, tell the worker to emit the `stop_requested` Signal which will
        tell the thread to stop and then emit the `stopped` Signal which will trigger
        the `on_worker_stopped` method which will terminate the thread and close
        the window.
        """
        if self._ready_to_quit:
            event.accept()
        else:
            self.worker.stop_requested.emit()
            event.ignore()
        super().closeEvent(event)
