from PySide2 import QtWidgets, QtCore, QtGui

from package.image import CustomImage


class Worker(QtCore.QObject):
    """This is a class to create the worker of the threading system."""

    image_converted = QtCore.Signal(object, bool)
    finished = QtCore.Signal()

    def __init__(self, images_to_convert, quality, size, folder):
        """The constructor of the worker.

        :param images_to_convert: The images items to process.
        :param quality: The percentage of quality.
        :param size: The reduction size coefficient.
        :param folder: The name of the output folder.
        :type images_to_convert: QWidgets.QListWidgetItem
        :type quality: int
        :type size: float
        :type folder: str
        """
        super().__init__()
        self.images_to_convert = images_to_convert
        self.quality = quality
        self.size = size
        self.folder = folder
        self.runs = True

    def convert_images(self):
        """Convert the all the images of the list."""
        for image_lw_item in self.images_to_convert:
            if self.runs and not image_lw_item.processed:
                image = CustomImage(path=image_lw_item.text(), folder=self.folder)
                success = image.reduce_image(size=self.size, quality=self.quality)
                self.image_converted.emit(image_lw_item, success)

        self.finished.emit()


class MainWindow(QtWidgets.QWidget):
    """This is a class to create the window of the application."""

    def __init__(self, ctx):
        """The constructor of the window.

        :param ctx: The context of the application.
        :type ctx: ApplicationContext
        """
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle("pyConverter")
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface of the application."""
        self.create_widgets()
        self.modify_widgets()
        self.create_layouts()
        self.add_widgets_to_layouts()
        self.setup_connections()

    def create_widgets(self):
        """Create the widgets of the application."""
        self.lbl_quality = QtWidgets.QLabel("Quality:")
        self.spn_quality = QtWidgets.QSpinBox()
        self.lbl_size = QtWidgets.QLabel("Size:")
        self.spn_size = QtWidgets.QSpinBox()
        self.lbl_outputDir = QtWidgets.QLabel("Output Directory:")
        self.le_outputDir = QtWidgets.QLineEdit()
        self.lw_files = QtWidgets.QListWidget()
        self.btn_convert = QtWidgets.QPushButton("Convert")
        self.lbl_dropInfo = QtWidgets.QLabel("^ Drop your images on the UI")

    def modify_widgets(self):
        """Apply a CSS style sheet to the user interface of the application and modify the widgets."""
        css_file = self.ctx.get_resource("style.css")
        with open(css_file, "r") as f:
            self.setStyleSheet(f.read())

        # Alignment
        self.spn_quality.setAlignment(QtCore.Qt.AlignRight)
        self.spn_size.setAlignment(QtCore.Qt.AlignRight)
        self.le_outputDir.setAlignment(QtCore.Qt.AlignRight)

        # Range
        self.spn_quality.setRange(1, 100)
        self.spn_quality.setValue(75)
        self.spn_size.setRange(1, 100)
        self.spn_size.setValue(50)

        # Divers
        self.le_outputDir.setPlaceholderText("Output directory")
        self.le_outputDir.setText("reduced")
        self.lbl_dropInfo.setVisible(False)

        # Drag & Drop
        self.setAcceptDrops(True)

        # List widget
        self.lw_files.setAlternatingRowColors(True)
        self.lw_files.setSelectionMode(QtWidgets.QListWidget.ExtendedSelection)

    def create_layouts(self):
        """Create the grid layout of the user interface."""
        self.main_layout = QtWidgets.QGridLayout(self)

    def add_widgets_to_layouts(self):
        """Add created widgets to the user interface layout."""
        self.main_layout.addWidget(self.lbl_quality, 0, 0, 1, 1)
        self.main_layout.addWidget(self.spn_quality, 0, 1, 1, 1)
        self.main_layout.addWidget(self.lbl_size, 1, 0, 1, 1)
        self.main_layout.addWidget(self.spn_size, 1, 1, 1, 1)
        self.main_layout.addWidget(self.lbl_outputDir, 2, 0, 1, 1)
        self.main_layout.addWidget(self.le_outputDir, 2, 1, 1, 1)
        self.main_layout.addWidget(self.lw_files, 3, 0, 1, 2)
        self.main_layout.addWidget(self.lbl_dropInfo, 4, 0, 1, 2)
        self.main_layout.addWidget(self.btn_convert, 5, 0, 1, 2)

    def setup_connections(self):
        """Setup the connections."""
        QtWidgets.QShortcut(QtGui.QKeySequence('Backspace'), self.lw_files, self.delete_selected_items)
        self.btn_convert.clicked.connect(self.convert_images)

    def convert_images(self):
        """Convert the images in the list using threading."""
        quality = self.spn_quality.value()
        size = self.spn_size.value() / 100.0
        folder = self.le_outputDir.text() or "reduced"

        lw_items = [self.lw_files.item(index) for index in range(self.lw_files.count())]
        images_to_convert = [1 for lw_item in lw_items if not lw_item.processed]
        if not images_to_convert:
            msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                            "No image to convert",
                                            "All the images are converted.")
            msg_box.exec_()
            return False

        self.thread = QtCore.QThread(self)

        self.worker = Worker(images_to_convert=lw_items,
                             quality=quality,
                             size=size,
                             folder=folder)

        self.worker.moveToThread(self.thread)
        self.worker.image_converted.connect(self.image_converted)
        self.thread.started.connect(self.worker.convert_images)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

        self.prg_dialog = QtWidgets.QProgressDialog("Convert images", "Cancel", 1, len(images_to_convert))
        self.prg_dialog.canceled.connect(self.abort)
        self.prg_dialog.show()

    def abort(self):
        """Stop the thread."""
        self.thread.quit()
        self.worker.runs = False

    def image_converted(self, lw_item, success):
        """Update the image item icon and the progress bar.

        :param lw_item: The image item
        :param success: True if the image is converted else False
        :type lw_item: QWidgets.QListWidgetItem
        :type success: bool
        """
        if success:
            lw_item.setIcon(self.ctx.img_checked)
            lw_item.processed = True
            self.prg_dialog.setValue(self.prg_dialog.value() + 1)

    def delete_selected_items(self):
        """Remove selected image item from the list."""
        for lw_item in self.lw_files.selectedItems():
            row = self.lw_files.row(lw_item)
            self.lw_files.takeItem(row)

    def dragEnterEvent(self, event):
        """Overload the dragEnterEvent method.

        :param event: The event when the cursor enters in the UI.
        :type event: QtGui.QDragEnterEvent

        """
        self.lbl_dropInfo.setVisible(True)
        event.accept()

    def dragLeaveEvent(self, event):
        """Overload the dragLeaveEvent method.

        :param event: The event when the cursor leaves the UI.
        :type event: QtGui.QDragLeaveEvent
        """
        self.lbl_dropInfo.setVisible(False)

    def dropEvent(self, event):
        """Overload the dropEvent method.

        :param event: The event when the user drops files in the UI.
        :type event: QtGui.QDropEvent
        """
        event.accept()
        for url in event.mimeData().urls():
            self.add_file(path=url.toLocalFile())

        self.lbl_dropInfo.setVisible(False)

    def add_file(self, path):
        """Add an image file in the image list to process.

        :param path: The path of the image file.
        :type path: str
        """
        items = [self.lw_files.item(index).text() for index in range(self.lw_files.count())]
        if path not in items:
            lw_item = QtWidgets.QListWidgetItem(path)
            lw_item.setIcon(self.ctx.img_unchecked)
            lw_item.processed = False
            self.lw_files.addItem(lw_item)
