from enum import Enum


class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"

    @property
    def label_vi(self) -> str:
        labels = {
            "PENDING": "Chờ xử lý",
            "PROCESSING": "Đang dịch",
            "DONE": "Hoàn thành",
            "FAILED": "Thất bại",
        }
        return labels[self.value]

    @property
    def css_class(self) -> str:
        classes = {
            "PENDING": "badge-pending",
            "PROCESSING": "badge-processing",
            "DONE": "badge-done",
            "FAILED": "badge-failed",
        }
        return classes[self.value]
