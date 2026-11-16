from pypdf import PdfReader      
import os

def extract_text_from_pdf(pdf_path):

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text

def load_resumes( folder ="Resumes"):

    resumes = []

    for filename in os.listdir(folder):

        if filename.lower().endswith(".pdf"):

            path = os.path.join(folder, filename)

            text = extract_text_from_pdf(path)

            name = os.path.splitext(filename)[0]

            resumes.append({
                "name": name,
                "text": text,
                "file": filename
            })

    return resumes