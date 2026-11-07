"""Convert a training-material PDF to Markdown with a page-image gallery in one step.

Usage:
    python tools/pdf_to_md.py <input.pdf> [output.md]

Pipeline (one step):
  1. Text: markitdown (Python API) converts the PDF to Markdown text.
  2. Figures: PyMuPDF renders every page to <out_stem>_media/pNN.png at 150 dpi.
      Page rendering is chosen over raw embedded-image extraction because printed
      slide decks carry their key figures (plots, block diagrams) as vector art;
      each page render contains everything that page shows. Embedded-image stats
      are probed and reported.
  3. Assembly: every page render is collected in an end gallery under
      "## Page images". (Inline anchoring on page-number footer lines was
      dropped: it is flaky because not every page carries a number.)
  4. A provenance header (source, date, tool versions, caveats) is prepended.

The original PDF is never modified.
"""

import importlib.metadata as im
import os
import sys
from datetime import date


def same_file(src: str, dst: str) -> bool:
    if os.path.normcase(os.path.abspath(src)) == os.path.normcase(os.path.abspath(dst)):
        return True
    try:
        return os.path.samefile(src, dst)
    except FileNotFoundError:
        return False


def clear_page_pngs(media_dir: str):
    """Remove pNN.png files left by earlier runs so the gallery directory only
    contains pages of the current document."""
    for name in os.listdir(media_dir):
        if name.startswith("p") and name.endswith(".png") and name[1:-4].isdigit():
            os.remove(os.path.join(media_dir, name))


def build_header(pdf: str, n: int, media_rel: str, md_ver: str, pymu_ver: str) -> list[str]:
    return [
        "> **Provenance**",
        f"> - Source: `{pdf}`",
        f"> - Converted: {date.today().isoformat()} — markitdown {md_ver} (text) + PyMuPDF {pymu_ver} (page images), one step via `pdf_to_md.py`",
        f"> - Figures: {n} page(s) rendered to `{media_rel}/pNN.png` at 150 dpi, listed in the '## Page images' gallery at the end of this file.",
        "> - Caveats: figure-internal labels can be mangled in the text layer; the page PNGs are authoritative for figures.",
        "> - Originals under `materials/` are never modified.",
    ]


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    pdf = os.path.abspath(sys.argv[1])
    if not os.path.isfile(pdf):
        print(f"[error] not found: {pdf}")
        return 2

    stem = os.path.splitext(os.path.basename(pdf))[0]
    out_md = (
        os.path.abspath(sys.argv[2])
        if len(sys.argv) > 2
        else os.path.abspath(os.path.join("materials", "md", stem + ".md"))
    )
    if same_file(pdf, out_md):
        print(f"[error] input and output refer to the same file: {out_md}")
        return 2

    media_dir = os.path.splitext(out_md)[0] + "_media"
    media_rel = os.path.basename(media_dir)
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    os.makedirs(media_dir, exist_ok=True)
    clear_page_pngs(media_dir)

    # 1) text via markitdown
    from markitdown import MarkItDown

    text = MarkItDown().convert(pdf).text_content
    md_ver = im.version("markitdown")
    print(f"[text] markitdown {md_ver}: {len(text)} chars")

    # 2) page images via PyMuPDF (+ embedded-image probe)
    import pymupdf

    doc = pymupdf.open(pdf)
    try:
        n = len(doc)
        if n == 0:
            print("[error] PDF has no pages")
            return 1
        pymu_ver = getattr(pymupdf, "VersionBind", None) or getattr(pymupdf, "__version__", "?")

        embedded = 0
        for page in doc:
            imgs = page.get_images(full=True)
            embedded += len(imgs)
            if imgs:
                sizes = sorted({(i[2], i[3]) for i in imgs}, reverse=True)
                print(f"[probe] page {page.number + 1}: {len(imgs)} embedded image(s), px {sizes[:4]}")
        print(f"[probe] total embedded images: {embedded}")

        for page in doc:
            page.get_pixmap(dpi=150).save(os.path.join(media_dir, f"p{page.number + 1:02d}.png"))
    finally:
        doc.close()
    print(f"[images] rendered {n} page(s) at 150 dpi -> {media_dir}")

    # 3) assemble: text, then every page render in an end gallery
    out = build_header(pdf, n, media_rel, md_ver, pymu_ver)
    out += [""] + text.splitlines()
    out += ["", "## Page images", ""]
    for p in range(1, n + 1):
        out += [f"**Page {p}**", "", f"![Page {p}]({media_rel}/p{p:02d}.png)", ""]
    print(f"[assemble] text + {n} page image(s) in end gallery")

    with open(out_md, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print(f"[done] {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
