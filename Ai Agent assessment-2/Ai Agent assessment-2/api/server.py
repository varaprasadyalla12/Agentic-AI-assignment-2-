"""
FastAPI Application Server for Applied Agentic AI Assignment 2.
Provides REST API endpoints and serves the interactive web dashboard.
"""

import os
import sys
import shutil
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.doc_qa import DocQAAgent
from agents.researcher import ResearchAgent
from agents.security_analyst import SecurityAnalystAgent
from agents.multi_agent import MultiAgentOrchestrator

app = FastAPI(
    title="Applied Agentic AI - Multi-Agent Suite",
    description="Interactive API and Web Dashboard for Assignment 2",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Project base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# Shared in-memory instances for server session
doc_agent = DocQAAgent()
research_agent = ResearchAgent()
security_agent = SecurityAnalystAgent()
multi_agent_orchestrator = MultiAgentOrchestrator()

# Initialize default document
default_pdf = os.path.join(DATA_DIR, "sample_docs", "agentic_ai_overview.pdf")
if os.path.exists(default_pdf):
    try:
        doc_agent.load_document(default_pdf)
    except Exception as e:
        print(f"Warning: Could not pre-index default PDF: {e}")


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------
class DocQAQueryRequest(BaseModel):
    query: str
    top_k: int = 3


class ResearchRequest(BaseModel):
    topic: str
    sources: int = 4


class SecurityTextRequest(BaseModel):
    log_text: str
    log_type: Optional[str] = "Pasted_Log.log"


class MultiAgentRequest(BaseModel):
    task: str


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "agents": ["DocQAAgent", "ResearchAgent", "SecurityAnalystAgent", "MultiAgentOrchestrator"],
        "indexed_documents": doc_agent.indexed_files,
    }


