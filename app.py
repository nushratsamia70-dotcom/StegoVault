import inspect
import tempfile
from pathlib import Path
import streamlit as st
from crypto_module import embed_payload, extract_payload

BASE_DIR = Path(__file__).parent
LOGO_PATH = BASE_DIR / "StegoVault.jpeg"
ICON_PATH = BASE_DIR / "StegoVault.ico"

page_icon = (
    str(ICON_PATH)
    if ICON_PATH.exists()
    else (str(LOGO_PATH) if LOGO_PATH.exists() else "🔐")
)
st.set_page_config(page_title="StegoVault", page_icon=page_icon, layout="wide")

st.markdown(
    """
    <style>
        .stApp {
            background-color: #1E293B;
            color: #F8FAFC;
        }
        [data-testid="stSidebar"] {
            background-color: #0F172A;
            color: #F8FAFC;
        }
        [data-testid="stSidebar"] * {
            color: #F8FAFC;
        }
        h1, h2, h3, label, p, span, div {
            color: #F8FAFC;
        }
        .stButton > button {
            background-color: #38BDF8;
            color: #0F172A !important;
            font-weight: 600;
            border: none;
            border-radius: 6px;
        }
        .stButton > button * {
            color: #0F172A !important;
        }
        input, textarea {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }
        div[data-testid="stAlert"],
        div[data-testid="stAlert"] *,
        .stAlert,
        .stAlert * {
            color: #0F172A !important;
        }
        div[data-testid="stFileUploaderFile"],
        div[data-testid="stFileUploaderFile"] *,
        [data-testid="stFileUploaderFileName"],
        [data-testid="stFileUploaderFileSize"] {
            color: #0F172A !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def _call_embed(
    cover_path: Path,
    cover_filename: str,
    secret_data: bytes,
    is_file: bool,
    payload_name: str,
    passphrase: str,
    tmp_dir: Path,
):
    ext = cover_path.suffix if cover_path.suffix else ".png"
    output_path = tmp_dir / f"stego_output{ext}"
    secret_file_path = None
    if is_file:
        secret_file_path = tmp_dir / payload_name
        secret_file_path.write_bytes(secret_data)

    params = inspect.signature(embed_payload).parameters
    kwargs = {}

    for name in params:
        low = name.lower()
        if "cover" in low and ("path" in low or "file" in low or "input" in low or "image" in low):
            kwargs[name] = str(cover_path)
        elif "output" in low or "stego" in low or "out_path" in low or "save" in low:
            kwargs[name] = str(output_path)
        elif "pass" in low or "key" in low or "pwd" in low or "secret_key" in low:
            kwargs[name] = passphrase
        elif "message" in low or "text" in low:
            kwargs[name] = secret_data.decode("utf-8", errors="replace") if not is_file else str(secret_file_path)
        elif "secret" in low and ("path" in low or "file" in low):
            kwargs[name] = str(secret_file_path) if secret_file_path else ""
        elif "data" in low or "payload" in low:
            kwargs[name] = secret_data
        elif "is_file" in low:
            kwargs[name] = is_file
        elif "filename" in low or "name" in low:
            kwargs[name] = payload_name

    ret = embed_payload(**kwargs) if kwargs else embed_payload(
        str(cover_path),
        secret_data.decode("utf-8", errors="replace") if not is_file else str(secret_file_path),
        passphrase,
        str(output_path),
    )

    if isinstance(ret, tuple) and len(ret) >= 2:
        first, second = ret[0], ret[1]
        if isinstance(first, (bytes, bytearray)):
            return bytes(first), str(second)
        if isinstance(second, (bytes, bytearray)):
            return bytes(second), str(first)
        p = Path(str(first))
        if p.exists():
            return p.read_bytes(), str(second)

    if isinstance(ret, (bytes, bytearray)):
        return bytes(ret), f"stego_{cover_filename}"

    if isinstance(ret, (str, Path)) and Path(str(ret)).exists():
        p = Path(str(ret))
        return p.read_bytes(), p.name

    if output_path.exists():
        return output_path.read_bytes(), f"stego_{cover_filename}"

    raise RuntimeError("Stego output file was not generated.")


def _call_extract(stego_path: Path, stego_filename: str, passphrase: str, tmp_dir: Path):
    out_extract_path = tmp_dir / "extracted_output"
    params = inspect.signature(extract_payload).parameters
    kwargs = {}

    for name in params:
        low = name.lower()
        if ("stego" in low or "cover" in low or "input" in low or "file" in low or "image" in low) and (
            "path" in low or "file" in low or "stego" in low or "cover" in low or "input" in low or "image" in low
        ):
            if "out" not in low and "output" not in low and "save" not in low:
                kwargs[name] = str(stego_path)
        elif "pass" in low or "key" in low or "pwd" in low or "secret_key" in low:
            kwargs[name] = passphrase
        elif "output" in low or "out_path" in low or "save" in low or "dir" in low:
            kwargs[name] = str(out_extract_path)

    ret = extract_payload(**kwargs) if kwargs else extract_payload(str(stego_path), passphrase)

    if isinstance(ret, dict):
        return ret

    if isinstance(ret, tuple) and len(ret) >= 2:
        return {"is_file": bool(ret[1]), "data": ret[0] if isinstance(ret[0], bytes) else str(ret[0]).encode("utf-8")}

    if isinstance(ret, (bytes, bytearray)):
        return {"is_file": False, "data": bytes(ret)}

    return {"is_file": False, "data": str(ret).encode("utf-8")}


with st.sidebar:
    st.markdown("## Welcome to StegoVault")
    mode = st.radio(
        "Select Operation",
        ["Embed Payload", "Extract Payload"],
        label_visibility="collapsed",
    )

header_col1, header_col2 = st.columns([1, 10], vertical_alignment="center")
with header_col1:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=56)
with header_col2:
    st.markdown("# StegoVault")

st.markdown("---")

if mode == "Embed Payload":
    st.markdown("## 🔒 Hide Secret Data or File")
    payload_type = st.radio(
        "Select Payload Type:",
        ["Secret Text Message", "Secret File"],
    )
    cover_file = st.file_uploader(
        "1. Select Cover File (.png or .docx)",
        type=["png", "docx"],
    )

    if payload_type == "Secret Text Message":
        secret_text = st.text_area(
            "Secret Message:",
            placeholder="Type your secret message here...",
        )
        passphrase = st.text_input("Passphrase Key:", type="password")

        if st.button("🔒 Embed & Encrypt"):
            if not cover_file or not secret_text or not passphrase:
                st.warning("Please provide a cover file, secret message, and passphrase key.")
            else:
                try:
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        tmp_path = Path(tmp_dir)
                        cover_path = tmp_path / cover_file.name
                        cover_path.write_bytes(cover_file.getvalue())

                        output_bytes, output_name = _call_embed(
                            cover_path=cover_path,
                            cover_filename=cover_file.name,
                            secret_data=secret_text.encode("utf-8"),
                            is_file=False,
                            payload_name="message.txt",
                            passphrase=passphrase,
                            tmp_dir=tmp_path,
                        )
                    st.success("Secret text message embedded successfully!")
                    st.download_button(
                        label="Download Stego File",
                        data=output_bytes,
                        file_name=output_name,
                    )
                except Exception as exc:
                    st.error(f"Embedding failed: {exc}")
    else:
        secret_file = st.file_uploader("Select Secret File to Hide")
        passphrase = st.text_input("Passphrase Key:", type="password")

        if st.button("🔒 Embed & Encrypt"):
            if not cover_file or not secret_file or not passphrase:
                st.warning("Please provide a cover file, secret file, and passphrase key.")
            else:
                try:
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        tmp_path = Path(tmp_dir)
                        cover_path = tmp_path / cover_file.name
                        cover_path.write_bytes(cover_file.getvalue())

                        output_bytes, output_name = _call_embed(
                            cover_path=cover_path,
                            cover_filename=cover_file.name,
                            secret_data=secret_file.getvalue(),
                            is_file=True,
                            payload_name=secret_file.name,
                            passphrase=passphrase,
                            tmp_dir=tmp_path,
                        )
                    st.success("Secret file embedded successfully!")
                    st.download_button(
                        label="Download Stego File",
                        data=output_bytes,
                        file_name=output_name,
                    )
                except Exception as exc:
                    st.error(f"Embedding failed: {exc}")

else:
    st.markdown("## 🔓 Extract Secret Data or File")
    stego_file = st.file_uploader(
        "1. Select Stego File (.png or .docx)",
        type=["png", "docx"],
    )
    passphrase = st.text_input("Passphrase Key:", type="password")

    if st.button("🔓 Extract & Decrypt"):
        if not stego_file or not passphrase:
            st.warning("Please provide a stego file and passphrase key.")
        else:
            try:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp_path = Path(tmp_dir)
                    stego_path = tmp_path / stego_file.name
                    stego_path.write_bytes(stego_file.getvalue())

                    result = _call_extract(
                        stego_path=stego_path,
                        stego_filename=stego_file.name,
                        passphrase=passphrase,
                        tmp_dir=tmp_path,
                    )
                if result.get("is_file"):
                    raw_data = result.get("data", b"")
                    if isinstance(raw_data, str):
                        raw_data = raw_data.encode("utf-8")
                    st.success("Secret file extracted successfully!")
                    st.download_button(
                        label=f"Download {result.get('filename', 'extracted_file')}",
                        data=raw_data,
                        file_name=result.get("filename", "extracted_file"),
                    )
                else:
                    raw_data = result.get("data", b"")
                    text_val = (
                        raw_data.decode("utf-8", errors="replace")
                        if isinstance(raw_data, (bytes, bytearray))
                        else str(raw_data)
                    )
                    st.success("Secret text message extracted successfully!")
                    st.text_area(
                        "Extracted Message:",
                        value=text_val,
                        height=150,
                    )
            except Exception as exc:
                st.error(f"Extraction failed: {exc}")