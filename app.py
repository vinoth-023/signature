import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64

# -------------------- Firebase Setup --------------------
if not firebase_admin._apps:
    # Make a copy of the secrets dict
    cred_dict = dict(st.secrets["FIREBASE"])

    # Fix the private key newlines
    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

    # Initialize Firebase
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -------------------- Streamlit UI --------------------
st.title("🖋️ Digital Signature Form")
st.write("Enter your details and upload your digital signature below:")

name = st.text_input("Full Name")
phone = st.text_input("Phone Number")
signature = st.file_uploader("Upload Digital Signature (PNG/JPG)", type=["png", "jpg", "jpeg"])

if st.button("Submit"):
    if not name or not phone or not signature:
        st.warning("⚠️ Please fill all fields and upload your signature.")
    else:
        # Convert uploaded image to base64 string
        signature_bytes = signature.read()
        signature_b64 = base64.b64encode(signature_bytes).decode("utf-8")

        # Save to Firestore
        db.collection("signatures").add({
            "name": name,
            "phone": phone,
            "signature_base64": signature_b64
        })

        st.success("✅ Data stored successfully in Firestore!")
        st.image(signature_bytes, caption="Uploaded Signature", width=200)
