"""Chunking.

A sliding word-window with overlap. Token budgets from config are approximated as
words (~1 token ≈ 0.75 words) — good enough for sizing chunks under the embedding
model's sequence limit without pulling in a tokenizer dependency. Char offsets are
tracked per page so a chunk can be traced back to its exact location in the source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.config import settings
from app.services.parsing import ParsedPage

WORDS_PER_TOKEN = 0.75
_WORD_RE = re.compile(r"\S+")


@dataclass
class Chunk:
    ordinal: int
    text: str
    char_start: int
    char_end: int
    token_count: int
    page: int | None


def _words_from_tokens(tokens: int) -> int:
    return max(1, round(tokens * WORDS_PER_TOKEN))


def chunk_pages(
    pages: list[ParsedPage],
    *,
    max_tokens: int | None = None,
    overlap_tokens: int | None = None,
) -> list[Chunk]:
    """Chunk every page, assigning a document-wide ordinal to each chunk."""
    max_words = _words_from_tokens(max_tokens or settings.chunk_size_tokens)
    overlap_words = _words_from_tokens(overlap_tokens or settings.chunk_overlap_tokens)
    overlap_words = min(overlap_words, max_words - 1) if max_words > 1 else 0
    step = max(1, max_words - overlap_words)

    chunks: list[Chunk] = []
    ordinal = 0
    for page in pages:
        for start, end, text in _windows(page.text, max_words, step):
            word_count = len(_WORD_RE.findall(text))
            chunks.append(
                Chunk(
                    ordinal=ordinal,
                    text=text,
                    char_start=start,
                    char_end=end,
                    token_count=round(word_count / WORDS_PER_TOKEN),
                    page=page.page,
                )
            )
            ordinal += 1
    return chunks


def _windows(text: str, max_words: int, step: int):
    """Yield (char_start, char_end, text) windows over the whitespace-delimited words."""
    matches = list(_WORD_RE.finditer(text))
    if not matches:
        return
    total = len(matches)
    i = 0
    while i < total:
        window = matches[i : i + max_words]
        char_start = window[0].start()
        char_end = window[-1].end()
        yield char_start, char_end, text[char_start:char_end]
        if i + max_words >= total:
            break
        i += step
