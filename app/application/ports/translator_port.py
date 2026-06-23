"""
Application Port — Translator
"""
from abc import ABC, abstractmethod


class ITranslator(ABC):

    @abstractmethod
    def translate(self, text: str) -> str:
        """Dịch một đoạn văn bản. Trả về bản dịch."""
        ...

    @property
    @abstractmethod
    def source_lang(self) -> str:
        """Ngôn ngữ nguồn (vd: 'ru')"""
        ...

    @property
    @abstractmethod
    def target_lang(self) -> str:
        """Ngôn ngữ đích (vd: 'vi')"""
        ...
