"""Unit tests for the chunker."""

from app.services.chunking import chunk_pages
from app.services.parsing import ParsedPage


def test_short_text_is_a_single_chunk():
    pages = [ParsedPage(page=1, text="hello world this is short")]
    chunks = chunk_pages(pages, max_tokens=256, overlap_tokens=40)
    assert len(chunks) == 1
    assert chunks[0].text == "hello world this is short"
    assert chunks[0].page == 1
    assert chunks[0].char_start == 0


def test_long_text_splits_with_overlap():
    words = " ".join(f"w{i}" for i in range(100))
    pages = [ParsedPage(page=None, text=words)]
    # ~10 words per chunk, ~2 overlap -> multiple chunks
    chunks = chunk_pages(pages, max_tokens=13, overlap_tokens=3)
    assert len(chunks) > 1
    # ordinals are contiguous and start at 0
    assert [c.ordinal for c in chunks] == list(range(len(chunks)))
    # consecutive chunks overlap (next starts before previous ends)
    assert chunks[1].char_start < chunks[0].char_end


def test_char_offsets_map_back_to_source():
    text = "alpha beta gamma delta epsilon zeta eta theta"
    pages = [ParsedPage(page=2, text=text)]
    chunks = chunk_pages(pages, max_tokens=5, overlap_tokens=1)
    for chunk in chunks:
        assert text[chunk.char_start : chunk.char_end] == chunk.text
        assert chunk.page == 2


def test_ordinals_span_multiple_pages():
    pages = [
        ParsedPage(page=1, text="first page content here"),
        ParsedPage(page=2, text="second page content here"),
    ]
    chunks = chunk_pages(pages, max_tokens=256, overlap_tokens=40)
    assert [c.page for c in chunks] == [1, 2]
    assert [c.ordinal for c in chunks] == [0, 1]


def test_empty_text_yields_no_chunks():
    assert chunk_pages([ParsedPage(page=None, text="   ")]) == []
