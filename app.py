import os
from flask import Flask, request, jsonify, Response, session
from flask_cors import CORS
import google.generativeai as genai
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# -----------------------------
# LIFT: Web App with Chat UI + Conversational Memory + PII Scrubbing
# -----------------------------

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise RuntimeError("Set the GEMINI_API_KEY environment variable before running the app.")

genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
model = genai.GenerativeModel(MODEL_NAME)

# Initialize PII Scrubbing Engines
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB uploads
MAX_HISTORY_TURNS = 6
ASSISTANT_SNIPPET_CHARS = 2000

# Mapping of use cases to system context
USE_CASES = {
    "none": "General instructional support.",
    "uc1": "Context: Rapid Course Material Development. Focus on reducing prep time for new faculty by generating outlines, lecture notes, and presentations.",
    "uc2": "Context: Accessible Multi-Format Learning. Focus on ADA compliance, generating transcripts, and simplified summaries.",
    "uc3": "Context: Automated Assessment & Rubrics. Focus on authentic assessments and Bloom's Taxonomy alignment.",
    "uc4": "Context: Flipped Classroom. Focus on pre-class video scripts and interactive quizzes.",
    "uc5": "Context: Cross-Disciplinary Revision. Focus on modernizing curriculum and integrating diverse perspectives."
}

def scrub_pii(text):
    """Local function to redact sensitive info before sending to API."""
    if not text.strip():
        return text
    # Analyze text for PII entities (Names, Emails, Phones, etc.)
    results = analyzer.analyze(text=text, entities=[], language='en')
    # Redact identified PII
    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized_result.text

@app.route("/", methods=["GET"])
def ui():
    # UI remains identical to your working version with "Paste content" removed
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>LIFT Tool</title>
      <style>
        body {{ font-family: system-ui, sans-serif; background: #f3f4f6; padding: 1.5rem; }}
        .card {{ background: #ffffff; max-width: 960px; margin: auto; border-radius: 18px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); overflow: hidden; display: flex; flex-direction: column; }}
        .header, .footer {{ padding: 1rem 1.5rem; background: #fff; border-bottom: 1px solid #e5e7eb; }}
        .body {{ padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }}
        .chat-window {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; height: 400px; overflow-y: auto; padding: 1rem; }}
        .message {{ margin-bottom: 1rem; display: flex; }}
        .user {{ justify-content: flex-end; }}
        .bubble {{ max-width: 70%; padding: 0.75rem 1rem; border-radius: 12px; font-size: 0.9rem; }}
        .user .bubble {{ background: #111827; color: #fff; }}
        .assistant .bubble {{ background: #fff; border: 1px solid #e5e7eb; }}
        .form-wrapper {{ display: flex; flex-direction: column; gap: 1rem; border-top: 1px solid #e5e7eb; padding-top: 1rem; }}
        .form-row {{ display: flex; gap: 1rem; }}
        .field {{ flex: 1; display: flex; flex-direction: column; gap: 0.3rem; }}
        textarea {{ min-height: 80px; padding: 0.5rem; border-radius: 8px; border: 1px solid #d1d5db; }}
        button {{ background: #111827; color: #fff; padding: 0.7rem; border-radius: 999px; border: none; cursor: pointer; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header"><h1>LIFT: Learning Innovation Faculty Tool</h1></div>
        <div class="body">
          <div id="chat-window" class="chat-window"></div>
          <form id="lift-form" class="form-wrapper">
            <div class="form-row">
              <div class="field">
                <label>Use Case</label>
                <select id="use_case" name="use_case">
                  <option value="none">General Support</option>
                  <option value="uc1">UC1: Course Development</option>
                  <option value="uc2">UC2: Accessibility</option>
                  <option value="uc3">UC3: Assessment</option>
                </select>
              </div>
              <div class="field">
                <label>or upload a custom use case</label>
                <input id="file" type="file" name="file" accept=".txt" />
              </div>
            </div>
            <div class="field">
              <label>Custom Instructions</label>
              <textarea id="instructions" name="instructions" placeholder="Enter instructions..."></textarea>
            </div>
            <button type="submit">Generate with LIFT</button>
          </form>
        </div>
        <div class="footer">Model: {MODEL_NAME} | Secure Local PII Scrubbing Active</div>
      </div>
      <script>
        const form = document.getElementById('lift-form');
        const chat = document.getElementById('chat-window');
        
        form.addEventListener('submit', async (e) => {{
          e.preventDefault();
          const instructions = document.getElementById('instructions').value;
          const formData = new FormData(form);
          
          const userMsg = document.createElement('div');
          userMsg.className = 'message user';
          userMsg.innerHTML = `<div class="bubble">${{instructions}}</div>`;
          chat.appendChild(userMsg);

          const res = await fetch('/generate-content', {{ method: 'POST', body: formData }});
          const data = await res.json();
          
          const aiMsg = document.createElement('div');
          aiMsg.className = 'message assistant';
          aiMsg.innerHTML = `<div class="bubble">${{data.generated_text}}</div>`;
          chat.appendChild(aiMsg);
          chat.scrollTop = chat.scrollHeight;
        }});
      </script>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")

@app.route("/generate-content", methods=["POST"])
def generate_content():
    instructions = request.form.get("instructions", "") or ""
    use_case_key = request.form.get("use_case", "none")
    uploaded_file = request.files.get("file")

    use_case_context = USE_CASES.get(use_case_key, USE_CASES["none"])

    # 1. Gather original text
    raw_content = ""
    if uploaded_file and uploaded_file.filename:
        try:
            raw_content += uploaded_file.read().decode("utf-8", errors="ignore") + "\n"
        except Exception as e:
            return jsonify({"error": f"File error: {e}"}), 400

    # 2. LOCAL SCRUBBING: Clean the data BEFORE it goes to the prompt
    clean_instructions = scrub_pii(instructions)
    clean_content = scrub_pii(raw_content)

    history = session.get("lift_history", [])
    history_block = "\n".join([f"{turn['role'].upper()}: {turn['content']}" for turn in history])

    prompt = f"""You are LIFT, an AI assistant for faculty.
CONTEXT: {use_case_context}

PREVIOUS:
{history_block}

LATEST REQUEST:
Instructions: {clean_instructions}
Content: {clean_content}
"""

    try:
        resp = model.generate_content(prompt)
        output_text = getattr(resp, "text", "No response.")

        # Update History
        history.append({"role": "user", "content": clean_instructions[:200]})
        history.append({"role": "assistant", "content": output_text[:ASSISTANT_SNIPPET_CHARS]})
        session["lift_history"] = history[-MAX_HISTORY_TURNS:]

        return jsonify({"generated_text": output_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
