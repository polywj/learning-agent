"""Convert a training-material DOCX (or legacy DOC) to Markdown with a page-image
gallery in one step.

Usage:
    python tools/docx_to_md.py <input.docx|input.doc> [output.md]

Pipeline (one step; mirrors pptx_to_md.py):
  1. Text: markitdown (Python API, via mammoth) converts the document to
     Markdown text — headings, styled runs, tables. Legacy .doc is a binary
     OLE format that markitdown/mammoth cannot read at all (a different
     workflow from the Open-XML .docx); it is supported by first saving a
     temporary .docx copy via Word — which is therefore mandatory for .doc
     inputs. Embedded images are replaced during conversion with non-resolving
     "![Picture N]" placeholders (same convention as the PPTX flow).
  2. Figures: Word (COM via comtypes — pure-Python COM client in the
     workspace venv) exports the document to a temporary PDF, and PyMuPDF
     renders every page to <out_stem>_media/pNN.png at 150 dpi. pNN is page N
     as paginated by Word's PDF export; pagination follows Word's rendering
     and may differ from other viewers. Word is required.
  3. Assembly: page renders are collected in an end gallery under
     "## Page images", structurally identical to the PDF/PPTX flows so the
     downstream image-analysis tooling works unchanged.
  4. A provenance header (source, date, tool versions, caveats) is prepended.

The original document is never modified; all intermediates live in a
temporary directory that is removed afterwards.
"""

import importlib.metadata as im
import os
import shutil
import sys
import tempfile
from datetime import date

DPI = 150


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


def com_export(src: str, pdf_dst: str, docx_dst: str):
    """Drive Word via COM (comtypes, pure-Python) to export src to PDF and,
    when docx_dst is non-empty, also save an Open-XML .docx copy.

    Returns (word_version, None) on success or (None, reason) on failure.
    """
    try:
        import comtypes.client
    except ImportError as e:
        return None, f"comtypes not available ({e})"
    doc = app = None
    try:
        app = comtypes.client.CreateObject("Word.Application", dynamic=True)
        ver = str(app.Version)
        app.Visible = False
        app.DisplayAlerts = 0  # wdAlertsNone
        options = app.Options
        update_links_at_open = options.UpdateLinksAtOpen
        try:
            options.UpdateLinksAtOpen = False
            # Documents.Open(FileName, ConfirmConversions, ReadOnly, AddToRecentFiles)
            automation_security = app.AutomationSecurity
            try:
                app.AutomationSecurity = 3  # msoAutomationSecurityForceDisable
                try:
                    doc = app.Documents.Open(src, False, True, False)
                except Exception as e_first:
                    return None, f"Documents.Open failed — {type(e_first).__name__}: {e_first}"
            finally:
                app.AutomationSecurity = automation_security
        finally:
            options.UpdateLinksAtOpen = update_links_at_open
        if docx_dst:
            doc.SaveAs2(docx_dst, 16)  # 16 = wdFormatDocumentDefault (.docx)
        doc.ExportAsFixedFormat(pdf_dst, 17)  # 17 = wdExportFormatPDF (all pages)
        doc.Close(False)  # SaveChanges = False; the original is never modified
        doc = None
        return ver, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    finally:
        if doc is not None:
            try:
                doc.Close(False)
            except Exception:
                pass
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass


def probe_media(docx_path: str) -> int:
    """Count embedded media files inside the .docx package (informational)."""
    import zipfile

    try:
        with zipfile.ZipFile(docx_path) as z:
            names = [
                n for n in z.namelist()
                if n.startswith("word/media/") and not n.endswith("/")
            ]
    except Exception as e:
        print(f"[probe] could not inspect embedded media: {e}")
        return 0
    for n in names[:8]:
        print(f"[probe] embedded media: {n}")
    if len(names) > 8:
        print(f"[probe] ... and {len(names) - 8} more")
    print(f"[probe] total embedded media files: {len(names)}")
    return len(names)


def convert_text(src: str) -> tuple[str, int]:
    from markitdown import MarkItDown
    from markitdown.converters import DocxConverter

    if not hasattr(DocxConverter, "_image_to_html"):
        raise RuntimeError("The installed MarkItDown DOCX converter lacks the image hook")

    class PlaceholderDocxConverter(DocxConverter):
        def __init__(self):
            super().__init__()
            self.image_count = 0

        def _image_to_html(self, image_stream, stream_info, **kwargs):
            self.image_count += 1
            return f"<span>![Picture {self.image_count}]</span>"

    converter = PlaceholderDocxConverter()
    md = MarkItDown(enable_builtins=False)
    md.register_converter(converter)
    return md.convert(src).text_content, converter.image_count


