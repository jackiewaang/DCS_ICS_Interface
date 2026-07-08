# Document Extractor Engine that reads PDF and extracts the text from it, splitting it into sections based on headings.

import html
import io
import re

import pdfplumber


def cleaning_pipeline(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = html.unescape(text)
    text = re.sub(r"http[s]?://", "", text)
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

            if re.match(r"^\s*1\.\s*summary of the impact", norm):
                current = "summary"
                continue

            if re.match(r"^\s*2\.\s*underpinning research", norm):
                current = "research"
                continue

            if re.match(r"^\s*3\.\s*references to the research", norm):
                current = None
                continue

            if re.match(r"^\s*4\.\s*details of the impact", norm):
                current = "impact"
                continue

            if re.match(r"^\s*5\.\s*sources to corroborate the impact", norm):
                current = None
                continue

            if current is not None:
                sections[current].append(line)

        return {
            "summary": cleaning_pipeline("\n".join(sections["summary"])),
            "research": cleaning_pipeline("\n".join(sections["research"])),
            "impact": cleaning_pipeline("\n".join(sections["impact"])),
        }

    def extract(self, pdf_bytes: bytes) -> dict[str, str]:
        raw_text = self.extract_pdf_text(pdf_bytes)
        return self.split_ref_sections(raw_text)


document_extractor = DocumentExtractorEngine()
