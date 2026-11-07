"""Convert a training-material PPTX (or legacy PPT) to Markdown with a slide-image
gallery in one step.

Usage:
    python tools/pptx_to_md.py <input.pptx|input.ppt> [output.md]

Pipeline (one step; mirrors pdf_to_md.py):
  1. Text: markitdown (Python API) converts the deck to Markdown text — slide
     anchors "<!-- Slide number: N -->", titles, tables, chart data, speaker
     notes ("### Notes:") when present. Legacy .ppt is a binary OLE format that
     markitdown/python-pptx cannot read at all (a different workflow from the
     Open-XML .pptx); it is supported by first saving a temporary .pptx copy
     via PowerPoint — which is therefore mandatory for .ppt inputs.
  2. Figures: PowerPoint (COM via comtypes — pure-Python COM client in the
     workspace venv) exports the deck to a temporary PDF, and PyMuPDF renders
     every page to <out_stem>_media/pNN.png at 150 dpi. The export explicitly
     requests all slides, including hidden slides. When the PDF page count
     matches the slide count, gallery "Page N" means slide N. Otherwise the
     gallery is labeled by PDF page and the slide mapping is reported as
     unknown. Rendering captures vector art and shape groups; embedded pictures
     are only probed for stats. PowerPoint is required.
  3. Assembly: slide renders are collected in an end gallery under
     "## Page images", structurally identical to the PDF flow so the
     downstream image-analysis tooling works unchanged.
  4. A provenance header (source, date, tool versions, caveats) is prepended.

The original presentation is never modified; all intermediates live in a
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


def com_export(src: str, pdf_dst: str, pptx_dst: str):
    """Drive PowerPoint via COM (comtypes, pure-Python) to export src to PDF
    and, when pptx_dst is non-empty, also save an Open-XML .pptx copy.

    Returns (powerpoint_version, None) on success or (None, reason) on failure.
    """
    try:
        import comtypes.client
    except ImportError as e:
        return None, f"comtypes not available ({e})"
    pres = app = None
    try:
        app = comtypes.client.CreateObject("PowerPoint.Application", dynamic=True)
        ver = str(app.Version)
        # Open(FileName, ReadOnly=msoTrue, Untitled=msoFalse, WithWindow=msoFalse);
        # retry with a visible window for builds that refuse windowless opens.
        try:
            pres = app.Presentations.Open(src, True, False, False)
        except Exception as e_first:
            try:
                pres = app.Presentations.Open(src, True, False, True)
            except Exception as e_retry:
                return None, (
                    f"Presentations.Open failed — windowless: {type(e_first).__name__}: {e_first}; "
                    f"with-window retry: {type(e_retry).__name__}: {e_retry}"
                )
        if pptx_dst:
            pres.SaveAs(pptx_dst, 24)  # 24 = ppSaveAsOpenXMLPresentation
        from ctypes import POINTER
        from comtypes.automation import IDispatch

        # Explicitly export all slides, including hidden slides, one per page.
        pres.ExportAsFixedFormat(
            pdf_dst, 2, 1, 0, 1, 1, -1, POINTER(IDispatch)(), 1
        )
        pres.Close()
        pres = None
        return ver, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    finally:
        if pres is not None:
            try:
                pres.Close()
            except Exception:
                pass
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass


def walk_pictures(shapes):
    """All picture shapes on a slide, recursing into groups (best effort)."""
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    pics = []
    for sh in shapes:
        try:
            st = sh.shape_type
        except Exception:
            continue
        if st == MSO_SHAPE_TYPE.PICTURE:
            pics.append(sh)
        elif st == MSO_SHAPE_TYPE.GROUP:
            pics.extend(walk_pictures(sh.shapes))
        elif st == MSO_SHAPE_TYPE.PLACEHOLDER:
            try:
                if sh.image is not None:
                    pics.append(sh)
            except Exception:
                pass
    return pics


def probe_pictures(prs):
    """Probe embedded pictures per slide (informational, like the PDF probe)."""
    total = 0
    for idx, slide in enumerate(prs.slides, 1):
        pics = walk_pictures(slide.shapes)
        total += len(pics)
        if pics:
            sizes = set()
            for pic in pics:
                try:
                    img = pic.image
                    sizes.add("x".join(map(str, img.size)))
                except Exception:  # e.g. SVG picture without a raster fallback
                    sizes.add("?")
            print(f"[probe] slide {idx}: {len(pics)} embedded picture(s), px {sorted(sizes, reverse=True)[:4]}")
    print(f"[probe] total embedded pictures: {total}")
    return total


def build_header(src, n_slides, media_rel, md_ver, pp_ver, pymu_ver, n_rendered,
                 legacy, slide_mapping_known):
    slides_txt = f"{n_slides} slide" + ("s" if n_slides != 1 else "")
    if legacy:
        slides_txt += " — legacy .ppt; text read from a temporary .pptx copy (original untouched)"
    if slide_mapping_known:
        coverage = "pNN = slide N; all slides, including hidden slides, were exported"
    else:
        coverage = (
            f"pNN = PDF page N; slide mapping is unknown because the PDF has "
            f"{n_rendered} page(s) for {n_slides} slide(s). Which slides were "
            "omitted, including hidden slides, cannot be determined"
        )
    return [
        "> **Provenance**",
        f"> - Source: `{src}` ({slides_txt})",
        f"> - Converted: {date.today().isoformat()} — markitdown {md_ver} (text) "
        f"+ PowerPoint {pp_ver} (slide→PDF export) + PyMuPDF {pymu_ver} "
        f"(page images at {DPI} dpi), one step via `pptx_to_md.py`",
        f"> - Figures: {n_rendered} PDF page(s) rendered to `{media_rel}/pNN.png` at "
        f"{DPI} dpi ({coverage}), "
        "listed in the '## Page images' gallery at the end of this file.",
        "> - Caveats: markitdown's inline `![Picture N](...)` image references are "
        "placeholders that resolve to no file; figure-internal labels and tables can be "
        "mangled in the text layer; the slide PNGs are authoritative for figures. "
        "Speaker notes appear as `### Notes:` when present.",
        "> - Originals under `materials/` are never modified.",
    ]


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    src = os.path.abspath(sys.argv[1])
    ext = os.path.splitext(src)[1].lower()
    if ext not in (".pptx", ".ppt"):
        print(f"[error] unsupported input '{ext}' (expected .pptx or .ppt)")
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

    tmpdir = tempfile.mkdtemp(prefix="pptx2md_")
    try:
        pdf_path = os.path.join(tmpdir, "deck.pdf")
        pptx_tmp = os.path.join(tmpdir, "converted.pptx") if ext == ".ppt" else ""

        # 1) slide images (and, for legacy .ppt, the .pptx text source) via PowerPoint
        pp_ver, com_reason = com_export(src, pdf_path, pptx_tmp)
        if not pp_ver:
            need = "slide renders" if ext == ".pptx" else "slide renders and the temporary .pptx text copy"
            print(f"[error] PowerPoint unavailable: {com_reason} — required for {need}")
            return 1
        what = "slide→PDF export" if ext == ".pptx" else "slide→PDF export + temp .pptx"
        print(f"[com] PowerPoint {pp_ver}: {what}")
        text_src = pptx_tmp if ext == ".ppt" else src

        # 2) text via markitdown
        from markitdown import MarkItDown

        text = MarkItDown().convert(text_src).text_content
        md_ver = im.version("markitdown")
        print(f"[text] markitdown {md_ver}: {len(text)} chars")

        # 3) slide renders via PyMuPDF (+ embedded-picture probe)
        from pptx import Presentation

        prs = Presentation(text_src)
        n_slides = len(prs.slides)
        if n_slides == 0:
            print("[error] presentation has no slides")
            return 1
        print(f"[slides] {n_slides} slide(s), including hidden slides")
        probe_pictures(prs)

        import pymupdf

        doc = pymupdf.open(pdf_path)
        try:
            n_pdf = len(doc)
            if n_pdf == 0:
                print("[error] exported PDF has no pages")
                return 1
            pymu_ver = getattr(pymupdf, "VersionBind", None) or getattr(pymupdf, "__version__", "?")
            slide_mapping_known = n_pdf == n_slides
            if not slide_mapping_known:
                print(
                    f"[warn] PDF pages ({n_pdf}) != slides ({n_slides}); "
                    "gallery labeled by PDF page. Slide mapping and omitted slides are unknown."
                )
            gallery = []  # (page number, png filename)
            for page_no, page in enumerate(doc, 1):
                fn = f"p{page_no:02d}.png"
                page.get_pixmap(dpi=DPI).save(os.path.join(media_dir, fn))
                gallery.append((page_no, fn))
        finally:
            doc.close()
        print(f"[images] rendered {n_pdf} PDF page(s) at {DPI} dpi -> {media_dir}")

        # 4) assemble: header + text + end gallery
        out = build_header(src, n_slides, media_rel, md_ver, pp_ver, pymu_ver,
                           len(gallery), legacy=(ext == ".ppt"),
                           slide_mapping_known=slide_mapping_known)
        out += [""] + text.splitlines()
        out += ["", "## Page images", ""]
        for page_no, fn in gallery:
            label = f"Page {page_no}" if slide_mapping_known else f"PDF page {page_no}"
            out += [f"**{label}**", "", f"![{label}]({media_rel}/{fn})", ""]
        print(f"[assemble] text + {len(gallery)} page image(s) in end gallery")

        with open(out_md, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out) + "\n")
        print(f"[done] {out_md}")
        return 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
