import fitz  # PyMuPDF
import sys

pdf_path = "ZadaniBP_LadislavTAHAL.pdf"
output_base = "ZadaniBP_page"

try:
    doc = fitz.open(pdf_path)
    for i in range(len(doc)):
        page = doc.load_page(i)
        # Use high zoom for better quality (e.g., 2.0 = 200% DPI, usually 72->144, maybe go higher)
        mat = fitz.Matrix(3.0, 3.0) 
        pix = page.get_pixmap(matrix=mat)
        output_filename = f"{output_base}_{i+1}.png"
        pix.save(output_filename)
        print(f"Saved {output_filename}")
    doc.close()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
