"""
Custom template filters and tags for evidence rendering.
"""
from django import template

register = template.Library()


@register.filter(name='file_icon')
def file_icon(mime_type: str | None) -> str:
    """
    Returns an appropriate Bootstrap 5 icon class according to the MIME type or extension.
    """
    if not mime_type:
        return 'bi-file-earmark'

    m = str(mime_type).lower().strip()

    if 'pdf' in m:
        return 'bi-file-earmark-pdf text-danger'
    if 'image' in m:
        return 'bi-file-earmark-image text-info'
    if 'audio' in m:
        return 'bi-file-earmark-music text-warning'
    if 'video' in m:
        return 'bi-file-earmark-play text-primary'
    if 'word' in m or 'msword' in m or 'document' in m:
        return 'bi-file-earmark-word text-primary'
    if 'excel' in m or 'sheet' in m or 'csv' in m:
        return 'bi-file-earmark-excel text-success'
    if 'text' in m:
        return 'bi-file-earmark-text text-secondary'
    if 'zip' in m or 'compressed' in m or 'tar' in m or 'gzip' in m:
        return 'bi-file-earmark-zip text-warning'
    if 'json' in m or 'xml' in m:
        return 'bi-file-earmark-code text-info'

    return 'bi-file-earmark text-muted'


@register.filter(name='file_size_display')
def file_size_display(bytes_value: int | float | None) -> str:
    """
    Converts bytes integer into formatted human-readable string (KB, MB, GB).
    """
    if bytes_value is None:
        return '0 B'

    try:
        bytes_val = float(bytes_value)
    except (ValueError, TypeError):
        return '0 B'

    if bytes_val < 1024:
        return f"{int(bytes_val)} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


@register.filter(name='truncate_hash')
def truncate_hash(hash_val: str | None, length: int = 12) -> str:
    """
    Truncates a hash to first `length` characters followed by an ellipsis.
    """
    if not hash_val:
        return ''
    s = str(hash_val).strip()
    if len(s) <= length:
        return s
    return f"{s[:length]}…"
