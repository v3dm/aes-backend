from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import base64
import os
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional


# ---  params ---
PBKDF2_ITER = 100_000
KEY_LEN = 32
SALT_LEN = 16
IV_LEN = 12
TAG_LEN = 16

app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# from db import Base, engine
# from db import EncryptedBlob
# from crud import create_blob, get_blob, list_blobs, delete_blob

# #tables
# Base.metadata.create_all(bind=engine)
# If USE_DB=true -> import real DB + CRUD and create tables
# If USE_DB is not true -> provide safe stub functions that raise 503
# -----------------------
USE_DB = os.getenv("USE_DB", "false").lower() == "true"

if USE_DB:
    # real DB imports & init (runs only when USE_DB=true)
    from db import Base, engine
    from db import EncryptedBlob
    from crud import create_blob, get_blob, list_blobs, delete_blob

    # create tables if needed
    Base.metadata.create_all(bind=engine)
else:
    # DB disabled: define safe stubs so endpoints don't crash the app.
    # These stubs raise HTTP 503 so callers know DB is unavailable.
    def create_blob(*args, **kwargs):
        raise HTTPException(status_code=503, detail="Database disabled")

    def get_blob(blob_id):
        raise HTTPException(status_code=503, detail="Database disabled")

    def list_blobs(limit=50):
        raise HTTPException(status_code=503, detail="Database disabled")

    def delete_blob(blob_id):
        raise HTTPException(status_code=503, detail="Database disabled")
# -----------------------
# End DB guard
# -----------------------

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=FileResponse)
def read_index():
    index_path = os.path.join("static", "index.html")
    return index_path


class EncryptRequest(BaseModel):
    plaintext: str
    password: str

class EncryptResponse(BaseModel):
    ciphertext_b64: str

class DecryptRequest(BaseModel):
    ciphertext_b64: str
    password: str

class DecryptResponse(BaseModel):
    plaintext: str

class SaveRequest(BaseModel):
    ciphertext_b64: str
    filename: Optional[str] = None
    note: Optional[str] = None
    owner: Optional[str] = None

# --- helpers ---
def derive_key(password: str, salt: bytes) -> bytes:
    return PBKDF2(password.encode(), salt, dkLen=KEY_LEN, count=PBKDF2_ITER)

# --- API endpoints ---
@app.get("/api/ping")
def ping():
    return {"ok": True, "msg": "pong"}



@app.post("/api/encrypt", response_model=EncryptResponse)
def encrypt(req: EncryptRequest):
    if not req.password:
        raise HTTPException(status_code=400, detail="Password required")
    salt = get_random_bytes(SALT_LEN)
    key = derive_key(req.password, salt)
    iv = get_random_bytes(IV_LEN)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ct, tag = cipher.encrypt_and_digest(req.plaintext.encode("utf-8"))
    blob = salt + iv + tag + ct
    return {"ciphertext_b64": base64.b64encode(blob).decode()}

@app.post("/api/decrypt", response_model=DecryptResponse)
def decrypt(req: DecryptRequest):
    try:
        blob = base64.b64decode(req.ciphertext_b64)
        if len(blob) < (SALT_LEN + IV_LEN + TAG_LEN):
            raise ValueError("Blob too short")
        salt = blob[:SALT_LEN]
        iv = blob[SALT_LEN:SALT_LEN + IV_LEN]
        tag = blob[SALT_LEN + IV_LEN:SALT_LEN + IV_LEN + TAG_LEN]
        ct = blob[SALT_LEN + IV_LEN + TAG_LEN:]
        key = derive_key(req.password, salt)
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        plaintext_bytes = cipher.decrypt_and_verify(ct, tag)
        plaintext = plaintext_bytes.decode("utf-8")
        return {"plaintext": plaintext}
    except Exception:
        raise HTTPException(status_code=400, detail="Decryption failed (bad password or corrupted data)")


from fastapi import Query

@app.post("/api/save", response_model=dict)
def api_save(req: SaveRequest):
    """
    Save ciphertext and optional metadata (JSON body).
    """
    rec = create_blob(
        ciphertext_b64=req.ciphertext_b64,
        filename=req.filename,
        note=req.note,
        owner=req.owner
    )
    return {"id": rec.id, "created_at": rec.created_at.isoformat()}


@app.get("/api/blob/{blob_id}", response_model=dict)
def api_get_blob(blob_id: int):
    rec = get_blob(blob_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": rec.id,
        "ciphertext_b64": rec.ciphertext_b64,
        "filename": rec.filename,
        "note": rec.note,
        "algorithm": rec.algorithm,
        "kdf": rec.kdf,
        "owner": rec.owner,
        "created_at": rec.created_at.isoformat()
    }

@app.get("/api/blobs", response_model=list)
def api_list_blobs(limit: int = Query(50, ge=1, le=200)):
    recs = list_blobs(limit=limit)
    return [{
        "id": r.id,
        "filename": r.filename,
        "note": r.note,
        "created_at": r.created_at.isoformat()
    } for r in recs]

@app.delete("/api/blob/{blob_id}", response_model=dict)
def api_delete_blob(blob_id: int):
    ok = delete_blob(blob_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": True}
