import base64
import hashlib
import os
from cryptography.fernet import Fernet


def generate_key_from_password(password: str) -> bytes:
  digest = hashlib.sha256(password.encode()).digest()
  return base64.urlsafe_b64encode(digest)


# --- Text & File Embedding Logic with Filename Preservation ---
def embed_payload(
    cover_path: str,
    output_path: str,
    secret_data: bytes,
    password: str,
    is_file: bool,
    filename: str = "",
):
  with open(cover_path, "rb") as f:
    cover_bytes = f.read()

  key = generate_key_from_password(password)
  cipher = Fernet(key)
  encrypted_data = cipher.encrypt(secret_data)

  delimiter = b"###STEGO_BOUNDARY###"

  if is_file:
    # Format: b"FLE" + filename_length (2 bytes) + filename_bytes + encrypted_data
    fn_bytes = filename.encode("utf-8")
    fn_len = len(fn_bytes).to_bytes(2, "big")
    payload = b"FLE" + fn_len + fn_bytes + encrypted_data
  else:
    payload = b"TXT" + encrypted_data

  final_bytes = cover_bytes + delimiter + payload

  with open(output_path, "wb") as f:
    f.write(final_bytes)


# --- Extraction Wrapper ---
def extract_payload(stego_path: str, password: str):
  with open(stego_path, "rb") as f:
    content = f.read()

  delimiter = b"###STEGO_BOUNDARY###"
  parts = content.split(delimiter)

  if len(parts) < 2:
    return None, None, None

  payload_section = parts[1]
  data_type_flag = payload_section[:3]

  try:
    key = generate_key_from_password(password)
    cipher = Fernet(key)

    if data_type_flag == b"FLE":
      fn_len = int.from_bytes(payload_section[3:5], "big")
      filename = payload_section[5 : 5 + fn_len].decode("utf-8")
      encrypted_data = payload_section[5 + fn_len :]
      decrypted_data = cipher.decrypt(encrypted_data)
      return "file", decrypted_data, filename
    else:
      encrypted_data = payload_section[3:]
      decrypted_data = cipher.decrypt(encrypted_data)
      return "text", decrypted_data.decode("utf-8"), None
  except Exception:
    return None, None, None