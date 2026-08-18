"""
NewsLens AI - Web App (Phase 4)

A minimal FastAPI app exposing the RAG pipeline through a browser UI.
Run with: uvicorn app:app --reload
Then open: http://127.0.0.1:8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler

from rag_pipeline import answer_question
from collector import collect_all

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run once on startup so the live app has fresh articles immediately
    try:
        collect_all()
    except Exception as e:
        print(f"[startup collect] failed: {e}")

    # Then keep refreshing every hour in the background
    scheduler.add_job(collect_all, "interval", hours=1, id="hourly_collect")
    scheduler.start()

    yield  # app runs here

    scheduler.shutdown()


app = FastAPI(title="NewsLens AI", lifespan=lifespan)


class QuestionRequest(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
def home():
    return INDEX_HTML


@app.post("/ask")
def ask(req: QuestionRequest):
    result = answer_question(req.question)
    return result


@app.post("/refresh")
def refresh():
    try:
        collect_all()
        return {"status": "ok", "message": "News refreshed successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>NewsLens AI</title>
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 800px;
    margin: 40px auto;
    padding: 0 20px;
    background: #0f1117;
    color: #e8e8e8;
  }
  h1 { font-size: 1.8em; margin-bottom: 4px; }
  .subtitle { color: #999; margin-bottom: 12px; }
  .top-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
  .refresh-btn {
    padding: 8px 16px;
    border-radius: 8px;
    border: 1px solid #444;
    background: #1a1d29;
    color: #ccc;
    font-size: 0.85em;
    cursor: pointer;
  }
  .refresh-btn:hover { background: #24283a; }
  .refresh-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .input-row { display: flex; gap: 8px; margin-bottom: 24px; }
  input[type=text] {
    flex: 1;
    padding: 12px 16px;
    border-radius: 8px;
    border: 1px solid #333;
    background: #1a1d29;
    color: #fff;
    font-size: 1em;
  }
  button {
    padding: 12px 24px;
    border-radius: 8px;
    border: none;
    background: #6c5ce7;
    color: white;
    font-size: 1em;
    cursor: pointer;
  }
  button:hover { background: #5a4bd1; }
  button:disabled { background: #444; cursor: not-allowed; }
  #answer {
    white-space: pre-wrap;
    line-height: 1.6;
    background: #1a1d29;
    padding: 20px;
    border-radius: 8px;
    display: none;
  }
  .sources { margin-top: 16px; font-size: 0.9em; color: #aaa; }
  .sources a { color: #8c7ae6; }
  .loading { color: #999; font-style: italic; }
  .examples { margin-bottom: 20px; font-size: 0.9em; color: #999; }
  .examples span {
    cursor: pointer;
    color: #8c7ae6;
    text-decoration: underline;
    margin-right: 12px;
  }
  #refreshStatus { font-size: 0.8em; color: #999; margin-left: 10px; }
</style>
</head>
<body>
  <div class="top-row">
    <div>
      <h1>📰 NewsLens AI</h1>
      <div class="subtitle">Multi-source news research assistant — source comparison, sentiment, contradictions</div>
    </div>
    <div>
      <button class="refresh-btn" id="refreshBtn" onclick="refreshNews()">🔄 Refresh News</button>
      <span id="refreshStatus"></span>
    </div>
  </div>

  <div class="examples">
    Try: <span onclick="ask('How are different sources reporting on India\\'s AI regulation?')">AI regulation</span>
    <span onclick="ask('What is being said about Nvidia earnings?')">Nvidia earnings</span>
  </div>

  <div class="input-row">
    <input type="text" id="question" placeholder="Ask about the news..." />
    <button id="askBtn" onclick="ask()">Ask</button>
  </div>

  <div id="answer"></div>

  <script>
    async function ask(presetQuestion) {
      const input = document.getElementById('question');
      const question = presetQuestion || input.value.trim();
      if (!question) return;
      input.value = question;

      const answerBox = document.getElementById('answer');
      const btn = document.getElementById('askBtn');
      btn.disabled = true;
      answerBox.style.display = 'block';
      answerBox.innerHTML = '<span class="loading">Retrieving articles and generating answer...</span>';

      try {
        const res = await fetch('/ask', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({question})
        });
        const data = await res.json();

        let sourcesHtml = '';
        if (data.sources && data.sources.length) {
          sourcesHtml = '<div class="sources"><strong>Sources:</strong><br>' +
            data.sources.map(s => `- ${s.source}: ${s.title}`).join('<br>') +
            '</div>';
        }

        answerBox.innerHTML = escapeHtml(data.answer) + sourcesHtml;
      } catch (err) {
        answerBox.innerHTML = 'Error: ' + err.message;
      } finally {
        btn.disabled = false;
      }
    }

    async function refreshNews() {
      const btn = document.getElementById('refreshBtn');
      const status = document.getElementById('refreshStatus');
      btn.disabled = true;
      status.textContent = 'Refreshing...';

      try {
        const res = await fetch('/refresh', { method: 'POST' });
        const data = await res.json();
        status.textContent = data.status === 'ok' ? 'Updated ✓' : 'Failed';
      } catch (err) {
        status.textContent = 'Failed';
      } finally {
        btn.disabled = false;
        setTimeout(() => { status.textContent = ''; }, 3000);
      }
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    document.getElementById('question').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') ask();
    });
  </script>
</body>
</html>
"""