def build_header(src, media_rel, md_ver, word_ver, pymu_ver, n_rendered,
                 n_images, legacy):
    src_txt = f"`{src}` (Word document"
    if legacy:
        src_txt += " — legacy .doc; text read from a temporary .docx copy (original untouched)"
    src_txt += ")"
    return [
        "> **Provenance**",
        f"> - Source: {src_txt}",
        f"> - Converted: {date.today().isoformat()} — markitdown {md_ver} (text) "
        f"+ Word {word_ver} (PDF export) + PyMuPDF {pymu_ver} "
        f"(page images at {DPI} dpi), one step via `docx_to_md.py`",
        f"> - Figures: {n_rendered} page(s) rendered to `{media_rel}/pNN.png` at "
        f"{DPI} dpi (pNN = page N as paginated by Word's PDF export; pagination "
        "follows Word's rendering and may differ from other viewers), "
        "listed in the '## Page images' gallery at the end of this file.",
        f"> - Caveats: {n_images} inline image(s) appear as `![Picture N]` "
        "placeholders that resolve to no file (the page PNGs are authoritative "
        "for figures); tables "
        "and complex layout can be mangled in the text layer; headers, footers, "
        "and footnotes may be dropped or reordered.",
        "> - Originals under `materials/` are never modified.",
    ]


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    src = os.path.abspath(sys.argv[1])
    ext = os.path.splitext(src)[1].lower()
    if ext not in (".docx", ".doc"):
        print(f"[error] unsupported input '{ext}' (expected .docx or .doc)")
        return 2
    if not os.path.isfile(src):
        print(f"[error] not found: {src}")
        return 2

    stem = os.path.splitext(os.path.basename(src))[0]
    out_md = (
        os.path.abspath(sys.argv[2])
        if len(sys.argv) > 2
        else os.path.abspath(os.path.join("materials", "md", stem + ".md"))
    )
    if same_file(src, out_md):
        print(f"[error] input and output refer to the same file: {out_md}")
        return 2

    media_dir = os.path.splitext(out_md)[0] + "_media"
    media_rel = os.path.basename(media_dir)
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    os.makedirs(media_dir, exist_ok=True)
    clear_page_pngs(media_dir)

    tmpdir = tempfile.mkdtemp(prefix="docx2md_")
    try:
        pdf_path = os.path.join(tmpdir, "document.pdf")
        docx_tmp = os.path.join(tmpdir, "converted.docx") if ext == ".doc" else ""

        # 1) page renders (and, for legacy .doc, the .docx text source) via Word
        word_ver, com_reason = com_export(src, pdf_path, docx_tmp)
        if not word_ver:
            need = "page renders" if ext == ".docx" else "page renders and the temporary .docx text copy"
            print(f"[error] Word unavailable: {com_reason} — required for {need}")
            return 1
        what = "PDF export" if ext == ".docx" else "PDF export + temp .docx"
        print(f"[com] Word {word_ver}: {what}")
        text_src = docx_tmp if ext == ".doc" else src

        # 2) text via markitdown, with inline image placeholders
        text, n_images = convert_text(text_src)
        md_ver = im.version("markitdown")
        print(f"[text] markitdown {md_ver}: {len(text)} chars, {n_images} inline image(s) -> placeholders")

        # 3) page renders via PyMuPDF (+ embedded-media probe)
        probe_media(text_src)

        import pymupdf

        doc = pymupdf.open(pdf_path)
        try:
            n_pdf = len(doc)
            if n_pdf == 0:
                print("[error] exported PDF has no pages")
                return 1
            pymu_ver = getattr(pymupdf, "VersionBind", None) or getattr(pymupdf, "__version__", "?")
            gallery = []  # (page number, png filename)
            for page_no, page in enumerate(doc, 1):
                fn = f"p{page_no:02d}.png"
                page.get_pixmap(dpi=DPI).save(os.path.join(media_dir, fn))
                gallery.append((page_no, fn))
        finally:
            doc.close()
        print(f"[images] rendered {n_pdf} PDF page(s) at {DPI} dpi -> {media_dir}")

        # 4) assemble: header + text + end gallery
        out = build_header(src, media_rel, md_ver, word_ver, pymu_ver,
                           len(gallery), n_images, legacy=(ext == ".doc"))
        out += [""] + text.splitlines()
        out += ["", "## Page images", ""]
        for page_no, fn in gallery:
            out += [f"**Page {page_no}**", "", f"![Page {page_no}]({media_rel}/{fn})", ""]
        print(f"[assemble] text + {len(gallery)} page image(s) in end gallery")

        with open(out_md, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out) + "\n")
        print(f"[done] {out_md}")
        return 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
