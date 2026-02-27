import fitz
import os
import sys

def test_pdf_conversion(pdf_path):
    try:
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            return
        
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=150)
        out_path = pdf_path + ".test.png"
        pix.save(out_path)
        print(f"Success! Saved to {out_path}")
        doc.close()
        if os.path.exists(out_path):
            os.remove(out_path)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # If no pdf provided, just check imports
    print("fitz imported successfully")
