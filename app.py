import re
import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_bytes
import pytesseract
from io import BytesIO
from datetime import datetime
import zipfile

# বাংলা → ইংরেজি সংখ্যা ম্যাপ
bangla_to_english_map = {
    "০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4",
    "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9"
}

def convert_bangla_to_english(num_str):
    return "".join(bangla_to_english_map.get(ch, ch) for ch in num_str)

def extract_bangla_numbers(text):
    return re.findall(r'[০-৯]+', text)

# --- Streamlit UI ---
st.title("🖼️ OCR PDF Bulk Rename")

uploaded_files = st.file_uploader("একাধিক PDF আপলোড করুন", type="pdf", accept_multiple_files=True)

if uploaded_files:
    total_files = len(uploaded_files)
    st.info(f"📖 মোট {total_files} ফাইল প্রক্রিয়া করা হবে... অনুগ্রহ করে অপেক্ষা করুন।")

    # Progress bar + status
    progress = st.progress(0)
    status_text = st.empty()

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for i, uploaded_file in enumerate(uploaded_files, start=1):
            pdf_bytes = uploaded_file.read()

            # OCR extract text
            images = convert_from_bytes(pdf_bytes)
            full_text = ""
            for img in images:
                text = pytesseract.image_to_string(img, lang="ben+eng")
                full_text += text + "\n"

            bangla_numbers = extract_bangla_numbers(full_text)

            # 🔍 Filter only 7-digit Bangla numbers
            valid_numbers = [num for num in bangla_numbers if len(num) == 7]

            # Show debug info
            # st.write(f"📄 {uploaded_file.name} → সব সংখ্যা: {bangla_numbers}, বৈধ ৭-সংখ্যা: {valid_numbers}")

            if valid_numbers:
                english_number = convert_bangla_to_english(valid_numbers[0])  # প্রথম বৈধ নম্বর
                new_name = f"{english_number}.pdf"
            else:
                new_name = f"{uploaded_file.name.replace('.pdf','')}.pdf"


            # Copy PDF pages
            reader = PdfReader(BytesIO(pdf_bytes))
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)

            pdf_buffer = BytesIO()
            writer.write(pdf_buffer)
            pdf_buffer.seek(0)

            # Add to ZIP
            zipf.writestr(new_name, pdf_buffer.read())

            # Update progress bar
            progress.progress(i / total_files)
            status_text.text(f"🔄 Processing {i}/{total_files}: {uploaded_file.name} → {new_name}")

    zip_buffer.seek(0)

    st.success("✅ সব ফাইল সফলভাবে প্রসেস হয়েছে!")

    # Download ZIP button
    st.download_button(
        "📦 Download All PDFs (ZIP)",
        zip_buffer,
        file_name=f"renamed_pdfs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        mime="application/zip"
    )

# UI-only footer
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:gray;'>Made with Love: "
    "<a href='https://profiles.wordpress.org/monzuralam'>Monzur Alam</a></p>",
    unsafe_allow_html=True
)
