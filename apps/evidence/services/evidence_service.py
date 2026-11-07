"""
Evidence service layer for EviTrack.
Handles cryptographic hashing, secure physical file storage outside web root,
integrity verification, and forensic QR code generation.
"""
import hashlib
import io
import os
from pathlib import Path
from typing import Any
import uuid

from django.conf import settings
from django.urls import reverse
import qrcode
from qrcode.image.pil import PilImage


def compute_sha256(file_obj: Any, chunk_size: int = 1048576) -> str:
    """
    Computes the SHA-256 cryptographic digest of a file-like object in 1MB chunks.
    Preserves and restores the stream pointer position if seekable.
    
    Args:
        file_obj: File-like object (e.g., UploadedFile, open file handle).
        chunk_size: Size of stream chunk in bytes (default 1MB / 1048576 bytes).
        
    Returns:
        Hexadecimal SHA-256 digest string (64 characters, lowercase).
    """
    initial_pos = None
    if hasattr(file_obj, 'seek') and hasattr(file_obj, 'tell'):
        try:
            initial_pos = file_obj.tell()
            file_obj.seek(0)
        except (OSError, io.UnsupportedOperation):
            initial_pos = None

    hasher = hashlib.sha256()

    if hasattr(file_obj, 'chunks'):
        # Django UploadedFile chunks() generator
        for chunk in file_obj.chunks(chunk_size=chunk_size):
            hasher.update(chunk)
    else:
        while True:
            chunk = file_obj.read(chunk_size)
            if not chunk:
                break
            if isinstance(chunk, str):
                chunk = chunk.encode('utf-8')
            hasher.update(chunk)

    if initial_pos is not None and hasattr(file_obj, 'seek'):
        try:
            file_obj.seek(initial_pos)
        except (OSError, io.UnsupportedOperation):
            pass

    return hasher.hexdigest().lower()


def store_evidence_file(uploaded_file: Any, case: Any) -> str:
    """
    Saves an uploaded evidence file strictly to EVIDENCE_ROOT outside the web root.
    Uses a UUID4 filename to prevent path traversal, filename collisions,
    or direct guessing attacks.
    
    Args:
        uploaded_file: Django UploadedFile instance.
        case: Case instance that owns this evidence item.
        
    Returns:
        Relative path string suitable for Evidence.file_path (relative to EVIDENCE_ROOT).
    """
    evidence_root = Path(getattr(settings, 'EVIDENCE_ROOT', settings.BASE_DIR / 'evidence_store'))
    
    # Sanitize case directory name
    case_folder = f"case_{case.case_no.replace('/', '_').replace(' ', '_')}" if hasattr(case, 'case_no') and case.case_no else f"case_{case.pk}"
    target_dir = evidence_root / case_folder
    target_dir.mkdir(parents=True, exist_ok=True)

    # Preserve file extension in lowercase
    original_name = getattr(uploaded_file, 'name', 'evidence.bin')
    _, ext = os.path.splitext(original_name)
    ext = ext.lower()

    # Generate random UUID filename
    random_filename = f"{uuid.uuid4().hex}{ext}"
    destination_path = target_dir / random_filename

    # Write file chunks to disk
    if hasattr(uploaded_file, 'seek'):
        try:
            uploaded_file.seek(0)
        except (OSError, io.UnsupportedOperation):
            pass

    with open(destination_path, 'wb') as dest:
        if hasattr(uploaded_file, 'chunks'):
            for chunk in uploaded_file.chunks(chunk_size=1048576):
                dest.write(chunk)
        else:
            dest.write(uploaded_file.read())

    # Return relative path from EVIDENCE_ROOT
    return f"{case_folder}/{random_filename}"


def get_evidence_file_path(evidence: Any) -> Path:
    """
    Returns the absolute Path to an evidence file stored on disk.
    
    Args:
        evidence: Evidence model instance.
        
    Returns:
        Path object pointing to physical file.
    """
    evidence_root = Path(getattr(settings, 'EVIDENCE_ROOT', settings.BASE_DIR / 'evidence_store'))
    return evidence_root / evidence.file_path


def verify_evidence_integrity(evidence: Any) -> tuple[bool, str]:
    """
    Reads the physical evidence file from disk, re-calculates its SHA-256 hash,
    and compares it to the immutable hash stored in the Evidence record.
    
    Args:
        evidence: Evidence model instance.
        
    Returns:
        Tuple of (is_valid: bool, computed_hash: str).
    """
    file_path = get_evidence_file_path(evidence)
    
    if not file_path.exists() or not file_path.is_file():
        return False, ''

    with open(file_path, 'rb') as f:
        computed_hash = compute_sha256(f)

    is_valid = (computed_hash == evidence.sha256.lower())
    return is_valid, computed_hash


def generate_qr_label(evidence: Any, request: Any = None) -> bytes:
    """
    Generates a high-contrast QR code image containing essential forensic metadata:
    Evidence No, Case No, Hash Prefix, and deep link URL.
    
    Args:
        evidence: Evidence model instance.
        request: Optional HttpRequest to build fully qualified URL.
        
    Returns:
        PNG image raw bytes.
    """
    evidence_url = reverse('evidence:evidence_detail', kwargs={'pk': evidence.pk})
    if request:
        evidence_url = request.build_absolute_uri(evidence_url)

    qr_payload = (
        f"EviTrack Digital Evidence Label\n"
        f"Evidence No: {evidence.evidence_no}\n"
        f"Case No: {evidence.case.case_no}\n"
        f"SHA-256 (Prefix): {evidence.sha256[:16]}...\n"
        f"Verify URL: {evidence_url}"
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(qr_payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#14213D", back_color="#FFFFFF")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()
