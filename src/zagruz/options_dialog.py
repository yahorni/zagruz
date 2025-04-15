from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QComboBox, QDialog, QFileDialog,
                             QFormLayout, QHBoxLayout, QLineEdit, QPushButton,
                             QStyle, QVBoxLayout, QWidget)

from zagruz.options import format_options, lang_options, theme_options, download_dir_options


class OptionsDialog(QDialog):
    """Application settings dialog"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Options"))
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setMinimumSize(500, 300)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Form section
        form_layout = QFormLayout()

        # Language selection
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(lang_options.values)
        self.lang_combo.setCurrentText(lang_options.selected_text)
        form_layout.addRow(self.tr("Language:"), self.lang_combo)

        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(theme_options.values)
        self.theme_combo.setCurrentText(theme_options.selected_text)
        form_layout.addRow(self.tr("Theme:"), self.theme_combo)

        # Format selection
        self.format_combo = QComboBox()
        self.format_combo.addItems(format_options.values)
        self.format_combo.setCurrentText(format_options.selected_text)
        form_layout.addRow(self.tr("Download Format:"), self.format_combo)

        # Directory selection
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setText(download_dir_options.selected)
        self.dir_input.setReadOnly(True)
        self.dir_btn = QPushButton()
        self.dir_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        self.dir_btn.setToolTip(self.tr("Choose download directory"))

        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.dir_btn)
        form_layout.addRow(self.tr("Download Directory:"), dir_layout)

        layout.addLayout(form_layout)

        # Dialog buttons
        button_box = QHBoxLayout()
        self.save_btn = QPushButton(self.tr("Save"))
        self.cancel_btn = QPushButton(self.tr("Cancel"))
        self.save_btn.setDefault(True)

        button_box.addWidget(self.save_btn)
        button_box.addWidget(self.cancel_btn)
        layout.addLayout(button_box)

        # Connect signals
        self.dir_btn.clicked.connect(self.choose_directory)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def choose_directory(self) -> None:
        """Open directory dialog and set download path"""
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if directory:
            self.dir_input.setText(directory)
