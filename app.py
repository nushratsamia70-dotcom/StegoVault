import os
import streamlit as st
from crypto_module import embed_payload, extract_payload

# Page Configuration with Sidebar Expanded by Default & Custom Icon
st.set_page_config(
    page_title="StegoVault",
    page_icon="StegoVault.ico"
    if os.path.exists("StegoVault.ico")
    else "🔒",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom CSS for Perfect Contrast & Visibility
st.markdown(
    """
    <style>
    .stApp {
        background-color: #1E293B;
        color: #F8FAFC !important;
    }
    
    /* Force all text and labels to be bright white */
    p, label, .stRadio label, .stCheckbox label, span, div, small {
        color: #F8FAFC !important;
    }

    /* Fix Sidebar Background and Text Color */
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
    }
    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }

    .main-header {
        background-color: #0F172A;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 5px solid #38BDF8;
    }
    .main-header h1 {
        color: #38BDF8 !important;
        font-size: 24px;
        margin: 0;
    }
    
    .stButton>button {
        background-color: #2563EB;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        border: none;
        padding: 8px 16px;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
    }
    
    /* Input field and uploader text visibility fixes */
    .stTextInput input, .stTextArea textarea {
        color: #0F172A !important;
        background-color: #F8FAFC !important;
    }
    
    [data-testid="stFileUploader"] section {
        background-color: #0F172A !important;
        border: 1px dashed #38BDF8 !important;
    }
    [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] span {
        color: #94A3B8 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Clean & Professional Header using Columns for Logo/Icon and Title
col_icon, col_title = st.columns([0.1, 0.9])
with col_icon:
  if os.path.exists("StegoVault.jpeg"):
    st.image("StegoVault.jpeg", width=36)
  elif os.path.exists("StegoVault.png"):
    st.image("StegoVault.png", width=36)
  else:
    st.markdown(
        "<h2 style='margin:0; padding-top:5px;'>🛡️</h2>", unsafe_allow_html=True
    )

with col_title:
  st.markdown(
      "<h1"
      " style='color: #38BDF8; font-size: 26px; margin: 0; padding-top: 4px;'>"
      "StegoVault</h1>",
      unsafe_allow_html=True,
  )

st.markdown("<hr style='border: 0.5px solid #334155;'>", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.markdown(
    "<h2 style='color: #38BDF8; font-size: 18px;'>Welcome to StegoVault</h2>",
    unsafe_allow_html=True,
)
menu = st.sidebar.radio("", ["Embed Payload", "Extract Payload"])

if menu == "Embed Payload":
  st.subheader("🔒 Hide Secret Data or File")

  embed_type = st.radio(
      "Select Payload Type:", ["Secret Text Message", "Secret File"]
  )

  cover_file = st.file_uploader(
      "1. Select Cover File (.png or .docx)",
      type=["png", "docx"],
      help="Upload a cover PNG image or DOCX document",
  )

  secret_data = None
  filename = ""

  if embed_type == "Secret Text Message":
    secret_text = st.text_area(
        "Secret Message:", placeholder="Type your secret message here..."
    )
    if secret_text:
      secret_data = secret_text.encode("utf-8")
  else:
    secret_file = st.file_uploader(
        "Select Secret File to Hide:",
        type=["pdf", "png", "docx", "txt"],
        help="Upload the file you want to hide",
    )
    if secret_file:
      secret_data = secret_file.read()
      filename = secret_file.name

  password = st.text_input(
      "Passphrase Encryption Key:",
      type="password",
      placeholder="Enter secure password...",
  )

  if st.button("🔒 Encrypt & Embed"):
    if not cover_file or not secret_data or not password:
      st.warning(
          "Please select a cover file, provide the secret payload, and enter a"
          " password."
      )
    else:
      cover_path = f"temp_{cover_file.name}"
      with open(cover_path, "wb") as f:
        f.write(cover_file.getbuffer())

      ext = os.path.splitext(cover_file.name)[1].lower()
      output_path = f"stego_output{ext}"

      try:
        is_file = True if embed_type == "Secret File" else False
        embed_payload(
            cover_path, output_path, secret_data, password, is_file, filename
        )
        st.success("Successfully embedded payload!")

        with open(output_path, "rb") as f:
          st.download_button(
              label="📥 Download Stego File",
              data=f,
              file_name=output_path,
              mime="application/octet-stream",
          )
      except Exception as e:
        st.error(f"Error: {str(e)}")

elif menu == "Extract Payload":
  st.subheader("🔓 Extract Hidden Payload")

  stego_file = st.file_uploader(
      "1. Select Stego File (.png or .docx)",
      type=["png", "docx"],
      help="Upload the stego file containing hidden data",
  )
  password = st.text_input(
      "Passphrase Key:",
      type="password",
      placeholder="Enter decryption password...",
  )

  if st.button("🔓 Extract & Decrypt"):
    if not stego_file or not password:
      st.warning("Please select a stego file and enter the password.")
    else:
      stego_path = f"temp_{stego_file.name}"
      with open(stego_path, "wb") as f:
        f.write(stego_file.getbuffer())

      try:
        dtype, data, filename = extract_payload(stego_path, password)

        if dtype == "text":
          st.success("Secret text message extracted successfully!")
          st.text_area("Extracted Message:", value=data, height=150)
        elif dtype == "file":
          st.success(f"Secret file '{filename}' extracted successfully!")
          st.download_button(
              label=f"📥 Download Extracted File ({filename})",
              data=data,
              file_name=filename,
              mime="application/octet-stream",
          )
        else:
          st.error(
              "Failed! Incorrect password or no hidden data found in this file."
          )
      except Exception as e:
        st.error(f"Error: {str(e)}")