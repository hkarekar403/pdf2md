from flask import Flask, render_template, request, jsonify, send_file
import os
import threading
import uuid
from werkzeug.utils import secure_filename
from converter import convert_pdf_to_md

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

jobs = {}

ALLOWED_EXTENSIONS = {".pdf"}


def allowed_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXTENSIONS


OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def get_default_md_path(pdf_filename):
    base = os.path.splitext(secure_filename(pdf_filename))[0]
    return os.path.join(OUTPUT_FOLDER, f"{base}.md")


def convert_job(job_id, pdf_path, md_path):
    for f in jobs[job_id]["files"]:
        if f["pdf_path"] == pdf_path:
            f["status"] = "converting"
            break
    try:
        md = convert_pdf_to_md(pdf_path)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        for f in jobs[job_id]["files"]:
            if f["pdf_path"] == pdf_path:
                f["status"] = "completed"
                f["md_path"] = md_path
                break
    except Exception as e:
        for f in jobs[job_id]["files"]:
            if f["pdf_path"] == pdf_path:
                f["status"] = "error"
                f["error"] = str(e)
                break


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files[]")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"files": [], "status": "pending", "progress": 0}

    for idx, file in enumerate(files):
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{job_id}_{filename}")
            file.save(pdf_path)
            base = os.path.splitext(filename)[0]
            current_md = os.path.join(OUTPUT_FOLDER, f"{base}.md")
            counter = 1
            while any(f["md_path"] == current_md for f in jobs[job_id]["files"]):
                current_md = os.path.join(OUTPUT_FOLDER, f"{base}_{counter}.md")
                counter += 1
            jobs[job_id]["files"].append({
                "name": filename,
                "size": os.path.getsize(pdf_path),
                "pdf_path": pdf_path,
                "md_path": current_md,
                "status": "pending",
            })

    for file_info in jobs[job_id]["files"]:
        thread = threading.Thread(target=convert_job, args=(job_id, file_info["pdf_path"], file_info["md_path"]))
        thread.start()
    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    total = len(job["files"])
    completed = sum(1 for f in job["files"] if f["status"] in ("completed", "error"))
    job["progress"] = int((completed / total) * 100) if total else 0
    return jsonify(job)


@app.route("/api/download")
def api_download():
    filename = request.args.get("filename", "")
    requested_name = os.path.basename(filename)
    safe_path = os.path.realpath(os.path.join(OUTPUT_FOLDER, requested_name))
    if os.path.dirname(safe_path) != os.path.realpath(OUTPUT_FOLDER):
        return jsonify({"error": "File not found"}), 404
    if not os.path.isfile(safe_path):
        return jsonify({"error": "File not found"}), 404
    return send_file(safe_path, as_attachment=True, download_name=requested_name)


if __name__ == "__main__":
    app.run(debug=False, port=5000)
