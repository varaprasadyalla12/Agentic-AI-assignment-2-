"""
Document Parser and Text Chunker for PDFs, Markdown, and Text files.
Preserves page numbers, source provenance, and chunk boundaries.
"""
import os
import re
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    doc_name: str
    page_number: int
    text: str
    token_count: int = 0


class DocumentParser:
    """
    Ingests PDF, TXT, MD, and JSON files and performs semantic chunking.
    """

    def __init__(self, chunk_size: int = 450, chunk_overlap: int = 80):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def parse_file(self, file_path: str) -> List[DocumentChunk]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        doc_name = os.path.basename(file_path)

        if ext == ".pdf":
            return self._parse_pdf(file_path, doc_name)
        elif ext in [".txt", ".md", ".json", ".log"]:
            return self._parse_text_file(file_path, doc_name)
        else:
            # Fallback to plain text attempt
            return self._parse_text_file(file_path, doc_name)

    def parse_raw_text(self, text: str, doc_name: str = "Pasted_Document.txt") -> List[DocumentChunk]:
        return self._chunk_text(text, doc_name=doc_name, page_number=1)

    def _parse_pdf(self, file_path: str, doc_name: str) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    page_chunks = self._chunk_text(
                        text=page_text,
                        doc_name=doc_name,
                        page_number=page_idx + 1,
                    )
                    chunks.extend(page_chunks)
        except Exception as e:
            # Fallback byte extraction if pypdf encounters an issue
            with open(file_path, "rb") as f:
                content = f.read().decode("latin1", errors="ignore")
            # Extract plain text inside BT ... ET if possible
            bt_matches = re.findall(r"BT\s*(.*?)\s*ET", content, re.DOTALL)
            cleaned = " ".join(bt_matches) if bt_matches else content
            chunks = self._chunk_text(cleaned, doc_name=doc_name, page_number=1)
        return chunks

    def _parse_text_file(self, file_path: str, doc_name: str) -> List[DocumentChunk]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return self._chunk_text(content, doc_name=doc_name, page_number=1)

    def _chunk_text(self, text: str, doc_name: str, page_number: int) -> List[DocumentChunk]:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        chunks: List[DocumentChunk] = []
        curr_text = ""
        chunk_idx = 1

        for para in paragraphs:
            # If paragraph itself is larger than chunk size, split by sentences
            if len(para) > self.chunk_size:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sentence in sentences:
                    if len(curr_text) + len(sentence) > self.chunk_size and curr_text:
                        chunk_id = f"{doc_name}_p{page_number}_c{chunk_idx}"
                        chunks.append(DocumentChunk(
                            chunk_id=chunk_id,
                            doc_name=doc_name,
                            page_number=page_number,
                            text=curr_text.strip(),
                            token_count=len(curr_text.split()),
                        ))
                        chunk_idx += 1
                        # Overlap: keep last part of text
                        curr_text = curr_text[-self.chunk_overlap:] + " " + sentence
                    else:
                        curr_text = (curr_text + " " + sentence).strip()
            else:
                if len(curr_text) + len(para) > self.chunk_size and curr_text:
                    chunk_id = f"{doc_name}_p{page_number}_c{chunk_idx}"
                    chunks.append(DocumentChunk(
                        chunk_id=chunk_id,
                        doc_name=doc_name,
                        page_number=page_number,
                        text=curr_text.strip(),
                        token_count=len(curr_text.split()),
                    ))
                    chunk_idx += 1
                    curr_text = curr_text[-self.chunk_overlap:] + "\n\n" + para
                else:
                    curr_text = (curr_text + "\n\n" + para).strip()

        if curr_text.strip():
            chunk_id = f"{doc_name}_p{page_number}_c{chunk_idx}"
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                doc_name=doc_name,
                page_number=page_number,
                text=curr_text.strip(),
                token_count=len(curr_text.split()),
            ))

        return chunks
