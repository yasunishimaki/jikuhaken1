from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path

from backend.api import analysis_uploads, analyze_uploads_and_recommend
from backend.analysis.recommender import analyze_text

BASE_DIR = Path(__file__).resolve().parents[1]
FRONT_DIR = BASE_DIR / "frontend" / "pages"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(FRONT_DIR, "self_analysis_form.html")

# 既存：保存だけ（分析なし）
@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("file")
    result = analysis_uploads(files)
    return jsonify(result)

# 既存：テキスト分析（質問フォーム用）
@app.route("/analyze-text", methods=["POST"])
def analyze_text_route():
    data = request.get_json(force=True, silent=True) or {}
    q1 = (data.get("q1") or "").strip()
    q2 = (data.get("q2") or "").strip()
    result = analyze_text(q1, q2)
    return jsonify(result)

# 追加：アップロード→抽出→分析（PDF/JPG/PNG用）
@app.route("/analyze-uploads", methods=["POST"])
def analyze_uploads_route():
    files = request.files.getlist("file")
    result = analyze_uploads_and_recommend(files)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
