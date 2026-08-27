# Document Extractor Engine that reads PDF and extracts the text from it, splitting it into sections based on headings.

import html
import io
import re

import pdfplumber


def clean_text(text: str) -> str:
    text = re.sub(r"_x000D_", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"_x[0-9A-Fa-f]{4}_", " ", text)
    text = html.unescape(text)
    text = text.replace("\\n", "\n")
    text = text.replace("\\'", "'").replace("`", "'")
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    text = re.sub(r"(\d),\s+(\d{3})", r"\1,\2", text)
    text = re.sub(r"(\d+)\s*\.\s*(\d+)", r"\1.\2", text)
    text = re.sub(r"\b(e|i)\s*\.\s*(g|e)\b", r"\1.\2", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = text.split("\n")
    cleaned_lines = []
    buffer = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if buffer:
                cleaned_lines.append(buffer.strip())
                buffer = ""
            cleaned_lines.append("")
        elif re.match(r"^[\W_]*$", stripped):
            continue
        elif buffer and not buffer.endswith((".", ":", "?", "!", '"')):
            buffer += " " + stripped
        else:
            if buffer:
                cleaned_lines.append(buffer.strip())
            buffer = stripped

    if buffer:
        cleaned_lines.append(buffer.strip())

    text = "\n".join(cleaned_lines)
    text = re.sub(r"([a-z0-9.,;:])\n(?=[a-z])", r"\1 ", text)
    text = re.sub(r"\n\n\s+", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(
        r"\(\s*([^)]+?)\s*\)\s*\n\s*([a-zA-Z])",
        r"(\1) \2",
        text,
    )
    text = re.sub(r"(\\n)+", "\n", text)
    return text.strip()


def normalize_heading(text: str) -> str:
    return re.sub(r"\([^)]*\)", "", text).strip().lower()


class DocumentExtractorEngine:
    def extract_pdf_text(self, pdf_bytes: bytes) -> str:
        text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += "\n" + page_text
        return text

    def split_ref_sections(self, text: str) -> dict[str, str]:
        lines = text.split("\n")
        sections = {"summary": [], "research": [], "impact": []}

        current = None

        for line in lines:
            norm = normalize_heading(line)

            match = re.match(
                r"^\s*1\.\s*summary of the impact\s*:?\s*(.*)$",
                norm,
                re.IGNORECASE,
            )
            if match:
                current = "summary"
                remainder = match.group(1).strip()
                if remainder:
                    sections[current].append(remainder)
                continue

            match = re.match(
                r"^\s*2\.\s*underpinning research\s*:?\s*(.*)$",
                norm,
                re.IGNORECASE,
            )
            if match:
                current = "research"
                remainder = match.group(1).strip()
                if remainder:
                    sections[current].append(remainder)
                continue

            if re.match(
                r"^\s*3\.\s*references to the research",
                norm,
                re.IGNORECASE,
            ):
                current = None
                continue

            match = re.match(
                r"^\s*4\.\s*details of the impact\s*:?\s*(.*)$",
                norm,
                re.IGNORECASE,
            )
            if match:
                current = "impact"
                remainder = match.group(1).strip()
                if remainder:
                    sections[current].append(remainder)
                continue

            if re.match(
                r"^\s*5\.\s*sources to corroborate the impact",
                norm,
                re.IGNORECASE,
            ):
                current = None
                continue

            if current is not None:
                sections[current].append(line)

        return {
            "summary": clean_text("\n".join(sections["summary"])),
            "research": clean_text("\n".join(sections["research"])),
            "impact": clean_text("\n".join(sections["impact"])),
        }

    def extract(self, pdf_bytes: bytes) -> dict[str, str]:
        raw_text = self.extract_pdf_text(pdf_bytes)
        return self.split_ref_sections(raw_text)


document_extractor = DocumentExtractorEngine()
