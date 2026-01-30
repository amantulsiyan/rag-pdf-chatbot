import fitz

def load_pdf(pdf_path:str)->str:
    doc=fitz.open(pdf_path)
    all_text=[]
    for page_num in range(len(doc)):
        page=doc[page_num]
        text=page.get_text()

        if text:
            cleaned=text.strip()
            if cleaned:
                all_text.append(cleaned)
    doc.close()
    return "\n\n".join(all_text)
