import os
from flask import Flask, request, jsonify, Response, session
from flask_cors import CORS
import google.generativeai as genai

# -----------------------------
# LIFT: Web App with Chat UI + Conversational Memory
# -----------------------------

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Secret key for Flask sessions (used for conversational memory)
# In Koyeb, set FLASK_SECRET_KEY as an environment variable.
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")

# Gemini API key via environment variable (Koyeb: set GEMINI_API_KEY)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise RuntimeError("Set the GEMINI_API_KEY environment variable before running the app.")

genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
model = genai.GenerativeModel(MODEL_NAME)

# Max upload size
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB uploads

# Conversational memory settings
MAX_HISTORY_TURNS = 6            # how many (user, assistant) pairs to keep
USER_SNIPPET_CHARS = 600         # chars of user content to store
ASSISTANT_SNIPPET_CHARS = 2000   # chars of assistant output to store


@app.route("/", methods=["GET"])
def ui():
    # Chat-style HTML UI
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>LIFT Tool</title>
      <style>
        * {{
          box-sizing: border-box;
        }}

        /* Reset some default margins that can break layout */
        body, p, div, h1, h2, h3, h4, h5, h6 {{
          margin: 0;
          padding: 0;
        }}

        body {{
          font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
          background: #f3f4f6;
          color: #111827;
        }}

        .app {{
          min-height: 100vh;
          display: flex;
          align-items: stretch;
          justify-content: center;
          padding: 1.5rem;
        }}

        .card {{
          background: #ffffff;
          width: 100%;
          max-width: 960px;
          border-radius: 18px;
          box-shadow: 0 10px 30px rgba(15,23,42,0.08);
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }}

        .header {{
          padding: 1.25rem 1.5rem 0.75rem;
          border-bottom: 1px solid #e5e7eb;
        }}

        .title-row {{
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }}

        .pill {{
          width: 32px;
          height: 32px;
          border-radius: 999px;
          background: linear-gradient(135deg, #6366f1, #06b6d4);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 700;
          font-size: 0.9rem;
        }}

        h1 {{
          font-size: 1.1rem;
        }}

        .subtitle {{
          margin-top: 0.4rem;
          font-size: 0.9rem;
          color: #6b7280;
        }}

        .body {{
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          padding: 0.75rem 1.5rem 1rem;
          min-height: 0;
          flex: 1;
        }}

        .chat-window {{
          border-radius: 12px;
          border: 1px solid #e5e7eb;
          background: #f3f4f6;
          padding: 0.75rem;
          overflow-y: auto;
          flex: 1;
          max-height: 60vh;
        }}

        .chat-window::-webkit-scrollbar {{
          width: 6px;
        }}
        .chat-window::-webkit-scrollbar-thumb {{
          background: #d1d5db;
          border-radius: 999px;
        }}

        /* Chat messages */

        .message {{
          width: 100%;
          display: flex;
          align-items: flex-start;
          margin-bottom: 0.75rem;
          gap: 0.5rem;
        }}

        .message.assistant {{
          flex-direction: row;
        }}

        .message.user {{
          flex-direction: row-reverse;
        }}

        .avatar {{
          width: 32px;
          height: 32px;
          border-radius: 999px;
          flex-shrink: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.75rem;
          font-weight: 600;
        }}

        .assistant .avatar {{
          background: #eef2ff;
          color: #3730a3;
        }}

        .user .avatar {{
          background: #ecfeff;
          color: #0f766e;
        }}

        .bubble {{
          max-width: 60%;
          display: inline-block;
          margin: 0 6px;
          padding: 0.75rem 1rem;
          border-radius: 14px;
          font-size: 0.9rem;
          line-height: 1.45;
          white-space: normal;      /* don't preserve indentation whitespace */
          word-break: break-word;
        }}

        .assistant .bubble {{
          background: #ffffff;
          border: 1px solid #e5e7eb;
        }}

        .user .bubble {{
          background: #111827;
          color: #f9fafb;
        }}

        .name {{
          font-size: 0.75rem;
          font-weight: 600;
          margin-bottom: 0.15rem;
          opacity: 0.8;
        }}

        .bubble-body {{
          font-size: 0.9rem;
          text-align: left;
        }}

        .typing-dots {{
          display: inline-flex;
          gap: 3px;
          align-items: center;
        }}

        .dot {{
          width: 4px;
          height: 4px;
          border-radius: 999px;
          background: #9ca3af;
          animation: blink 1.4s infinite both;
        }}

        .dot:nth-child(2) {{
          animation-delay: 0.2s;
        }}

        .dot:nth-child(3) {{
          animation-delay: 0.4s;
        }}

        @keyframes blink {{
          0%, 80%, 100% {{ opacity: 0.3; }}
          40% {{ opacity: 1; }}
        }}

        /* Form */

        .form-wrapper {{
          border-radius: 12px;
          border: 1px solid #e5e7eb;
          padding: 0.75rem 0.9rem 0.9rem;
          background: #ffffff;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }}

        .form-row {{
          display: flex;
          gap: 0.75rem;
          flex-wrap: wrap;
        }}

        .field {{
          flex: 1 1 200px;
          display: flex;
          flex-direction: column;
          gap: 0.2rem;
        }}

        label {{
          font-size: 0.8rem;
          font-weight: 600;
          color: #4b5563;
        }}

        textarea {{
          width: 100%;
          resize: vertical;
          min-height: 70px;
          padding: 0.45rem 0.55rem;
          border-radius: 10px;
          border: 1px solid #d1d5db;
          font-size: 0.9rem;
          font-family: inherit;
        }}

        textarea:focus {{
          outline: none;
          border-color: #6366f1;
          box-shadow: 0 0 0 1px #6366f1;
        }}

        input[type="file"] {{
          font-size: 0.8rem;
        }}

        .hint {{
          font-size: 0.75rem;
          color: #9ca3af;
        }}

        .actions {{
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 0.75rem;
          margin-top: 0.25rem;
        }}

        button[type="submit"] {{
          padding: 0.6rem 1.2rem;
          border-radius: 999px;
          border: none;
          background: #111827;
          color: white;
          font-size: 0.9rem;
          font-weight: 500;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
        }}

        button[type="submit"]:disabled {{
          opacity: 0.6;
          cursor: default;
        }}

        .muted {{
          color: #6b7280;
          font-size: 0.75rem;
        }}

        .error-text {{
          color: #b91c1c;
          font-size: 0.8rem;
          margin-top: 0.25rem;
        }}

        .footer {{
          border-top: 1px solid #e5e7eb;
          padding: 0.5rem 1.5rem 0.65rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.75rem;
          color: #9ca3af;
        }}

        .mono {{
          font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        }}

        @media (max-width: 640px) {{
          .app {{
            padding: 0.75rem;
          }}

          .chat-window {{
            max-height: 55vh;
          }}

          .bubble {{
            max-width: 90%;
          }}
        }}
      </style>
    </head>
    <body>
      <div class="app">
        <div class="card">
          <header class="header">
            <div class="title-row">
              <div class="pill">L</div>
              <div>
                <h1>LIFT: Learning Innovation Faculty Tool</h1>
                <p class="subtitle">
                  Chat with LIFT using course content + custom teaching instructions.
                </p>
              </div>
            </div>
          </header>

          <main class="body">
            <div id="chat-window" class="chat-window">
              <div class="message assistant">
                <div class="avatar">L</div>
                <div class="bubble">
                  <div class="name">LIFT</div>
                  <div class="bubble-body">Hi! Paste course content or upload a .txt file, add your Custom Instructions (tone, Bloom’s level, outcomes, etc.), and I’ll generate teaching materials here in the chat.</div>
                </div>
              </div>
            </div>

            <form id="lift-form" action="/generate-content" method="POST"
                  enctype="multipart/form-data" class="form-wrapper">
              <div class="form-row">
                <div class="field">
                  <label for="file">Upload file (.txt)</label>
                  <input id="file" type="file" name="file" accept=".txt" />
                  <div class="hint">Optional. Plain text files work best.</div>
                </div>
                <div class="field">
                  <label for="instructions">Custom Instructions</label>
                  <textarea id="instructions" name="instructions"
                    placeholder="e.g., Write 5 quiz questions at Bloom’s apply/analyze; academic tone; include brief feedback."></textarea>
                </div>
              </div>
              <div class="field">
                <label for="text_input">Paste content</label>
                <textarea id="text_input" name="text_input"
                  placeholder="Paste course content, lecture notes, or article text here."></textarea>
              </div>
              <div class="actions">
                <div class="muted">
                  LIFT will respond in this chat window. Conversation memory is enabled per browser.
                </div>
                <button type="submit">
                  <span>Generate with LIFT</span>
                </button>
              </div>
              <div id="error" class="error-text" style="display:none;"></div>
            </form>
          </main>

          <footer class="footer">
            <span>Model: <span class="mono">{MODEL_NAME}</span></span>
            <span>Powered by Gemini</span>
          </footer>
        </div>
      </div>

      <script>
        const form = document.getElementById('lift-form');
        const chat = document.getElementById('chat-window');
        const errorBox = document.getElementById('error');
        const submitBtn = form.querySelector('button[type="submit"]');

        function escapeHTML(str) {{
          return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
        }}

        function formatWithBreaks(str) {{
          return escapeHTML(str).replace(/\\n/g, "<br>");
        }}

        function scrollChatToBottom() {{
          chat.scrollTop = chat.scrollHeight;
        }}

        function addMessage(role, htmlBody) {{
          const wrapper = document.createElement('div');
          wrapper.className = 'message ' + role;

          const avatar = document.createElement('div');
          avatar.className = 'avatar';
          avatar.textContent = role === 'user' ? 'You' : 'L';

          const bubble = document.createElement('div');
          bubble.className = 'bubble';

          const name = document.createElement('div');
          name.className = 'name';
          name.textContent = role === 'user' ? 'You' : 'LIFT';

          const body = document.createElement('div');
          body.className = 'bubble-body';
          body.innerHTML = htmlBody;

          bubble.appendChild(name);
          bubble.appendChild(body);

          wrapper.appendChild(avatar);
          wrapper.appendChild(bubble);

          chat.appendChild(wrapper);
          scrollChatToBottom();

          return wrapper;
        }}

        function createTypingMessage() {{
          const typingHTML = '<span class="typing-dots">' +
            '<span class="dot"></span>' +
            '<span class="dot"></span>' +
            '<span class="dot"></span>' +
            '</span>';
          const el = addMessage('assistant', typingHTML);
          return el;
        }}

        form.addEventListener('submit', async (e) => {{
          e.preventDefault();
          errorBox.style.display = 'none';
          errorBox.textContent = '';

          const textInput = document.getElementById('text_input').value.trim();
          const instructions = document.getElementById('instructions').value.trim();
          const fileInput = document.getElementById('file');
          const file = fileInput.files[0];

          if (!textInput && !instructions && !file) {{
            errorBox.textContent = 'Provide text via upload, paste, or instructions.';
            errorBox.style.display = 'block';
            return;
          }}

          let summaryParts = [];
          if (instructions) {{
            summaryParts.push('<strong>Instructions:</strong><br>' + formatWithBreaks(instructions));
          }}
          if (textInput) {{
            const preview = textInput.length > 600 ? textInput.slice(0, 600) + '…' : textInput;
            summaryParts.push('<strong>Content:</strong><br>' + formatWithBreaks(preview));
          }}
          if (file && !textInput) {{
            summaryParts.push('<strong>File:</strong> ' + escapeHTML(file.name));
          }}

          const userBody = summaryParts.length
            ? summaryParts.join('<br><br>')
            : 'Generate teaching materials based on the uploaded file.';

          addMessage('user', userBody);

          const typingMsg = createTypingMessage();
          submitBtn.disabled = true;

          const fd = new FormData(form);

          try {{
            const res = await fetch('/generate-content', {{
              method: 'POST',
              body: fd
            }});

            let data;
            try {{
              data = await res.json();
            }} catch (jsonErr) {{
              throw new Error('Unexpected response from server.');
            }}

            const bubbleBody = typingMsg.querySelector('.bubble-body');

            if (!res.ok || data.error) {{
              bubbleBody.innerHTML = '<span class="error-text"><strong>Error:</strong> ' +
                formatWithBreaks(data.error || 'Request failed.') +
                '</span>';
            }} else {{
              const text = (data.generated_text || '');
              bubbleBody.innerHTML = formatWithBreaks(text);
            }}
          }} catch (err) {{
            const bubbleBody = typingMsg.querySelector('.bubble-body');
            bubbleBody.innerHTML = '<span class="error-text"><strong>Network error:</strong> ' +
              formatWithBreaks(err.message || String(err)) +
              '</span>';
          }} finally {{
            submitBtn.disabled = false;
            scrollChatToBottom();
          }}
        }});
      </script>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"})


def _get_history():
    """Get conversation history for this browser session."""
    return session.get("lift_history", [])


def _save_history(history):
    """Save truncated conversation history back to the session cookie."""
    history = history[-MAX_HISTORY_TURNS:]
    session["lift_history"] = history


def _build_history_block(history):
    """Build a text block summarizing prior conversation for the model."""
    if not history:
        return "No prior conversation.\n"

    lines = []
    for turn in history:
        role = turn.get("role", "user").upper()
        content = turn.get("content", "")
        lines.append(f"{role}:\n{content}\n")
    return "\n".join(lines)


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

    if not combined_text and not instructions.strip():
        return jsonify({"error": "Provide text via upload, paste, or instructions."}), 400

    # ---- Conversational memory ----
    history = _get_history()
    history_block = _build_history_block(history)

    # Build a user message summary to store in memory (smaller than full content)
    user_summary_parts = []
    if instructions.strip():
        user_summary_parts.append("Instructions:\n" + instructions.strip())
    if combined_text.strip():
        snippet = combined_text.strip()[:USER_SNIPPET_CHARS]
        user_summary_parts.append("Content snippet:\n" + snippet)

    user_summary = (
        "\n\n".join(user_summary_parts)
        if user_summary_parts
        else "(no explicit content, meta question)"
    )

    # ---- Prompt with history ----
    prompt = f"""You are LIFT, an AI assistant for faculty.

You specialize in generating and refining teaching materials:
- Learning outcomes
- Scaffolding and activities
- Summaries
- Quiz and exam questions (with Bloom’s alignment when requested)
- Discussion prompts
- Feedback and rubrics
- Accessibility-minded suggestions

You have access to the prior conversation with this user in this session.
Use it to maintain context, refer back to earlier outputs, and keep style and constraints consistent.

Below is the previous conversation, followed by the user's latest request.

===== PRIOR CONVERSATION (MOST RECENT LAST) =====
{history_block}
===== END PRIOR CONVERSATION =====

Now process the user's latest Custom Instructions and Content.

Custom Instructions (for this turn):
{instructions}

New Content (for this turn):
{combined_text}

Respond with clear, faculty-facing teaching materials. If the user asks meta-questions about LIFT itself,
answer those directly and clearly.
"""

    try:
        resp = model.generate_content(prompt)
        output_text = getattr(resp, "text", None) or ""

        # ---- Update conversation history ----
        history.append(
            {
                "role": "user",
                "content": user_summary,
            }
        )
        history.append(
            {
                "role": "assistant",
                "content": output_text[:ASSISTANT_SNIPPET_CHARS],
            }
        )
        _save_history(history)

        return jsonify({"generated_text": output_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # For local dev only. In production (Koyeb), you'll typically use gunicorn via Dockerfile.
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
