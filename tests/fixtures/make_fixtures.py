"""Generate test fixture files programmatically."""

from __future__ import annotations

from pathlib import Path

FIXTURES_DIR = Path(__file__).parent


def make_epub(path: Path) -> None:
    """Create a minimal synthetic EPUB with 3 chapters."""
    try:
        from ebooklib import epub
    except ImportError:
        print("ebooklib not installed, skipping EPUB fixture")
        return

    book = epub.EpubBook()
    book.set_identifier("test-ebook-001")
    book.set_title("The Test Book")
    book.add_author("Test Author")

    chapters = [
        ("Chapter One", "Once upon a time, there was a small rabbit who lived in a cosy burrow. "
         "The rabbit had long ears and a fluffy white tail. Every morning the rabbit would hop "
         "out to find fresh carrots in the meadow nearby. The sun shone brightly and the grass "
         "was green and soft beneath the rabbit's paws. Birds sang sweet songs in the trees above."),
        ("Chapter Two", "One day, the rabbit discovered a strange golden key half-buried in the "
         "mud beside the old oak tree. The key was heavy and cold in the rabbit's paw. What could "
         "it open? The rabbit looked all around but could see no lock. Perhaps the key was magic. "
         "Perhaps it would lead somewhere wonderful. The rabbit decided to keep it safe."),
        ("Chapter Three", "That evening, as the sun set in great orange and pink streaks across "
         "the sky, the rabbit found a tiny door at the base of the old oak tree. The golden key "
         "fit perfectly. Inside was a warm little room with a glowing fireplace and a table laid "
         "with the most delicious carrot soup the rabbit had ever tasted. And from that day on, "
         "the rabbit had two homes and was never lonely again. The end."),
    ]

    spine_items = []
    for i, (title, text) in enumerate(chapters, 1):
        c = epub.EpubHtml(
            title=title,
            file_name=f"chapter{i}.xhtml",
            lang="en",
        )
        c.content = f"<html><body><h1>{title}</h1><p>{text}</p></body></html>"
        book.add_item(c)
        spine_items.append(c)

    book.toc = [epub.Link(c.file_name, c.title, f"chap{i}") for i, c in enumerate(spine_items, 1)]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + spine_items

    epub.write_epub(str(path), book)


def make_txt(path: Path) -> None:
    path.write_text(
        "The little fox ran through the forest, her red tail flashing between the trees. "
        "She was looking for her family who had gone ahead without her.\n\n"
        "After a long search she found them gathered in a clearing, waiting patiently. "
        "Her mother nuzzled her warmly. They were together again and all was well.\n\n"
        "That night they curled up together under the stars and slept deeply until morning.",
        encoding="utf-8",
    )


if __name__ == "__main__":
    make_epub(FIXTURES_DIR / "test_book.epub")
    make_txt(FIXTURES_DIR / "test_book.txt")
    print("Fixtures written to", FIXTURES_DIR)
