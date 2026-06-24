import fitz
import re

def clean_text(text: str) -> str:

    # Fix hyphenated line breaks
    text = re.sub(r'-\s*\n\s*', '-', text)

    # Replace remaining newlines with spaces
    text = re.sub(r'\n+', ' ', text)

    # Remove extra spaces/tabs
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def load_pdf(pdf_path: str) -> str:

    doc = fitz.open(pdf_path)

    all_text = []
    page_metadata = []

    for page_num in range(len(doc)):

        page = doc[page_num]

        text = page.get_text()

        if text:

            cleaned = clean_text(text)

            if cleaned:

                all_text.append(cleaned)

                page_metadata.append({
                    "page_number": page_num + 1,
                    "char_start": len(" ".join(all_text[:-1])) if all_text[:-1] else 0,
                    "char_end": len(" ".join(all_text))
                })

    doc.close()

    full_text = " ".join(all_text)

    return full_text, page_metadata