import streamlit as st
from agents.github_agent import GitHubAnalyserAgent
from utils.github_client import GitHubClient
from utils.display import render_analysis

st.set_page_config(
    page_title="RepoLens — GitHub AI Analyser",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Security headers via meta tags (mitigates XSS, clickjacking, MIME sniffing)
st.markdown("""
<meta http-equiv="X-Content-Type-Options" content="nosniff">
<meta http-equiv="X-Frame-Options" content="SAMEORIGIN">
<meta http-equiv="Referrer-Policy" content="strict-origin-when-cross-origin">
<meta http-equiv="Permissions-Policy" content="camera=(), microphone=(), geolocation=()">
<meta name="Content-Security-Policy" content="default-src \'self\' fonts.googleapis.com fonts.gstatic.com; style-src \'self\' \'unsafe-inline\' fonts.googleapis.com; script-src \'self\' \'unsafe-inline\'">
""", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background: #FFFFFF !important; }
.main .block-container { padding: 1.5rem 2rem 4rem !important; max-width: 1200px !important; }
#MainMenu, footer, header { visibility: hidden !important; }

/* ── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E8ECF0 !important;
}
[data-testid="stSidebar"] .block-container { padding: 1.25rem 1.1rem !important; }
[data-testid="stSidebar"] label {
    font-size: 10px !important;
    font-weight: 600 !important;
    color: #8896A7 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}

/* ── Sidebar inputs ──────────────────────────────────────── */
[data-testid="stSidebar"] input {
    background: #F6F8FA !important;
    border: 1px solid #E2E8EF !important;
    border-radius: 8px !important;
    color: #1A202C !important;
    font-size: 13px !important;
    font-family: 'JetBrains Mono', monospace !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #F6F8FA !important;
    border: 1px solid #E2E8EF !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    color: #1A202C !important;
}

/* ── Multiselect: compact pill style ────────────────────── */
[data-baseweb="multi-select"] {
    background: #F6F8FA !important;
    border: 1px solid #E2E8EF !important;
    border-radius: 8px !important;
    gap: 4px !important;
    padding: 4px 6px !important;
    flex-wrap: wrap !important;
}
[data-baseweb="tag"] {
    background: #EEF3FB !important;
    border-radius: 20px !important;
    border: none !important;
    padding: 2px 8px !important;
    margin: 2px !important;
}
[data-baseweb="tag"] span { color: #4A7CDD !important; font-size: 11px !important; font-weight: 500 !important; }
[data-baseweb="tag"] [role="presentation"] { color: #9BB3E0 !important; }

/* ── URL input ───────────────────────────────────────────── */
.url-input input {
    background: #F6F8FA !important;
    border: 1px solid #E2E8EF !important;
    border-radius: 10px !important;
    color: #1A202C !important;
    font-size: 14px !important;
    height: 48px !important;
    padding-left: 44px !important;
}
.url-input input::placeholder { color: #A8B4C4 !important; }
.url-input input:focus { border-color: #4A7CDD !important; box-shadow: 0 0 0 3px rgba(74,124,221,0.1) !important; }

/* ── Analyse button ──────────────────────────────────────── */
.analyse-btn button {
    background: #1A202C !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    height: 48px !important;
    letter-spacing: 0.01em !important;
    font-family: 'Inter', sans-serif !important;
}
.analyse-btn button:hover { background: #2D3748 !important; }

/* ── Tabs ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    background: transparent !important;
    border-bottom: 1.5px solid #EEF1F5 !important;
    padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 0 !important;
    color: #8896A7 !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    padding: 0.6rem 1rem !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    font-family: 'Inter', sans-serif !important;
}
.stTabs [aria-selected="true"] {
    color: #4A7CDD !important;
    border-bottom: 2px solid #4A7CDD !important;
    background: transparent !important;
    font-weight: 500 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.25rem !important; }

/* ── Expanders ───────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #FFFFFF !important;
    border: 1px solid #E8ECF2 !important;
    border-radius: 10px !important;
    margin-bottom: 6px !important;
    box-shadow: none !important;
}
[data-testid="stExpander"] summary { color: #2D3748 !important; font-size: 13px !important; font-weight: 500 !important; }

/* ── Download button ─────────────────────────────────────── */
[data-testid="stDownloadButton"] button {
    background: #F6F8FA !important;
    border: 1px solid #E2E8EF !important;
    border-radius: 8px !important;
    color: #4A7CDD !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
[data-testid="stDownloadButton"] button:hover { background: #EEF3FB !important; }

/* ── Alerts ──────────────────────────────────────────────── */
[data-testid="stAlert"] { border-radius: 8px !important; font-size: 13px !important; }

/* ── Divider ─────────────────────────────────────────────── */
hr { border-color: #EEF1F5 !important; margin: 1.25rem 0 !important; }

/* ── Scrollbar ───────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #F6F8FA; }
::-webkit-scrollbar-thumb { background: #D1D9E6; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding-bottom:16px;
      border-bottom:1px solid #EEF1F5;margin-bottom:16px">
      <div style="width:32px;height:32px;border-radius:9px;background:#EEF3FB;
        display:flex;align-items:center;justify-content:center;font-size:16px">🔭</div>
      <div>
        <div style="font-size:14px;font-weight:600;color:#1A202C">RepoLens</div>
        <div style="font-size:11px;color:#A8B4C4;margin-top:1px">groq · llama 3.3</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    groq_api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    github_token = st.text_input("GitHub Token (optional)", type="password", placeholder="ghp_...")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    model_choice = st.selectbox("Model", [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ])

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    analysis_options = st.multiselect("Scope", [
        "📋 Repo Overview", "🏗️ Architecture", "📦 Dependencies",
        "🔒 Security", "📊 Code Quality", "🐛 Bug Detection",
        "📝 Documentation", "🚀 Improvement Suggestions",
    ], default=[
        "📋 Repo Overview", "🏗️ Architecture", "📦 Dependencies",
        "🔒 Security", "📊 Code Quality", "🚀 Improvement Suggestions",
    ])

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    max_files = st.slider("Files to read", 5, 40, 15)

    st.markdown("""
    <div style="margin-top:18px;padding-top:14px;border-top:1px solid #EEF1F5">
      <div style="font-size:10px;font-weight:600;color:#A8B4C4;text-transform:uppercase;
        letter-spacing:.07em;margin-bottom:10px">How it works</div>
      <div style="font-size:12px;color:#C5CDD8;line-height:2.1">
        <span style="color:#8896A7">①</span> Fetch repo metadata<br>
        <span style="color:#8896A7">②</span> Map file tree<br>
        <span style="color:#8896A7">③</span> Read key source files<br>
        <span style="color:#8896A7">④</span> Groq LLM synthesis<br>
        <span style="color:#8896A7">⑤</span> Structured report
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:20px 0 16px;border-bottom:1px solid #EEF1F5;margin-bottom:18px">
  <div style="display:inline-flex;align-items:center;gap:7px;background:#F0F5FF;
    border:1px solid #D6E4FF;border-radius:20px;padding:4px 12px;margin-bottom:14px">
    <div style="width:6px;height:6px;border-radius:50%;background:#4A7CDD"></div>
    <span style="font-size:11px;font-weight:500;color:#4A7CDD;letter-spacing:.04em">
      live · groq api · github api
    </span>
  </div>
  <div style="font-size:1.65rem;font-weight:600;color:#1A202C;margin:0 0 8px;
    letter-spacing:-0.4px;line-height:1.25">
    GitHub repo<br><span style="color:#4A7CDD">intelligence engine</span>
  </div>
  <div style="color:#8896A7;font-size:14px;max-width:500px;line-height:1.65">
    Paste any public repository URL. The agent reads your code, maps the architecture,
    flags security risks, and delivers a full AI-powered report in seconds.
  </div>
</div>
""", unsafe_allow_html=True)

# ── SEARCH BAR ────────────────────────────────────────────────────────────────
c_url, c_btn = st.columns([5, 1])
with c_url:
    st.markdown('<div class="url-input">', unsafe_allow_html=True)
    repo_url = st.text_input("url", label_visibility="collapsed",
                              placeholder="https://github.com/owner/repository")
    st.markdown('</div>', unsafe_allow_html=True)
with c_btn:
    st.markdown('<div class="analyse-btn">', unsafe_allow_html=True)
    go = st.button("Analyse →", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── RUN ───────────────────────────────────────────────────────────────────────
if go:
    if not repo_url:         st.error("Enter a GitHub repository URL."); st.stop()
    if not groq_api_key:     st.error("Add your Groq API key in the sidebar."); st.stop()
    if not analysis_options: st.error("Select at least one analysis type."); st.stop()

    try:
        parts = repo_url.rstrip("/").replace("https://github.com/", "").split("/")
        owner, repo_name = parts[0], parts[1]
    except Exception:
        st.error("Invalid URL — use: https://github.com/owner/repo"); st.stop()

    # Progress panel
    st.markdown("""
    <div style="background:#F6F8FA;border:1px solid #E8ECF2;border-radius:10px;
      padding:14px 18px;margin:14px 0 6px">
      <div style="font-size:10px;font-weight:600;color:#A8B4C4;letter-spacing:.08em;
        text-transform:uppercase;margin-bottom:10px">Agent pipeline</div>
    """, unsafe_allow_html=True)
    steps_ph = st.empty()
    st.markdown("</div>", unsafe_allow_html=True)

    log: list[str] = []
    def step(msg: str, status: str = "run") -> None:
        clr  = {"done": "#22C55E", "err": "#EF4444"}.get(status, "#4A7CDD")
        icon = {"done": "✓",       "err": "✗"      }.get(status, "●")
        log.append(
            f'<div style="display:flex;align-items:center;gap:10px;padding:5px 0;'
            f'border-bottom:1px solid #EEF1F5;font-size:12px;color:#2D3748">'
            f'<div style="width:3px;height:20px;border-radius:2px;background:{clr};flex-shrink:0"></div>'
            f'<span style="color:{clr};width:14px;text-align:center;flex-shrink:0;font-weight:600">{icon}</span>'
            f'<span>{msg}</span></div>'
        )
        steps_ph.markdown("".join(log), unsafe_allow_html=True)

    try:
        gh    = GitHubClient(token=github_token or None)
        agent = GitHubAnalyserAgent(groq_api_key=groq_api_key, model=model_choice,
                                    github_client=gh, max_files=max_files)

        step(f'Fetching metadata — <code style="background:#EEF3FB;color:#4A7CDD;padding:1px 5px;border-radius:4px;font-size:11px">{owner}/{repo_name}</code>')
        meta = gh.get_repo_metadata(owner, repo_name)
        step(f"Metadata — {meta.get('stargazers_count',0):,} ★  {meta.get('forks_count',0):,} forks  {meta.get('open_issues_count',0)} issues", "done")

        step("Mapping file tree")
        tree = gh.get_file_tree(owner, repo_name)
        step(f"File tree — {len(tree):,} entries", "done")

        step(f"Reading up to {max_files} key files")
        files = gh.get_key_files(owner, repo_name, tree, max_files)
        step(f"Read {len(files)} files", "done")

        step("Fetching language stats")
        langs = gh.get_languages(owner, repo_name)
        step(f"Languages: {', '.join(list(langs.keys())[:6])}", "done")

        step("Synthesising with Groq AI — 10–20 s")
        report = agent.analyse(repo_meta=meta, file_tree=tree, file_contents=files,
                               lang_stats=langs, analysis_options=analysis_options)
        step("Analysis complete", "done")

        steps_ph.empty()
        render_analysis(report, meta, langs)

    except Exception as exc:
        step(f"Error: {exc}", "err")
        st.error(f"Analysis failed: {exc}")
        st.info("Check your API keys and ensure the repo is public.")

# ── EMPTY STATE ───────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div style="text-align:center;padding:4rem 1rem 2rem">
      <div style="width:52px;height:52px;border-radius:14px;background:#EEF3FB;
        display:inline-flex;align-items:center;justify-content:center;
        font-size:24px;margin-bottom:16px">🔭</div>
      <div style="font-size:1rem;font-weight:600;color:#1A202C;margin-bottom:7px">
        Ready to analyse any repository
      </div>
      <div style="font-size:13px;color:#A8B4C4;max-width:340px;margin:0 auto;line-height:1.7">
        Enter a GitHub URL above and click
        <strong style="color:#4A7CDD">Analyse →</strong>.<br>
        Works on any public repo — no setup required.
      </div>
      <div style="display:flex;justify-content:center;gap:10px;margin-top:2.25rem;flex-wrap:wrap">
        <div style="background:#F6F8FA;border:1px solid #E8ECF2;border-radius:10px;
          padding:14px 16px;text-align:left;width:148px">
          <div style="width:7px;height:7px;border-radius:50%;background:#4A7CDD;margin-bottom:9px"></div>
          <div style="font-size:12px;font-weight:500;color:#2D3748;margin-bottom:3px">Architecture</div>
          <div style="font-size:11px;color:#A8B4C4;line-height:1.5">Patterns &amp; structure</div>
        </div>
        <div style="background:#F6F8FA;border:1px solid #E8ECF2;border-radius:10px;
          padding:14px 16px;text-align:left;width:148px">
          <div style="width:7px;height:7px;border-radius:50%;background:#EF4444;margin-bottom:9px"></div>
          <div style="font-size:12px;font-weight:500;color:#2D3748;margin-bottom:3px">Security</div>
          <div style="font-size:11px;color:#A8B4C4;line-height:1.5">Risks &amp; vulnerabilities</div>
        </div>
        <div style="background:#F6F8FA;border:1px solid #E8ECF2;border-radius:10px;
          padding:14px 16px;text-align:left;width:148px">
          <div style="width:7px;height:7px;border-radius:50%;background:#F59E0B;margin-bottom:9px"></div>
          <div style="font-size:12px;font-weight:500;color:#2D3748;margin-bottom:3px">Code quality</div>
          <div style="font-size:11px;color:#A8B4C4;line-height:1.5">Score &amp; observations</div>
        </div>
        <div style="background:#F6F8FA;border:1px solid #E8ECF2;border-radius:10px;
          padding:14px 16px;text-align:left;width:148px">
          <div style="width:7px;height:7px;border-radius:50%;background:#22C55E;margin-bottom:9px"></div>
          <div style="font-size:12px;font-weight:500;color:#2D3748;margin-bottom:3px">Improvements</div>
          <div style="font-size:11px;color:#A8B4C4;line-height:1.5">Actionable suggestions</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
