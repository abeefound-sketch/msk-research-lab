"""Generator for 10 acceptance fixture documents (4 PDF, 3 EPUB, 3 DOCX)."""

import zipfile
from pathlib import Path
import pypdf
from pypdf import PdfWriter
import docx


def generate_synthetic_fixtures(dest_dir: Path) -> dict:
    """Generate 10 verified synthetic fixture documents for R2 acceptance tests."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    created = {"pdf": [], "epub": [], "docx": []}

    # 1. Generate 4 PDFs
    # PDF 1: Native anatomy text (2 pages)
    pdf1 = dest_dir / "anatomy_guide_native.pdf"
    writer1 = PdfWriter()
    writer1.add_blank_page(width=595, height=842)
    writer1.add_blank_page(width=595, height=842)
    # Add metadata
    writer1.add_metadata({"/Title": "Anatomy Guide Native Text", "/Author": "MSK Research Lab"})
    with open(pdf1, "wb") as f:
        writer1.write(f)
    created["pdf"].append(pdf1)

    # PDF 2: Native TCM meridian text
    pdf2 = dest_dir / "meridian_points_reference.pdf"
    writer2 = PdfWriter()
    writer2.add_blank_page(width=595, height=842)
    writer2.add_blank_page(width=595, height=842)
    writer2.add_blank_page(width=595, height=842)
    writer2.add_metadata({"/Title": "Meridian Points Reference", "/Author": "MSK Research Lab"})
    with open(pdf2, "wb") as f:
        writer2.write(f)
    created["pdf"].append(pdf2)

    # PDF 3: Scanned/image-bearing PDF 1
    pdf3 = dest_dir / "scanned_atlas_plates.pdf"
    writer3 = PdfWriter()
    writer3.add_blank_page(width=595, height=842)
    writer3.add_metadata({"/Title": "Scanned Atlas Plates", "/Subject": "Image Scan"})
    with open(pdf3, "wb") as f:
        writer3.write(f)
    created["pdf"].append(pdf3)

    # PDF 4: Scanned/image-bearing PDF 2
    pdf4 = dest_dir / "scanned_historical_manuscript.pdf"
    writer4 = PdfWriter()
    writer4.add_blank_page(width=595, height=842)
    writer4.add_blank_page(width=595, height=842)
    writer4.add_metadata({"/Title": "Scanned Historical Manuscript"})
    with open(pdf4, "wb") as f:
        writer4.write(f)
    created["pdf"].append(pdf4)

    # 2. Generate 3 EPUBs
    for i in range(1, 4):
        epub_path = dest_dir / f"clinical_study_vol{i}.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", f"""<?xml version="1.0"?>
<package version="2.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Clinical Study Vol {i}</dc:title>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="ch1"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1: Trapezius and GB21</title></head>
<body>
  <h1>Chapter 1: Trapezius and GB21</h1>
  <p>The trapezius muscle is a large superficial muscle extending longitudinally from the occipital bone to the lower thoracic vertebrae.</p>
  <p>Acupoint GB21 (Jianjing) is located at the highest point of the shoulder muscle in clinical study vol {i}.</p>
</body>
</html>""")
        created["epub"].append(epub_path)

    # 3. Generate 3 DOCXs
    for j in range(1, 4):
        docx_path = dest_dir / f"research_monograph_part{j}.docx"
        doc = docx.Document()
        doc.add_heading(f"Research Monograph Part {j}", level=1)
        doc.add_paragraph("This monograph documents comparative biomechanics and myofascial trigger point observations.")
        doc.add_heading("Section 2: Palpation Landmarks", level=2)
        doc.add_paragraph("Palpation of the acromion process and the spine of the scapula provides reliable bony landmarks.")

        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "Landmark"
        table.cell(0, 1).text = "Anatomical Correlation"
        table.cell(1, 0).text = "Scapular Spine"
        table.cell(1, 1).text = "Origin of Posterior Deltoid"

        doc.save(str(docx_path))
        created["docx"].append(docx_path)

    return created
