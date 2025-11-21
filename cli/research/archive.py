"""Research archive CLI flow."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Sequence

from ..data.research_documents import DOCUMENTS, ResearchDocument, iter_by_tier
from pathlib import Path
import tempfile
from ..manuals import display_manual_panel
from ..data.user import DEMO_USER
from ..menu import Menu, MenuItem
from ..utils.text import format_table, get_terminal_width, wrap_paragraphs


@dataclass
class FilterState:
    search: str = ""
    category: str | None = None


def _filter_documents(documents: Iterable[ResearchDocument], state: FilterState) -> list[ResearchDocument]:
    results: list[ResearchDocument] = []
    for document in documents:
        if state.category and document.category != state.category:
            continue
        if state.search:
            text = " ".join(
                [
                    document.title.lower(),
                    document.summary.lower(),
                    " ".join(document.tags).lower(),
                ]
            )
            if state.search.lower() not in text:
                continue
        results.append(document)
    return results


def _describe_document(document: ResearchDocument) -> str:
    width = get_terminal_width()
    header = f"{document.title}\n{'-' * min(len(document.title), width)}"
    meta = format_table(
        [
            ("Classification", document.classification),
            ("Access", document.access_level.upper()),
            ("Category", document.category.title()),
            ("Author", document.author),
            ("Tags", ", ".join(document.tags)),
            ("Summary", wrap_paragraphs(document.summary, width)),
        ]
    )
    body = wrap_paragraphs(document.content, width)
    return f"{header}\n\n{meta}\n\n{body}"


def _list_documents(documents: Sequence[ResearchDocument]) -> None:
    if not documents:
        print("No documents match the current filters. Adjust your search criteria.")
        return
    rows = [(doc.title, doc.category.title(), doc.access_level.upper(), doc.created_at.date().isoformat()) for doc in documents]
    print(format_table([("Title", "Category", "Tier", "Date")] + rows))


def _print_filters(state: FilterState) -> None:
    print("Current filters:")
    print(f"  Search: {state.search or '—'}")
    print(f"  Category: {state.category or 'Any'}")


def run() -> None:
    print("Research Archive — Gamma-tier access granted to demo user.\n")
    state = FilterState()
    tier_documents = list(iter_by_tier(DEMO_USER.subscription_tier))

    def set_search() -> None:
        state.search = input("Enter search text: ").strip()

    def set_category() -> None:
        categories = sorted({doc.category for doc in DOCUMENTS})
        options = categories + ["Any"]
        from ..menu import TerminalMenu

        if TerminalMenu is not None:
            menu = TerminalMenu(options, title="Select category\n")
            selected = menu.show()
            if selected is None:
                return
            choice = options[int(selected)]
        else:
            for idx, label in enumerate(options, start=1):
                print(f"{idx}. {label}")
            raw = input("Choose category: ").strip()
            if not raw:
                return
            try:
                choice = options[int(raw) - 1]
            except Exception:
                print("Invalid choice.")
                return
        state.category = None if choice == "Any" else choice

    def view_document() -> None:
        documents = _filter_documents(tier_documents, state)
        if not documents:
            print("No documents available for current selection.\n")
            return
        menu = Menu(
            "Select document",
            [
                MenuItem(
                    doc.title,
                    # open the document in the shared panel viewer by writing a temp file
                    lambda doc=doc: _open_doc_in_panel(doc),
                )
                for doc in documents
            ],
        )
        menu.show()


    def _open_doc_in_panel(doc: ResearchDocument) -> None:
        # Compose a small markdown file including title and metadata + content
        md = f"# {doc.title}\n\n"
        md += f"**Classification:** {doc.classification}  \n"
        md += f"**Access:** {doc.access_level}  \n"
        md += f"**Author:** {doc.author}  \n\n"
        md += doc.content or ""

        tf = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md")
        try:
            tf.write(md)
            tf.flush()
            tf.close()
            display_manual_panel(Path(tf.name))
        finally:
            try:
                Path(tf.name).unlink()
            except Exception:
                pass

    def show_tag_cloud() -> None:
        documents = _filter_documents(tier_documents, state)
        tags = Counter(tag for doc in documents for tag in doc.tags)
        if not tags:
            print("No tags in current selection.\n")
            return
        rows = [(tag, str(count)) for tag, count in sorted(tags.items(), key=lambda item: (-item[1], item[0]))]
        print(format_table([("Tag", "Count")] + rows) + "\n")

    def list_documents() -> None:
        _print_filters(state)
        _list_documents(_filter_documents(tier_documents, state))

    actions = [
        MenuItem("List documents", list_documents),
        MenuItem("Set search text", set_search),
        MenuItem("Choose category", set_category),
        MenuItem("View document", view_document),
        MenuItem("Tag cloud", show_tag_cloud),
    ]

    menu = Menu("Research Archive", actions)
    menu.show()
