import os

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}

class AllowedFileError(Exception):
    """Raised when an unsupported file type is uploaded."""

class FileTooLargeError(Exception):
    """Raised when the uploaded file exceeds the allowed size."""

def save_upload(file_obj, upload_dir='uploads', max_size=None):
    filename = getattr(file_obj, 'filename', None)
    if not filename:
        raise ValueError('Missing filename')

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AllowedFileError('Unsupported file type')

    data = file_obj.read()
    if max_size is not None and len(data) > max_size:
        raise FileTooLargeError('File too large')

    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, filename)
    with open(path, 'wb') as f:
        f.write(data)

    # 以降でも読みたい場合に備えて先頭へ戻す
    file_obj.seek(0)
    return path
