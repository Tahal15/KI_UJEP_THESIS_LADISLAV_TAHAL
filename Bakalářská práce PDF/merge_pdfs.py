import fitz
import sys

# File paths
thesis_path = "ki-thesis.pdf"
zadani_path = "ZadaniBP_LadislavTAHAL.pdf"
prohlaseni_path = "Prohlaseni_LadislavTAHAL.pdf"
output_path = "ki-thesis-final.pdf"

try:
    doc_thesis = fitz.open(thesis_path)
    doc_zadani = fitz.open(zadani_path)
    doc_prohlaseni = fitz.open(prohlaseni_path)
    
    doc_final = fitz.open()
    
    # 1. Title and blank page (Pages 1-2 from Thesis)
    # Indices 0, 1
    doc_final.insert_pdf(doc_thesis, from_page=0, to_page=1)
    
    # 2. Assignment (Pages 3-4 from Zadani PDF)
    # Assuming Zadani is 2 pages. If it's more, we take all.
    doc_final.insert_pdf(doc_zadani)
    
    # 3. Declaration (Page 5 from Prohlaseni PDF)
    # Assuming Prohlaseni is 1 page.
    doc_final.insert_pdf(doc_prohlaseni)
    
    # 4. Rest of Thesis (Page 6 onwards)
    # In doc_thesis, we skipped 3 pages (indices 2, 3, 4).
    # So we resume from index 5.
    doc_final.insert_pdf(doc_thesis, from_page=5)
    
    doc_final.save(output_path)
    print(f"Successfully created {output_path}")
    
    doc_thesis.close()
    doc_zadani.close()
    doc_prohlaseni.close()
    doc_final.close()

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
