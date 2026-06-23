"""
Application Port — Document Parser
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


@dataclass
class DocumentStats:
    paragraph_count: int
    char_count: int


class IDocumentParser(ABC):

    @abstractmethod
    def translate_and_save(
        self,
        input_path: str,
        output_path: str,
        translate_fn: Callable[[str], str],
    ) -> DocumentStats:
        """
        Đọc document, dịch từng đoạn, lưu ra output_path.
        Trả về thống kê số đoạn và ký tự đã dịch.
        """
        ...