# --- Question 1: Doc QA ---
@app.post("/api/doc-qa/upload")
async def upload_document(file: UploadFile = File(...)):
    target_path = os.path.join(UPLOADS_DIR, file.filename)
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        num_chunks = doc_agent.load_document(target_path)
        return {
            "success": True,
            "filename": file.filename,
            "chunks_indexed": num_chunks,
            "total_documents": len(doc_agent.indexed_files),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@app.post("/api/doc-qa/ask")
async def ask_doc_qa(request: DocQAQueryRequest):
    if not doc_agent.indexed_files and not doc_agent.retriever.chunks:
        # Try loading default sample PDF if nothing indexed
        if os.path.exists(default_pdf):
            doc_agent.load_document(default_pdf)
        else:
            raise HTTPException(status_code=400, detail="No documents indexed. Please upload a PDF first.")

    result = doc_agent.ask(query=request.query, top_k=request.top_k)
    return result.model_dump()


# --- Question 2: Autonomous Research ---
@app.post("/api/research/run")
async def run_research(request: ResearchRequest):
    result = research_agent.research(topic=request.topic, max_sources=request.sources)
    return result.model_dump()


# --- Question 3: Security Log Analysis ---
@app.post("/api/security/analyze")
async def analyze_security_logs(request: SecurityTextRequest):
    result = security_agent.analyze_text(request.log_text, label=request.log_type)
    return result.model_dump()


@app.get("/api/security/sample/{sample_name}")
async def get_sample_log(sample_name: str):
    mapping = {
        "ssh": "data/sample_logs/ssh_bruteforce.log",
        "web": "data/sample_logs/web_sqli_attack.log",
        "cloudtrail": "data/sample_logs/cloudtrail_suspicious.json",
    }
    rel_path = mapping.get(sample_name)
    if not rel_path:
        raise HTTPException(status_code=404, detail="Sample not found")
    full_path = os.path.join(BASE_DIR, rel_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Log file missing on disk")

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {"name": sample_name, "path": rel_path, "content": content}


# --- Question 4: Collaborative Multi-Agent ---
@app.post("/api/multi-agent/collaborate")
async def run_collaboration(request: MultiAgentRequest):
    result = multi_agent_orchestrator.run_collaborative_task(request.task)
    return result.model_dump()


# --- Outputs Explorer ---
@app.get("/api/outputs")
async def list_outputs():
    files = []
    if os.path.exists(OUTPUTS_DIR):
        for f in os.listdir(OUTPUTS_DIR):
            fpath = os.path.join(OUTPUTS_DIR, f)
            if os.path.isfile(fpath):
                files.append({
                    "name": f,
                    "size": os.path.getsize(fpath),
                    "modified": os.path.getmtime(fpath),
                    "is_markdown": f.endswith(".md"),
                    "is_html": f.endswith(".html"),
                    "is_json": f.endswith(".json"),
                })
    return {"outputs": files}


@app.get("/api/outputs/file/{filename}")
async def get_output_file(filename: str):
    safe_filename = os.path.basename(filename)
    full_path = os.path.join(OUTPUTS_DIR, safe_filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {"filename": safe_filename, "content": content}


# ---------------------------------------------------------------------------
# Dashboard Frontend (Modern Glassmorphic SPA)
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Applied Agentic AI - Multi-Agent Suite</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-primary: #0a0e17;
      --bg-secondary: #121826;
      --bg-card: rgba(18, 24, 38, 0.7);
      --bg-card-hover: rgba(26, 35, 54, 0.85);
      --border: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(99, 102, 241, 0.3);
      --text-primary: #f1f5f9;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --primary: #6366f1;
      --primary-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
      --accent-cyan: #06b6d4;
      --accent-emerald: #10b981;
      --accent-rose: #f43f5e;
      --accent-amber: #f59e0b;
      --shadow-sm: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
      --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
    }

    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg-primary);
      color: var(--text-primary);
      min-height: 100vh;
      line-height: 1.6;
      background-image: 
        radial-gradient(circle at 15% 15%, rgba(99, 102, 241, 0.12) 0%, transparent 40%),
        radial-gradient(circle at 85% 85%, rgba(236, 72, 153, 0.1) 0%, transparent 40%);
      background-attachment: fixed;
    }

    header {
      border-bottom: 1px solid var(--border);
      backdrop-filter: blur(12px);
      background: rgba(10, 14, 23, 0.75);
      position: sticky;
      top: 0;
      z-index: 50;
    }

    .header-container {
      max-width: 1400px;
      margin: 0 auto;
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .logo-badge {
      width: 40px;
      height: 40px;
      border-radius: var(--radius-sm);
      background: var(--primary-gradient);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1.25rem;
      color: #fff;
      box-shadow: 0 0 15px rgba(99, 102, 241, 0.5);
    }

    .brand h1 {
      font-size: 1.35rem;
      font-weight: 700;
      background: linear-gradient(135deg, #fff 60%, #94a3b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .brand span {
      font-size: 0.8rem;
      color: var(--accent-cyan);
      background: rgba(6, 182, 212, 0.1);
      padding: 0.2rem 0.5rem;
      border-radius: 999px;
      border: 1px solid rgba(6, 182, 212, 0.2);
    }

    .nav-tabs {
      display: flex;
      gap: 0.5rem;
      background: rgba(18, 24, 38, 0.6);
      padding: 0.35rem;
      border-radius: var(--radius-md);
      border: 1px solid var(--border);
    }

    .tab-btn {
      padding: 0.55rem 1.1rem;
      border-radius: var(--radius-sm);
      border: none;
      background: transparent;
      color: var(--text-secondary);
      font-size: 0.875rem;
      font-weight: 500;
      font-family: inherit;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .tab-btn:hover {
      color: var(--text-primary);
      background: rgba(255, 255, 255, 0.05);
    }

    .tab-btn.active {
      background: var(--primary-gradient);
      color: #fff;
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
    }

    main {
      max-width: 1400px;
      margin: 2rem auto;
      padding: 0 2rem;
    }

    .tab-content {
      display: none;
    }

    .tab-content.active {
      display: block;
      animation: fadeIn 0.3s ease-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }

    @media (max-width: 960px) {
      .grid-2 { grid-template-columns: 1fr; }
      .header-container { flex-direction: column; gap: 1rem; }
    }

    .card {
      background: var(--bg-card);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 1.75rem;
      box-shadow: var(--shadow-sm);
      transition: border-color 0.2s ease;
    }

    .card:hover {
      border-color: var(--border-accent);
    }

    .card-title {
      font-size: 1.25rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }

    .card-subtitle {
      font-size: 0.875rem;
      color: var(--text-secondary);
      margin-bottom: 1.5rem;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 0.25rem 0.6rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .badge-primary { background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); }
    .badge-critical { background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }
    .badge-success { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }

    .form-group {
      margin-bottom: 1.25rem;
    }

    label {
      display: block;
      font-size: 0.875rem;
      font-weight: 500;
      color: var(--text-secondary);
      margin-bottom: 0.5rem;
    }

    input[type="text"], textarea, select {
      width: 100%;
      padding: 0.75rem 1rem;
      background: rgba(10, 14, 23, 0.6);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      color: var(--text-primary);
      font-family: inherit;
      font-size: 0.9rem;
      outline: none;
      transition: all 0.2s ease;
    }

    textarea {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      resize: vertical;
      min-height: 140px;
    }

    input[type="text"]:focus, textarea:focus, select:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }

    .btn-primary {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      padding: 0.75rem 1.5rem;
      background: var(--primary-gradient);
      color: #fff;
      border: none;
      border-radius: var(--radius-sm);
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
      transition: all 0.2s ease;
      width: 100%;
    }

    .btn-primary:hover {
      opacity: 0.95;
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
    }

    .btn-secondary {
      padding: 0.45rem 0.85rem;
      background: rgba(255, 255, 255, 0.06);
      color: var(--text-secondary);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.12);
      color: var(--text-primary);
    }

    .output-panel {
      background: rgba(10, 14, 23, 0.85);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 1.25rem;
      max-height: 520px;
      overflow-y: auto;
      font-size: 0.875rem;
      white-space: pre-wrap;
      font-family: 'JetBrains Mono', monospace;
      color: #e2e8f0;
    }

    .step-list {
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
      margin-top: 1rem;
    }

    .step-item {
      background: rgba(255, 255, 255, 0.03);
      border-left: 3px solid var(--primary);
      padding: 0.6rem 0.9rem;
      border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
      font-size: 0.825rem;
    }

    .step-item strong {
      color: var(--accent-cyan);
    }

    .dialogue-box {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      margin-top: 1rem;
    }

    .dialogue-msg {
      padding: 0.85rem 1.1rem;
      border-radius: var(--radius-sm);
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border);
    }

    .dialogue-header {
      display: flex;
      justify-content: space-between;
      font-size: 0.775rem;
      margin-bottom: 0.35rem;
      color: var(--accent-cyan);
      font-weight: 600;
    }

    .citation-tag {
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      background: rgba(6, 182, 212, 0.12);
      border: 1px solid rgba(6, 182, 212, 0.3);
      color: #22d3ee;
      font-size: 0.75rem;
      margin: 0.2rem 0.2rem 0.2rem 0;
      font-family: 'JetBrains Mono', monospace;
    }

    .loader {
      display: none;
      width: 20px;
      height: 20px;
      border: 2px solid rgba(255,255,255,0.2);
      border-top-color: #fff;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  </style>
</head>
<body>

  <header>
    <div class="header-container">
      <div class="brand">
        <div class="logo-badge">AI</div>
        <div>
          <h1>Applied Agentic AI <span>Assignment 2</span></h1>
        </div>
      </div>
      <nav class="nav-tabs">
        <button class="tab-btn active" onclick="switchTab('tab-q1', this)">
          📄 Q1: Doc QA
        </button>
        <button class="tab-btn" onclick="switchTab('tab-q2', this)">
          🌐 Q2: Research
        </button>
        <button class="tab-btn" onclick="switchTab('tab-q3', this)">
          🛡️ Q3: Security
        </button>
        <button class="tab-btn" onclick="switchTab('tab-q4', this)">
          🤖 Q4: Multi-Agent
        </button>
        <button class="tab-btn" onclick="switchTab('tab-outputs', this)">
          📁 Outputs Explorer
        </button>
      </nav>
    </div>
  </header>

  <main>
    <!-- ==================== TAB 1: DOC QA ==================== -->
    <div id="tab-q1" class="tab-content active">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">
            <span>📄</span> Document / PDF Question Answering
            <span class="badge badge-primary">Question 1</span>
          </div>
          <div class="card-subtitle">
            Ingests PDFs and documents, retrieves relevant passages via hybrid search, and synthesizes answers with strict page citations.
          </div>

          <div class="form-group">
            <label>Upload Custom PDF or Document</label>
            <input type="file" id="q1-file" accept=".pdf,.txt,.md" style="margin-bottom: 0.5rem;">
            <button class="btn-secondary" onclick="uploadDoc()">Upload & Index File</button>
            <span id="q1-upload-status" style="font-size: 0.8rem; margin-left: 0.5rem; color: var(--accent-emerald);"></span>
          </div>

          <div class="form-group">
            <label>Active Indexed Document</label>
            <input type="text" id="q1-doc-name" value="data/sample_docs/agentic_ai_overview.pdf" readonly style="opacity: 0.8;">
          </div>

          <div class="form-group">
            <label>User Query</label>
            <input type="text" id="q1-query" value="What are the core pillars of agentic architecture?">
          </div>

          <div class="form-group" style="display: flex; gap: 0.5rem; align-items: center;">
            <label style="margin: 0;">Top-K Passages:</label>
            <select id="q1-topk" style="width: 80px;">
              <option value="2">2</option>
              <option value="3" selected>3</option>
              <option value="5">5</option>
            </select>
          </div>

          <button class="btn-primary" id="q1-submit-btn" onclick="runDocQA()">
            <span>Execute Grounded QA</span>
            <div class="loader" id="q1-loader"></div>
          </button>
        </div>

        <div class="card">
          <div class="card-title">
            <span>💡</span> Grounded Agent Response & Provenance
          </div>
          <div id="q1-citations" style="margin-bottom: 0.75rem;"></div>
          <div class="output-panel" id="q1-output">Awaiting execution... Click 'Execute Grounded QA' to start.</div>
          <div class="step-list" id="q1-steps"></div>
        </div>
      </div>
    </div>

    <!-- ==================== TAB 2: RESEARCH ==================== -->
    <div id="tab-q2" class="tab-content">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">
            <span>🌐</span> Autonomous Research & Report Agent
            <span class="badge badge-primary">Question 2</span>
          </div>
          <div class="card-subtitle">
            Formulates multi-source web queries, extracts verified facts, and compiles an executive research report with formal references.
          </div>

          <div class="form-group">
            <label>Research Topic / Domain</label>
            <input type="text" id="q2-topic" value="Emerging Trends in Agentic AI and Autonomous Systems">
          </div>

          <div class="form-group">
            <label>Max Authoritative Sources</label>
            <select id="q2-sources">
              <option value="3">3 Sources</option>
              <option value="4" selected>4 Sources</option>
              <option value="6">6 Sources</option>
            </select>
          </div>

          <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem;">
            <button class="btn-secondary" onclick="setQ2Topic('Agentic AI in Enterprise Cybersecurity')">Cybersecurity</button>
            <button class="btn-secondary" onclick="setQ2Topic('Multi-Agent Coordination & Game Theoretic Consensus')">Multi-Agent</button>
            <button class="btn-secondary" onclick="setQ2Topic('Autonomous LLM Tool Use Benchmarks')">Tool Benchmarks</button>
          </div>

          <button class="btn-primary" id="q2-submit-btn" onclick="runResearch()">
            <span>Conduct Autonomous Research</span>
            <div class="loader" id="q2-loader"></div>
          </button>
        </div>

        <div class="card">
          <div class="card-title">
            <span>📊</span> Structured Research Deliverable & References
          </div>
          <div class="output-panel" id="q2-output">Awaiting research prompt... Click 'Conduct Autonomous Research'.</div>
          <div class="step-list" id="q2-steps"></div>
        </div>
      </div>
    </div>

    <!-- ==================== TAB 3: SECURITY ==================== -->
    <div id="tab-q3" class="tab-content">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">
            <span>🛡️</span> Security Log & Threat Intelligence Agent
            <span class="badge badge-critical">Question 3</span>
          </div>
          <div class="card-subtitle">
            Parses heterogeneous security logs, correlates MITRE ATT&CK techniques, classifies threat severity, and formulates containment playbooks.
          </div>

          <div class="form-group">
            <label>Load Sample Security Scenario</label>
            <div style="display: flex; gap: 0.5rem; margin-bottom: 0.75rem;">
              <button class="btn-secondary" onclick="loadSampleLog('ssh')">SSH Brute-Force (auth.log)</button>
              <button class="btn-secondary" onclick="loadSampleLog('web')">Web SQL Injection</button>
              <button class="btn-secondary" onclick="loadSampleLog('cloudtrail')">CloudTrail IAM Escalation</button>
            </div>
          </div>

          <div class="form-group">
            <label>Security Log Stream / Alerts (Raw Text or Pasted)</label>
            <textarea id="q3-log-text" placeholder="Paste security log events here..."></textarea>
          </div>

          <button class="btn-primary" id="q3-submit-btn" onclick="runSecurityAnalysis()">
            <span>Analyze Security Logs</span>
            <div class="loader" id="q3-loader"></div>
          </button>
        </div>

        <div class="card">
          <div class="card-title">
            <span>🚨</span> Incident Assessment & Containment Script
            <span id="q3-sev-badge" class="badge badge-critical" style="display: none; margin-left: auto;">CRITICAL</span>
          </div>
          <div class="output-panel" id="q3-output">Awaiting log stream... Click 'Analyze Security Logs' to inspect.</div>
          <div class="step-list" id="q3-steps"></div>
        </div>
      </div>
    </div>

    <!-- ==================== TAB 4: MULTI-AGENT ==================== -->
    <div id="tab-q4" class="tab-content">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">
            <span>🤖</span> Collaborative Multi-Agent System
            <span class="badge badge-primary">Question 4</span>
          </div>
          <div class="card-subtitle">
            Three specialized autonomous agents (Research, Analyst, Report) collaborate sequentially over a shared blackboard bus to solve high-level tasks.
          </div>

          <div class="form-group">
            <label>Collaborative Mission / Task</label>
            <input type="text" id="q4-task" value="Evaluate the Impact of Agentic AI on Enterprise Cloud Security">
          </div>

          <div style="display: flex; gap: 0.5rem; margin-bottom: 1.25rem;">
            <button class="btn-secondary" onclick="setQ4Task('Autonomous Agent Governance and Safety in Production')">Governance</button>
            <button class="btn-secondary" onclick="setQ4Task('Cost vs Accuracy Trade-offs in Multi-Agent Workflows')">Cost vs Accuracy</button>
          </div>

          <button class="btn-primary" id="q4-submit-btn" onclick="runCollaboration()">
            <span>Launch Multi-Agent Task Force</span>
            <div class="loader" id="q4-loader"></div>
          </button>

          <div style="margin-top: 1.5rem;">
            <label>Shared Blackboard Inter-Agent Dialogue Stream</label>
            <div class="dialogue-box" id="q4-dialogue">
              <div style="color: var(--text-muted); font-size: 0.85rem;">Dialogue will stream once launched.</div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-title">
            <span>📑</span> Final Executive Multi-Agent Deliverable
          </div>
          <div class="output-panel" id="q4-output">Awaiting collaboration launch...</div>
          <div class="step-list" id="q4-steps"></div>
        </div>
      </div>
    </div>

    <!-- ==================== TAB 5: OUTPUTS EXPLORER ==================== -->
    <div id="tab-outputs" class="tab-content">
      <div class="card">
        <div class="card-title" style="justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span>📁</span> Pre-Generated Outputs Explorer
          </div>
          <button class="btn-secondary" onclick="loadOutputsList()">Refresh File List</button>
        </div>
        <div class="card-subtitle">
          Directly inspect all rendered markdown, HTML reports, and JSON execution traces produced by the 4 agents.
        </div>

        <div style="display: grid; grid-template-columns: 320px 1fr; gap: 1.5rem; margin-top: 1rem;">
          <div style="background: rgba(10, 14, 23, 0.6); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 1rem; max-height: 520px; overflow-y: auto;" id="outputs-list">
            Loading outputs...
          </div>
          <div class="output-panel" id="output-file-viewer" style="max-height: 520px;">
            Select a file from the list on the left to preview its content.
          </div>
        </div>
      </div>
    </div>

  </main>

  <script>
    function switchTab(tabId, el) {
      document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      el.classList.add('active');
      if (tabId === 'tab-outputs') {
        loadOutputsList();
      }
    }

    function setQ2Topic(t) { document.getElementById('q2-topic').value = t; }
    function setQ4Task(t) { document.getElementById('q4-task').value = t; }

    async function uploadDoc() {
      const fileInput = document.getElementById('q1-file');
      if (!fileInput.files.length) {
        alert('Please select a file first.');
        return;
      }
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);

      const status = document.getElementById('q1-upload-status');
      status.innerText = 'Uploading & indexing...';
      try {
        const res = await fetch('/api/doc-qa/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.success) {
          status.innerText = `✓ Indexed ${data.chunks_indexed} chunks (${data.filename})`;
          document.getElementById('q1-doc-name').value = data.filename;
        } else {
          status.innerText = 'Upload failed.';
        }
      } catch (err) {
        status.innerText = 'Error uploading file.';
      }
    }

    async function runDocQA() {
      const query = document.getElementById('q1-query').value;
      const top_k = parseInt(document.getElementById('q1-topk').value);
      const loader = document.getElementById('q1-loader');
      const output = document.getElementById('q1-output');
      const citationsDiv = document.getElementById('q1-citations');
      const stepsDiv = document.getElementById('q1-steps');

      loader.style.display = 'inline-block';
      output.innerText = 'Retrieving passages and generating grounded answer...';
      citationsDiv.innerHTML = '';
      stepsDiv.innerHTML = '';

      try {
        const res = await fetch('/api/doc-qa/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, top_k }),
        });
        const data = await res.json();
        loader.style.display = 'none';

        if (data.success) {
          output.innerText = data.output;
          if (data.metadata && data.metadata.citations) {
            citationsDiv.innerHTML = data.metadata.citations
              .map(c => `<span class="citation-tag">${c}</span>`).join('');
          }
          if (data.steps) {
            stepsDiv.innerHTML = data.steps
              .map(s => `<div class="step-item"><strong>${s.action}</strong>: ${s.thoughts || ''}</div>`).join('');
          }
        } else {
          output.innerText = `Error: ${data.output || 'Query failed'}`;
        }
      } catch (err) {
        loader.style.display = 'none';
        output.innerText = `Network error: ${err.message}`;
      }
    }

    async function runResearch() {
      const topic = document.getElementById('q2-topic').value;
      const sources = parseInt(document.getElementById('q2-sources').value);
      const loader = document.getElementById('q2-loader');
      const output = document.getElementById('q2-output');
      const stepsDiv = document.getElementById('q2-steps');

      loader.style.display = 'inline-block';
      output.innerText = 'Searching authoritative sources and synthesizing findings...';
      stepsDiv.innerHTML = '';

      try {
        const res = await fetch('/api/research/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic, sources }),
        });
        const data = await res.json();
        loader.style.display = 'none';

        if (data.success) {
          output.innerText = data.output;
          if (data.steps) {
            stepsDiv.innerHTML = data.steps
              .map(s => `<div class="step-item"><strong>${s.action}</strong>: ${s.thoughts || ''}</div>`).join('');
          }
        } else {
          output.innerText = `Error: ${data.output}`;
        }
      } catch (err) {
        loader.style.display = 'none';
        output.innerText = `Network error: ${err.message}`;
      }
    }

    async function loadSampleLog(name) {
      try {
        const res = await fetch(`/api/security/sample/${name}`);
        const data = await res.json();
        document.getElementById('q3-log-text').value = data.content;
      } catch (err) {
        alert('Could not load sample log.');
      }
    }

    async function runSecurityAnalysis() {
      const log_text = document.getElementById('q3-log-text').value;
      if (!log_text.trim()) {
        alert('Please select or paste log events first.');
        return;
      }
      const loader = document.getElementById('q3-loader');
      const output = document.getElementById('q3-output');
      const badge = document.getElementById('q3-sev-badge');
      const stepsDiv = document.getElementById('q3-steps');

      loader.style.display = 'inline-block';
      output.innerText = 'Normalizing schema, matching MITRE ATT&CK rules, scoring severity...';
      stepsDiv.innerHTML = '';
      badge.style.display = 'none';

      try {
        const res = await fetch('/api/security/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ log_text, log_type: 'Incident_Stream.log' }),
        });
        const data = await res.json();
        loader.style.display = 'none';

        if (data.success) {
          output.innerText = data.output;
          if (data.metadata && data.metadata.peak_severity) {
            badge.innerText = data.metadata.peak_severity;
            badge.style.display = 'inline-flex';
          }
          if (data.steps) {
            stepsDiv.innerHTML = data.steps
              .map(s => `<div class="step-item"><strong>${s.action}</strong>: ${s.thoughts || ''}</div>`).join('');
          }
        } else {
          output.innerText = `Error: ${data.output}`;
        }
      } catch (err) {
        loader.style.display = 'none';
        output.innerText = `Network error: ${err.message}`;
      }
    }

    async function runCollaboration() {
      const task = document.getElementById('q4-task').value;
      const loader = document.getElementById('q4-loader');
      const output = document.getElementById('q4-output');
      const dialogueDiv = document.getElementById('q4-dialogue');
      const stepsDiv = document.getElementById('q4-steps');

      loader.style.display = 'inline-block';
      output.innerText = 'Coordinating 3 specialized agents over shared blackboard...';
      dialogueDiv.innerHTML = '<div style="color: var(--text-muted);">Coordinating task handoffs...</div>';
      stepsDiv.innerHTML = '';

      try {
        const res = await fetch('/api/multi-agent/collaborate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ task }),
        });
        const data = await res.json();
        loader.style.display = 'none';

        if (data.success) {
          output.innerText = data.output;
          if (data.metadata && data.metadata.dialogue) {
            dialogueDiv.innerHTML = data.metadata.dialogue.map(m => `
              <div class="dialogue-msg">
                <div class="dialogue-header">
                  <span>[${m.phase}] ${m.sender} ➔ ${m.recipient}</span>
                </div>
                <div style="font-size: 0.825rem;">${m.summary}</div>
              </div>
            `).join('');
          }
          if (data.steps) {
            stepsDiv.innerHTML = data.steps
              .map(s => `<div class="step-item"><strong>[${s.agent_name}] ${s.action}</strong>: ${s.thoughts || ''}</div>`).join('');
          }
        } else {
          output.innerText = `Error: ${data.output}`;
        }
      } catch (err) {
        loader.style.display = 'none';
        output.innerText = `Network error: ${err.message}`;
      }
    }

    async function loadOutputsList() {
      const listContainer = document.getElementById('outputs-list');
      listContainer.innerHTML = 'Loading outputs...';
      try {
        const res = await fetch('/api/outputs');
        const data = await res.json();
        if (data.outputs && data.outputs.length) {
          listContainer.innerHTML = data.outputs.map(f => `
            <div style="padding: 0.5rem 0.75rem; margin-bottom: 0.4rem; background: rgba(255,255,255,0.03); border-radius: 6px; cursor: pointer; display: flex; justify-content: space-between; align-items: center;" onclick="viewOutputFile('${f.name}')">
              <span style="font-size: 0.825rem; font-weight: 500;">${f.name}</span>
              <span style="font-size: 0.7rem; color: var(--text-muted);">${Math.round(f.size / 1024)} KB</span>
            </div>
          `).join('');
        } else {
          listContainer.innerHTML = 'No output files found.';
        }
      } catch (err) {
        listContainer.innerHTML = 'Error loading files.';
      }
    }

    async function viewOutputFile(filename) {
      const viewer = document.getElementById('output-file-viewer');
      viewer.innerText = `Loading ${filename}...`;
      try {
        const res = await fetch(`/api/outputs/file/${filename}`);
        const data = await res.json();
        viewer.innerText = data.content;
      } catch (err) {
        viewer.innerText = 'Failed to load file.';
      }
    }

    // Pre-load default sample into security tab on startup
    window.addEventListener('DOMContentLoaded', () => {
      loadSampleLog('ssh');
    });
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
