
import os
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import google.generativeai as genai

# -----------------------------
# LIFT: Single-container Web App
# Serves UI at "/" and API at "/generate-content"
# -----------------------------

app = Flask(__name__)
# Same-origin by default; enable CORS if you later host UI separately.
CORS(app, resources={r"/*": {"origins": "*"}})

# ⚠️ EDIT ME: HARD-CODED GEMINI API KEY
# Replace ONLY the string value below with your real key.
GEMINI_API_KEY = "AIzaSyDYNwZHZjDaRc9M-qknfoEpJIprUkmMktM"
genai.configure(api_key=GEMINI_API_KEY)

# Model choice: fast + inexpensive. Change if you need higher quality.
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
model = genai.GenerativeModel(MODEL_NAME)

# Basic request limits (adjust as needed)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB uploads

@app.route("/", methods=["GET"])
def ui():
    # Simple HTML UI (no external assets)
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>LIFT Tool</title>
      <style>
        body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; line-height: 1.4; }
        .card { max-width: 840px; margin: auto; padding: 1.5rem; border: 1px solid #e5e7eb; border-radius: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
        h1 { margin-top: 0; }
        label { display:block; font-weight:600; margin-top: 1rem; margin-bottom: .25rem; }
        textarea, input[type="file"] { width: 100%; }
        textarea { min-height: 120px; }
        button { margin-top: 1rem; padding: .7rem 1rem; border: 0; border-radius: 10px; background:#111827; color: white; cursor:pointer; }
        .muted { color: #6b7280; font-size: .9rem; }
        .ok { color: #059669; }
        .err { color: #b91c1c; white-space: pre-wrap; }
        .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
      </style>
    </head>
    <body>
      <div class="card">
        <h1>LIFT: Learning Innovation Faculty Tool</h1>
        <p class="muted">Paste content or upload a text file. Add Custom Instructions to steer tone, outcomes, Bloom’s level, etc.</p>
        <form id="lift-form" action="/generate-content" method="POST" enctype="multipart/form-data">
          <label>Upload file (plain text, .txt)</label>
          <input type="file" name="file" accept=".txt" />

          <label>Paste text</label>
          <textarea name="text_input" placeholder="Paste course content, lecture notes, article text …"></textarea>

          <label>Custom Instructions</label>
          <textarea name="instructions" placeholder="e.g., Write 5 quiz questions aligned to Bloom’s apply/analyze; academic tone; include feedback."></textarea>

          <button type="submit">Generate</button>
        </form>

        <div id="result" style="margin-top:1rem;"></div>
        <p class="muted">Model: <span class="mono">gemini-1.5-flash</span> (change in code if needed)</p>
      </div>

      <script>
        const form = document.getElementById('lift-form');
        const result = document.getElementById('result');

        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          result.innerHTML = '<p class="muted">Processing…</p>';
          const fd = new FormData(form);
          try {
            const res = await fetch('/generate-content', { method: 'POST', body: fd });
            const data = await res.json();
            if (data.error) {
              result.innerHTML = '<div class="err"><strong>Error:</strong> ' + data.error + '</div>';
            } else {
              const text = (data.generated_text || '').replaceAll('\n', '<br>');
              result.innerHTML = '<div class="ok"><strong>Success</strong></div><div>' + text + '</div>';
            }
          } catch (err) {
            result.innerHTML = '<div class="err">Network error: ' + err + '</div>';
          }
        });
      </script>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")

@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"})

@app.route("/generate-content", methods=["POST"])
def generate_content():
    text_input = request.form.get("text_input", "") or ""
    instructions = request.form.get("instructions", "") or ""
    uploaded_file = request.files.get("file")

    combined_text = ""
    if uploaded_file and uploaded_file.filename:
        try:
            file_text = uploaded_file.read().decode("utf-8", errors="ignore")
            combined_text += file_text + "\n"
        except Exception as e:
            return jsonify({"error": f"Failed to read file: {e}"}), 400
    if text_input.strip():
        combined_text += text_input.strip()

    if not combined_text:
        return jsonify({"error": "Provide text via upload or paste."}), 400

    prompt = f"""You are LIFT, an assistant for faculty.
    Follow the user's Custom Instructions carefully.
    Then, based on the provided Content, generate helpful teaching materials (summary, quiz, discussion prompts, etc.).

    Custom Instructions:
    {instructions}

    Content:
    {combined_text}
    """

    try:
        resp = model.generate_content(prompt)
        output_text = getattr(resp, "text", None) or ""
        return jsonify({"generated_text": output_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # For local dev only. In production we use gunicorn via Dockerfile.
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
