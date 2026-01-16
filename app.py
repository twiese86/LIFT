@app.route("/", methods=["GET"])
def ui():
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>LIFT Tool</title>
      <style>
        * {{ box-sizing: border-box; }}
        body, p, div, h1, h2, h3, h4, h5, h6 {{ margin: 0; padding: 0; }}
        body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: #f3f4f6; color: #111827; }}
        .app {{ min-height: 100vh; display: flex; align-items: stretch; justify-content: center; padding: 1.5rem; }}
        .card {{ background: #ffffff; width: 100%; max-width: 960px; border-radius: 18px; box-shadow: 0 10px 30px rgba(15,23,42,0.08); display: flex; flex-direction: column; overflow: hidden; }}
        .header {{ padding: 1.25rem 1.5rem 0.75rem; border-bottom: 1px solid #e5e7eb; }}
        .title-row {{ display: flex; align-items: center; gap: 0.75rem; }}
        .pill {{ width: 32px; height: 32px; border-radius: 999px; background: linear-gradient(135deg, #6366f1, #06b6d4); display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 0.9rem; }}
        h1 {{ font-size: 1.1rem; }}
        .subtitle {{ margin-top: 0.4rem; font-size: 0.9rem; color: #6b7280; }}
        .body {{ display: flex; flex-direction: column; gap: 0.75rem; padding: 0.75rem 1.5rem 1rem; min-height: 0; flex: 1; }}
        .chat-window {{ border-radius: 12px; border: 1px solid #e5e7eb; background: #f3f4f6; padding: 0.75rem; overflow-y: auto; flex: 1; max-height: 60vh; }}
        .chat-window::-webkit-scrollbar {{ width: 6px; }}
        .chat-window::-webkit-scrollbar-thumb {{ background: #d1d5db; border-radius: 999px; }}
        .message {{ width: 100%; display: flex; align-items: flex-start; margin-bottom: 0.75rem; gap: 0.5rem; }}
        .message.assistant {{ flex-direction: row; }}
        .message.user {{ flex-direction: row-reverse; }}
        .avatar {{ width: 32px; height: 32px; border-radius: 999px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 600; }}
        .assistant .avatar {{ background: #eef2ff; color: #3730a3; }}
        .user .avatar {{ background: #ecfeff; color: #0f766e; }}
        .bubble {{ max-width: 60%; display: inline-block; margin: 0 6px; padding: 0.75rem 1rem; border-radius: 14px; font-size: 0.9rem; line-height: 1.45; white-space: normal; word-break: break-word; }}
        .assistant .bubble {{ background: #ffffff; border: 1px solid #e5e7eb; }}
        .user .bubble {{ background: #111827; color: #f9fafb; }}
        .name {{ font-size: 0.75rem; font-weight: 600; margin-bottom: 0.15rem; opacity: 0.8; }}
        .bubble-body {{ font-size: 0.9rem; text-align: left; }}
        .typing-dots {{ display: inline-flex; gap: 3px; align-items: center; }}
        .dot {{ width: 4px; height: 4px; border-radius: 999px; background: #9ca3af; animation: blink 1.4s infinite both; }}
        .dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .dot:nth-child(3) {{ animation-delay: 0.4s; }}
        @keyframes blink {{ 0%, 80%, 100% {{ opacity: 0.3; }} 40% {{ opacity: 1; }} }}
        .form-wrapper {{ border-radius: 12px; border: 1px solid #e5e7eb; padding: 0.75rem 0.9rem 0.9rem; background: #ffffff; display: flex; flex-direction: column; gap: 0.5rem; }}
        .form-row {{ display: flex; gap: 0.75rem; flex-wrap: wrap; }}
        .field {{ flex: 1 1 200px; display: flex; flex-direction: column; gap: 0.2rem; }}
        label {{ font-size: 0.8rem; font-weight: 600; color: #4b5563; }}
        textarea, select {{ width: 100%; padding: 0.45rem 0.55rem; border-radius: 10px; border: 1px solid #d1d5db; font-size: 0.9rem; font-family: inherit; }}
        textarea {{ resize: vertical; min-height: 70px; }}
        textarea:focus, select:focus {{ outline: none; border-color: #6366f1; box-shadow: 0 0 0 1px #6366f1; }}
        .actions {{ display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; margin-top: 0.25rem; }}
        button[type="submit"] {{ padding: 0.6rem 1.2rem; border-radius: 999px; border: none; background: #111827; color: white; font-size: 0.9rem; font-weight: 500; cursor: pointer; display: inline-flex; align-items: center; gap: 0.4rem; }}
        button[type="submit"]:disabled {{ opacity: 0.6; cursor: default; }}
        .muted {{ color: #6b7280; font-size: 0.75rem; }}
        .error-text {{ color: #b91c1c; font-size: 0.8rem; margin-top: 0.25rem; }}
        .footer {{ border-top: 1px solid #e5e7eb; padding: 0.5rem 1.5rem 0.65rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: #9ca3af; }}
        .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
        @media (max-width: 640px) {{ .app {{ padding: 0.75rem; }} .chat-window {{ max-height: 55vh; }} .bubble {{ max-width: 90%; }} }}
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
                <p class="subtitle">Chat with LIFT using course content + custom teaching instructions.</p>
              </div>
            </div>
          </header>

          <main class="body">
            <div id="chat-window" class="chat-window">
              <div class="message assistant">
                <div class="avatar">L</div>
                <div class="bubble">
                  <div class="name">LIFT</div>
                  <div class="bubble-body">Hi! Select a use case below, provide your instructions or upload a .txt file, and I'll generate specialized teaching materials for you.</div>
                </div>
              </div>
            </div>

            <form id="lift-form" action="/generate-content" method="POST" enctype="multipart/form-data" class="form-wrapper">
              <div class="form-row">
                <div class="field">
                  <label for="use_case">Select a Use Case</label>
                  <select id="use_case" name="use_case">
                    <option value="none">General / No Specific Use Case</option>
                    <option value="uc1">Use Case 1: Rapid Course Material Development</option>
                    <option value="uc2">Use Case 2: Accessible Multi-Format Materials</option>
                    <option value="uc3">Use Case 3: Assessment & Rubric Development</option>
                    <option value="uc4">Use Case 4: Flipped Classroom Content</option>
                    <option value="uc5">Use Case 5: Cross-Disciplinary Revision</option>
                  </select>
                </div>
                <div class="field">
                  <label for="file">Or upload a custom use case:</label>
                  <input id="file" type="file" name="file" accept=".txt" />
                </div>
              </div>
              <div class="form-row">
                <div class="field">
                  <label for="instructions">Custom Instructions</label>
                  <textarea id="instructions" name="instructions" placeholder="e.g., Write 5 quiz questions based on the uploaded material..."></textarea>
                </div>
              </div>
              <div class="actions">
                <div class="muted">Conversation memory is enabled per browser.</div>
                <button type="submit"><span>Generate with LIFT</span></button>
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

        function escapeHTML(str) {{ return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;"); }}
        function formatWithBreaks(str) {{ return escapeHTML(str).replace(/\\n/g, "<br>"); }}
        function scrollChatToBottom() {{ chat.scrollTop = chat.scrollHeight; }}

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

        form.addEventListener('submit', async (e) => {{
          e.preventDefault();
          errorBox.style.display = 'none';
          const instructions = document.getElementById('instructions').value.trim();
          const useCaseSelect = document.getElementById('use_case');
          const useCaseText = useCaseSelect.options[useCaseSelect.selectedIndex].text;
          const file = document.getElementById('file').files[0];

          if (!instructions && !file) {{
            errorBox.textContent = 'Provide instructions or upload a file.';
            errorBox.style.display = 'block';
            return;
          }}

          let summaryParts = [`<strong>Mode:</strong> ${{useCaseText}}`];
          if (instructions) summaryParts.push('<strong>Instructions:</strong><br>' + formatWithBreaks(instructions));
          if (file) summaryParts.push('<strong>File:</strong> ' + escapeHTML(file.name));

          addMessage('user', summaryParts.join('<br><br>'));
          const typingMsg = addMessage('assistant', '<span class="typing-dots"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span>');
          submitBtn.disabled = true;

          try {{
            const res = await fetch('/generate-content', {{ method: 'POST', body: new FormData(form) }});
            const data = await res.json();
            const bubbleBody = typingMsg.querySelector('.bubble-body');
            if (!res.ok) bubbleBody.innerHTML = '<span class="error-text">Error: ' + (data.error || 'Failed') + '</span>';
            else bubbleBody.innerHTML = formatWithBreaks(data.generated_text);
          }} catch (err) {{
            typingMsg.querySelector('.bubble-body').innerHTML = 'Network error.';
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
