from .analysis.file_parser import save_upload, AllowedFileError, FileTooLargeError

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def analysis_uploads(file_objs):
    """
    file_objs: Flaskの request.files.getlist('file') 等で得たファイル配列
    戻り値: dict 例 {'uploaded': ['a.pdf', 'b.png']}
    """
    if not file_objs:
        raise ValueError('No files provided')

    uploaded = []
    for f in file_objs:
        save_upload(f, max_size=MAX_FILE_SIZE)
        uploaded.append(f.filename)
    return {'uploaded': uploaded}
    from .analysis.file_parser import save_upload, AllowedFileError, FileTooLargeError
from .analysis.extractors import extract_from_paths
from .analysis.recommender import analyze_text

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def analysis_uploads(file_objs):
    if not file_objs:
        raise ValueError('No files provided')
    uploaded = []
    for f in file_objs:
        save_upload(f, max_size=MAX_FILE_SIZE)
        uploaded.append(f.filename)
    return {'uploaded': uploaded}

def analyze_uploads_and_recommend(file_objs):
    """アップロードを保存しつつPDF/JPGからテキスト抽出→推薦を返す"""
    if not file_objs:
        raise ValueError('No files provided')

    # 保存
    saved_paths = []
    uploaded = []
    for f in file_objs:
        path = save_upload(f, max_size=MAX_FILE_SIZE)
        saved_paths.append(path)
        uploaded.append(f.filename)

    # 抽出
    text, sources, ocr_status = extract_from_paths(saved_paths)

    # 推薦（抽出テキストは「興味」側に寄せて投入）
    analysis = analyze_text("", text)

    preview = text[:500]
    return {
        "uploaded": uploaded,
        "text_preview": preview,
        "sources": sources,
        "ocr_status": ocr_status,
        "analysis": analysis
    }

