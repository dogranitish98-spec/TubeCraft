"""Bounded upload helpers used by public multipart endpoints."""
from __future__ import annotations

import os
import tempfile

from fastapi import HTTPException, UploadFile

from core.config import get_settings


def max_upload_bytes() -> int:
    try:
        value = int(getattr(get_settings(), "tubecraft_max_upload_mb", 100))
    except Exception:
        value = 100
    return max(1, value) * 1024 * 1024


async def read_upload_limited(upload: UploadFile, limit: int | None = None) -> bytes:
    limit = limit or max_upload_bytes()
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise HTTPException(
                status_code=413,
                detail=f"Uploaded file exceeds the {limit // (1024 * 1024)} MB limit",
            )
        chunks.append(chunk)
    return b"".join(chunks)


async def save_upload_limited(
    upload: UploadFile,
    destination: str,
    limit: int | None = None,
) -> int:
    """Stream an UploadFile to disk with an atomic temp-file swap.

    Unlike ``read_upload_limited`` this never materializes the entire upload in
    Python memory, which is important for mobile/LAN deployments with several
    concurrent media jobs. The temporary file is removed on failure.
    """
    limit = limit or max_upload_bytes()
    directory = os.path.dirname(os.path.realpath(destination)) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".upload-", dir=directory)
    total = 0
    try:
        with os.fdopen(fd, "wb") as out:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > limit:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Uploaded file exceeds the {limit // (1024 * 1024)} MB limit",
                    )
                out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp_path, destination)
        return total
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise
