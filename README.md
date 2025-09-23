# LIFT — One-Container Production App (UI + API)

This bundle gives you the **fastest, cheapest, easiest** deployment path: a single Docker container that serves both the **web UI** and the **/generate-content** API. Deploy it on any Docker host (e.g., **Koyeb** free Starter, **Render** free instances, **Railway** free credits, **Fly.io**, a $5 VPS, etc.).

---

## ✍️ One edit required

Open `app.py`, find:

```python
GEMINI_API_KEY = "PASTE_YOUR_GEMINI_API_KEY_HERE"
```

and paste your real key **between the quotes**.

*(Optional)* Change the model by editing:

```python
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
```

---

## 🚀 Deploy anywhere (Docker)

### Option A — Push to any Docker host
1. Build the image
   ```bash
   docker build -t lift:prod .
   ```
2. Run locally once (optional sanity check)
   ```bash
   docker run -p 8080:8080 lift:prod
   # open http://localhost:8080
   ```
3. Push the image to your registry of choice (GHCR, Docker Hub).
   ```bash
   docker tag lift:prod ghcr.io/YOUR_USER/lift:prod
   docker push ghcr.io/YOUR_USER/lift:prod
   ```
4. Create a new service on your platform and point it at the image.

### Option B — Git deploy (provider builds image)
1. Create a new Git repo with these files and push.
2. On your host (Koyeb/Render/Railway/Fly.io), choose **Deploy from Git**.
3. It will detect the **Dockerfile** automatically and build the container.

---

## 🌐 Recommended: Koyeb (free Starter includes one Web Service)
- Create account at Koyeb, choose **Create Web Service → GitHub or Docker image**.
- Point to your repo or image, keep defaults.
- Expose port **8080** (platform honors `$PORT` automatically).
- Assign a subdomain (e.g., `lift.koyeb.app`) and deploy.
- Visit `https://your-subdomain/` for the UI.
- API available at `POST https://your-subdomain/generate-content`.

> Other options: Render free instances (may sleep after inactivity), Railway (free credits each month), Fly.io (pay-as-you-go).

---

## 🔒 Notes
- The API key is **hard-coded** per your request. Anyone with image access can read it. Prefer environment variables for long-term security.
- `MAX_CONTENT_LENGTH` is set to 10MB. Adjust in `app.py` if needed.
- `CORS` is permissive to keep things simple. If you split UI and API, lock it down to your origin.

---

## 🧪 Endpoints
- `GET /` — simple HTML UI
- `GET /healthz` — returns `{"status":"ok"}`
- `POST /generate-content` — form-data with fields:
  - `file` (optional, .txt)
  - `text_input` (optional)
  - `instructions` (optional)

**Response**:
```json
{ "generated_text": "..." }
```
