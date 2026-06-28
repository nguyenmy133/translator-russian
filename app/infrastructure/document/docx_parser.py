"""
Infrastructure: python-docx Adapter — implements IDocumentParser
Dịch file Word giữ nguyên format (bold, italic, font size, color, tables)
"""
import logging
import html
import xml.etree.ElementTree as ET
from docx import Document
from app.application.ports.document_port import IDocumentParser, DocumentStats
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class DocxParser(IDocumentParser):
    """
    Đọc .docx, dịch từng paragraph và cell trong table,
    giữ nguyên style của run đầu tiên.
    """

    def translate_and_save(
        self,
        input_path: str,
        output_path: str,
        translate_fn: Callable[[str], str],
    ) -> DocumentStats:
        doc = Document(input_path)
        total_paragraphs = 0
        total_chars = 0

        # ── Dịch body paragraphs ──
        for para in doc.paragraphs:
            stats = self._translate_paragraph(para, translate_fn)
            total_paragraphs += stats[0]
            total_chars += stats[1]

        # ── Dịch tables ──
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        stats = self._translate_paragraph(para, translate_fn)
                        total_paragraphs += stats[0]
                        total_chars += stats[1]

        doc.save(output_path)
        logger.info(
            f"✅ Đã lưu: {output_path} "
            f"({total_paragraphs} đoạn, {total_chars:,} ký tự)"
        )
        return DocumentStats(
            paragraph_count=total_paragraphs,
            char_count=total_chars,
        )

    @staticmethod
    def _apply_style(run, style_data: dict) -> None:
        run.bold = style_data["bold"]
        run.italic = style_data["italic"]
        run.underline = style_data["underline"]
        if style_data["font_name"]:
            run.font.name = style_data["font_name"]
        if style_data["font_size"]:
            run.font.size = style_data["font_size"]
        if style_data["font_color"]:
            try:
                run.font.color.rgb = style_data["font_color"]
            except Exception:
                pass

    @staticmethod
    def _translate_paragraph(para, translate_fn: Callable[[str], str]) -> tuple[int, int]:
        """Dịch một paragraph. Trả về (số đoạn đã dịch, số ký tự)."""
        original = para.text.strip()
        if not original:
            return 0, 0

        # Lọc ra các runs không trống
        non_empty_runs = [r for r in para.runs if r.text]
        
        # Nếu không có runs nào hoặc toàn bộ văn bản rỗng
        if not non_empty_runs:
            try:
                para.text = translate_fn(original)
            except Exception as e:
                logger.warning(f"Lỗi dịch đoạn văn không runs: {e}")
            return 1, len(original)

        # Trích xuất dữ liệu định dạng của các runs gốc
        original_runs_data = []
        html_parts = []
        for run in non_empty_runs:
            font_color = None
            try:
                if run.font.color and run.font.color.type:
                    font_color = run.font.color.rgb
            except Exception:
                pass

            style = {
                "bold": run.bold,
                "italic": run.italic,
                "underline": run.underline,
                "font_name": run.font.name,
                "font_size": run.font.size,
                "font_color": font_color,
            }
            original_runs_data.append(style)
            
            # Mã hóa nội dung text thành HTML an toàn
            escaped_text = html.escape(run.text)
            # Tạo tag span đại diện cho run
            html_parts.append(f'<span id="{len(original_runs_data)-1}">{escaped_text}</span>')

        # Trường hợp tối ưu: chỉ có 1 run duy nhất
        if len(original_runs_data) == 1:
            try:
                translated = translate_fn(original)
                # Xóa toàn bộ runs cũ
                for r in para.runs:
                    r.text = ""
                # Tạo run mới với style cũ
                new_run = para.add_run(translated)
                DocxParser._apply_style(new_run, original_runs_data[0])
            except Exception as e:
                logger.warning(f"Lỗi dịch đoạn văn 1 run: {e}")
            return 1, len(original)

        # Trường hợp nhiều runs: Dịch bằng giải thuật HTML Span Mapping
        html_string = "".join(html_parts)
        try:
            translated_html = translate_fn(html_string)
            
            # Bọc root tag để parse XML
            xml_str = f"<div>{translated_html}</div>"
            root = ET.fromstring(xml_str)
            
            # Xóa sạch nội dung runs cũ
            for r in para.runs:
                r.text = ""

            # Tạo các runs mới dựa trên cây XML đã được dịch và sắp xếp lại
            # 1. Văn bản đứng trước thẻ span đầu tiên
            if root.text:
                new_run = para.add_run(root.text)
                DocxParser._apply_style(new_run, original_runs_data[0])

            # 2. Các thẻ span và phần đuôi (tail) của chúng
            for child in root:
                if child.tag == "span" and "id" in child.attrib:
                    try:
                        run_idx = int(child.attrib["id"])
                        run_style = original_runs_data[run_idx]
                    except (ValueError, IndexError):
                        run_style = original_runs_data[0]

                    # Ghi text trong span
                    new_run = para.add_run(child.text or "")
                    DocxParser._apply_style(new_run, run_style)

                    # Ghi tail (văn bản đứng sau span)
                    if child.tail:
                        new_run_tail = para.add_run(child.tail)
                        DocxParser._apply_style(new_run_tail, run_style)

        except Exception as e:
            logger.warning(f"Lỗi dịch HTML paragraph: {e}. Sử dụng fallback dịch thô.")
            try:
                translated_plain = translate_fn(original)
                # Xóa sạch runs cũ
                for r in para.runs:
                    r.text = ""
                # Tạo run mới áp dụng style của run đầu tiên
                new_run = para.add_run(translated_plain)
                DocxParser._apply_style(new_run, original_runs_data[0])
            except Exception as fallback_err:
                logger.error(f"Lỗi fallback dịch paragraph: {fallback_err}")

        return 1, len(original)
