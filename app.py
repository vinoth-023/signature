import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import base64
from fpdf import FPDF
import tempfile
import os
import json
from firebase_admin import credentials
# -------------------- Firebase Setup --------------------
if not firebase_admin._apps:
    cred_dict = st.secrets["FIREBASE"]
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -------------------- Admin UI --------------------
st.title("📋 Admin Dashboard")
st.write("Monitor all submitted signatures:")

# Fetch Firestore data
docs = db.collection("signatures").stream()

data = []
for doc in docs:
    d = doc.to_dict()
    # Decode base64 to display image
    signature_bytes = base64.b64decode(d['signature_base64'])
    d['signature_bytes'] = signature_bytes
    data.append(d)

if data:
    df = pd.DataFrame(data)
    st.dataframe(df[['name', 'phone']])

    st.write("### Uploaded Signatures")
    for idx, row in df.iterrows():
        st.write(f"**{row['name']} ({row['phone']})**")
        st.image(row['signature_bytes'], width=150)

        # -------------------- Individual PDF --------------------
        def generate_individual_pdf(entry):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "User Signature Data", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, f"Name: {entry['name']}", ln=True)
            pdf.cell(0, 8, f"Phone: {entry['phone']}", ln=True)
            pdf.ln(5)

            # Detect image type
            sig_bytes = base64.b64decode(entry['signature_base64'])
            ext = ".png" if sig_bytes[:8].startswith(b'\x89PNG') else ".jpg"

            # Save temp image
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_img:
                tmp_img.write(sig_bytes)
                tmp_img_path = tmp_img.name

            pdf.image(tmp_img_path, w=50)
            os.remove(tmp_img_path)

            # Save temp PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                pdf.output(tmp_pdf.name)
                return tmp_pdf.name

        pdf_file = generate_individual_pdf(row)
        with open(pdf_file, "rb") as f:
            st.download_button(
                label=f"📥 Download {row['name']}'s PDF",
                data=f,
                file_name=f"{row['name']}_signature.pdf",
                mime="application/pdf"
            )
        os.remove(pdf_file)

    st.write("---")
    st.write("### Download All Users Data")

    # -------------------- All Users PDF --------------------
    def generate_all_pdf(data):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "All Signature Entries", ln=True, align='C')
        pdf.ln(10)

        for entry in data:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, f"Name: {entry['name']}, Phone: {entry['phone']}", ln=True)
            pdf.ln(2)

            sig_bytes = base64.b64decode(entry['signature_base64'])
            ext = ".png" if sig_bytes[:8].startswith(b'\x89PNG') else ".jpg"

            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_img:
                tmp_img.write(sig_bytes)
                tmp_img_path = tmp_img.name

            pdf.image(tmp_img_path, w=50)
            pdf.ln(10)
            os.remove(tmp_img_path)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)
            return tmp_pdf.name

    all_pdf_file = generate_all_pdf(data)
    with open(all_pdf_file, "rb") as f:
        st.download_button(
            label="📥 Download All Users PDF",
            data=f,
            file_name="all_users_signatures.pdf",
            mime="application/pdf"
        )
    os.remove(all_pdf_file)

else:
    st.info("No data found in Firestore.")
