import fitz  # PyMuPDF


class PDFParser:

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    # Read complete PDF as one text
    def extract_text(self):
        document = fitz.open(self.pdf_path)

        full_text = ""

        for page_number, page in enumerate(document, start=1):
            print(f"Reading Page {page_number}")

            text = page.get_text()
            full_text += text + "\n"

        document.close()

        return full_text

    # Read page by page
    def extract_pages(self):
        document = fitz.open(self.pdf_path)

        pages = []

        for page_number, page in enumerate(document, start=1):
            pages.append({
                "page": page_number,
                "text": page.get_text()
            })

        document.close()

        return pages

    # Extract possible headings
    def extract_headings(self):
        document = fitz.open(self.pdf_path)

        headings = []

        for page_number, page in enumerate(document, start=1):

            blocks = page.get_text("dict")["blocks"]

            for block in blocks:

                if "lines" not in block:
                    continue

                for line in block["lines"]:

                    text = ""

                    max_size = 0

                    for span in line["spans"]:
                        text += span["text"]

                        if span["size"] > max_size:
                            max_size = span["size"]

                    text = text.strip()

                    if text == "":
                        continue

                    # Treat larger font as heading
                    if max_size >= 14:
                        headings.append({
                            "page": page_number,
                            "heading": text,
                            "font_size": round(max_size, 2)
                        })

        document.close()

        return headings