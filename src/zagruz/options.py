from abc import ABCMeta, abstractmethod

from PyQt6.QtCore import QObject, QSettings


class _TranslatableOptionsMeta(ABCMeta, type(QObject)):
    """Metaclass to handle QObject and ABC inheritance"""
    pass


class _BaseOptions(QObject, metaclass=_TranslatableOptionsMeta):
    """Base class for translatable option sets"""
    @abstractmethod
    def _get_section(self) -> str:
        pass

    @abstractmethod
    def _get_default_key(self) -> str:
        pass

    @abstractmethod
    def _get_raw_options(self) -> dict[str, str]:
        """Should return dictionary of {key: untranslated_label}"""
        pass

    def __init__(self) -> None:
        super().__init__()
        self.section = self._get_section()
        self.default_key = self._get_default_key()

    @property
    def options(self) -> dict[str, str]:
        """Returns translated options with original keys"""
        return {k: self.tr(v) for k, v in self._get_raw_options().items()}

    @property
    def selected(self) -> str:
        key = QSettings().value(self.section, self.default_key, type=str)
        return key if self.is_valid(key) else self.default_key

    @selected.setter
    def selected(self, value: str) -> None:
        QSettings().setValue(self.section, value)

    def is_valid(self, key: str) -> bool:
        return key in self._get_raw_options()

    @property
    def selected_text(self) -> str:
        return self.options[self.selected]

    @property
    def values(self) -> list[str]:
        return list(self.options.values())

    def from_value(self, value: str) -> str:
        for k, v in self.options.items():
            if value == v:
                return k
        return self.default_key


class _FormatOptions(_BaseOptions):
    def _get_section(self) -> str:
        return "format"

    def _get_default_key(self) -> str:
        return "tv"

    def _get_raw_options(self) -> dict[str, str]:
        return {
            "default": "Default (best)",
            "tv": "TV (mp4, 480p)",
            "audio": "Audio (mp3, 320kbps)"
        }


class _ThemeOptions(_BaseOptions):
    def _get_section(self) -> str:
        return "theme"

    def _get_default_key(self) -> str:
        return "auto"

    def _get_raw_options(self) -> dict[str, str]:
        return {
            "auto": "System",
            "light": "Light",
            "dark": "Dark"
        }


format_options = _FormatOptions()
theme_options = _ThemeOptions()
