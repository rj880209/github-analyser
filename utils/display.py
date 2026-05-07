from __future__ import annotations
import streamlit as st
import json

# ── Light palette ──────────────────────────────────────────────────────────────
BG      = "#FFFFFF"
SURFACE = "#F6F8FA"
BORDER  = "#E8ECF2"
T1      = "#1A202C"
T2      = "#4A5568"
T3      = "#8896A7"
T4      = "#C5CDD8"
ACCENT  = "#4A7CDD"
GREEN   = "#22C55E"
AMBER   = "#F59E0B"
RED     = "#EF4444"

SEV_FG = {"Critical": RED,   "High": "#F97316", "Medium": AMBER, "Low": GREEN}
PRI_FG = {"High": RED,       "Medium": AMBER,    "Low": GREEN}
RISK_C = {"Low": GREEN,      "Medium": AMBER,    "High": RED,    "Critical": RED}
LANG_C = [ACCENT, GREEN, AMBER, RED, "#8B5CF6", "#06B6D4", "#EC4899"]

def _sc(s):
    return GREEN if s >= 8 else (AMBER if s >= 6 else RED)

def _rgb(h):
    h = h.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"

def _pill(text, fg):
    return (f'<span style="background:rgba({_rgb(fg)},0.08);color:{fg};'
            f'border:1px solid rgba({_rgb(fg)},0.2);border-radius:20px;'
            f'padding:2px 10px;font-size:11px;font-weight:500">{text}</span>')

def _lbl(text):
    return (f'<div style="font-size:10px;font-weight:600;color:{T4};text-transform:uppercase;'
            f'letter-spacing:.07em;margin:16px 0 8px">{text}</div>')

def _bar(pct, clr):
    return (f'<div style="background:#EEF1F5;border-radius:3px;height:4px;margin:3px 0 10px">'
            f'<div style="background:{clr};width:{pct}%;height:4px;border-radius:3px"></div></div>')

def _box(html, accent=None):
    left = f"border-left:3px solid {accent};" if accent else ""
    return (f'<div style="background:{SURFACE};border:1px solid {BORDER};{left}'
            f'border-radius:8px;padding:11px 14px;margin-bottom:7px;font-size:13px;'
            f'color:{T2};line-height:1.65">{html}</div>')

def _stat_card(col, val, lbl, clr=T1):
    col.markdown(
        f'<div style="background:{SURFACE};border:1px solid {BORDER};border-radius:10px;'
        f'padding:14px 12px;text-align:center">'
        f'<div style="font-size:18px;font-weight:600;color:{clr}">{val}</div>'
        f'<div style="font-size:10px;color:{T4};margin-top:4px;text-transform:uppercase;'
        f'letter-spacing:.06em;font-weight:500">{lbl}</div></div>',
        unsafe_allow_html=True)


def render_analysis(report: dict, repo_meta: dict, lang_stats: dict) -> None:
    if report.get("parse_error"):
        st.warning("AI returned an unstructured response.")
        st.code(report.get("raw_response", ""), language="text")
        return

    overall = report.get("overall_score", 0)
    cq   = report.get("code_quality", {})
    doc  = report.get("documentation", {})
    sec  = report.get("security", {})
    risk = sec.get("risk_level", "Unknown")

    # ── Verdict ───────────────────────────────────────────────────────────────
    verdict = report.get("verdict", "")
    if verdict:
        st.markdown(
            f'<div style="background:{SURFACE};border:1px solid {BORDER};'
            f'border-left:3px solid {ACCENT};border-radius:8px;'
            f'padding:11px 16px;margin:14px 0 16px;font-size:13px;'
            f'color:{T2};line-height:1.65;font-style:italic">'
            f'💬 &nbsp;{verdict}</div>',
            unsafe_allow_html=True)

    # ── Score strip ───────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    _stat_card(c1, f"{overall}/10",               "Overall",      _sc(overall))
    _stat_card(c2, f"{cq.get('score','?')}/10",   "Code quality", _sc(cq.get('score', 0)))
    _stat_card(c3, f"{doc.get('score','?')}/10",  "Docs",         _sc(doc.get('score', 0)))
    _stat_card(c4, risk,                           "Security",     RISK_C.get(risk, T3))
    _stat_card(c5, f"{repo_meta.get('stargazers_count',0):,} ★", "Stars", ACCENT)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tabs = st.tabs(["Overview", "Architecture", "Quality", "Security",
                    "Dependencies", "Bugs", "Improvements"])
    tab_ov, tab_arch, tab_qual, tab_sec, tab_dep, tab_bug, tab_imp = tabs

    # ── OVERVIEW ──────────────────────────────────────────────────────────────
    with tab_ov:
        col_l, col_r = st.columns([3, 2])
        with col_l:
            st.markdown(_lbl("Summary"), unsafe_allow_html=True)
            st.markdown(_box(report.get("summary", "—")), unsafe_allow_html=True)

            st.markdown(_lbl("Purpose"), unsafe_allow_html=True)
            st.markdown(_box(report.get("purpose", "—")), unsafe_allow_html=True)

            st.markdown(_lbl("Tech stack"), unsafe_allow_html=True)
            pills = " ".join(
                f'<span style="font-family:JetBrains Mono,monospace;font-size:11px;'
                f'background:{SURFACE};border:1px solid {BORDER};border-radius:6px;'
                f'padding:3px 9px;color:{T2}">{t}</span>'
                for t in report.get("tech_stack", []))
            st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:5px">{pills}</div>',
                        unsafe_allow_html=True)

        with col_r:
            st.markdown(_lbl("Languages"), unsafe_allow_html=True)
            total = sum(lang_stats.values()) or 1
            for i, (lang, b) in enumerate(sorted(lang_stats.items(), key=lambda x: -x[1])[:7]):
                pct = round(b / total * 100)
                clr = LANG_C[i % len(LANG_C)]
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:2px">'
                    f'<span style="color:{T1};font-weight:500">{lang}</span>'
                    f'<span style="color:{T4};font-family:JetBrains Mono,monospace">{pct}%</span></div>'
                    + _bar(pct, clr), unsafe_allow_html=True)

            st.markdown(_lbl("Documentation"), unsafe_allow_html=True)
            for label, key in [("README", "has_readme"),
                                ("Contributing guide", "has_contributing"),
                                ("Changelog", "has_changelog")]:
                has = doc.get(key, False)
                clr = GREEN if has else RED
                txt = "present" if has else "missing"
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:9px;padding:6px 0;'
                    f'border-bottom:1px solid #EEF1F5;font-size:12px">'
                    f'<div style="width:6px;height:6px;border-radius:50%;background:{clr};flex-shrink:0"></div>'
                    f'<span style="flex:1;color:{T1 if has else T3}">{label}</span>'
                    f'<span style="font-size:11px;color:{clr};font-weight:500">{txt}</span></div>',
                    unsafe_allow_html=True)

    # ── ARCHITECTURE ──────────────────────────────────────────────────────────
    with tab_arch:
        arch = report.get("architecture", {})
        if arch:
            st.markdown(
                f'<div style="background:{SURFACE};border:1px solid {BORDER};border-radius:10px;'
                f'padding:16px 18px;margin-bottom:14px">'
                f'<div style="font-size:10px;font-weight:600;color:{T4};text-transform:uppercase;'
                f'letter-spacing:.07em;margin-bottom:6px">Pattern detected</div>'
                f'<div style="font-size:16px;font-weight:600;color:{ACCENT};margin-bottom:8px">'
                f'{arch.get("pattern","Unknown")}</div>'
                f'<div style="font-size:13px;color:{T2};line-height:1.65">'
                f'{arch.get("description","")}</div></div>',
                unsafe_allow_html=True)
            c_s, c_c = st.columns(2)
            with c_s:
                st.markdown(_lbl("Strengths"), unsafe_allow_html=True)
                for s in arch.get("strengths", []):
                    st.markdown(_box(s, accent=GREEN), unsafe_allow_html=True)
            with c_c:
                st.markdown(_lbl("Concerns"), unsafe_allow_html=True)
                for c in arch.get("concerns", []):
                    st.markdown(_box(c, accent=AMBER), unsafe_allow_html=True)
        else:
            st.info("Architecture data not available.")

    # ── QUALITY ───────────────────────────────────────────────────────────────
    with tab_qual:
        score = cq.get("score", 0)
        clr   = _sc(score)
        ql, qr = st.columns([1, 2])
        with ql:
            st.markdown(
                f'<div style="background:{SURFACE};border:1px solid {BORDER};border-radius:10px;'
                f'padding:24px 14px;text-align:center">'
                f'<div style="font-size:3rem;font-weight:700;color:{clr};line-height:1">{score}'
                f'<span style="font-size:1.1rem;color:{T4}">/10</span></div>'
                f'<div style="margin-top:12px">{_pill(cq.get("rating",""), clr)}</div></div>',
                unsafe_allow_html=True)
        with qr:
            st.markdown(_lbl("Observations"), unsafe_allow_html=True)
            for obs in cq.get("observations", []):
                st.markdown(_box(obs, accent=clr), unsafe_allow_html=True)

    # ── SECURITY ──────────────────────────────────────────────────────────────
    with tab_sec:
        dot      = RISK_C.get(risk, T3)
        findings = sec.get("findings", [])
        st.markdown(
            f'<div style="background:{SURFACE};border:1px solid {BORDER};border-radius:10px;'
            f'padding:16px 20px;margin-bottom:16px;display:flex;align-items:center;gap:14px">'
            f'<div style="width:10px;height:10px;border-radius:50%;background:{dot};flex-shrink:0"></div>'
            f'<div>'
            f'<div style="font-size:16px;font-weight:600;color:{dot}">{risk} risk</div>'
            f'<div style="font-size:12px;color:{T4};margin-top:2px">'
            f'{len(findings)} finding{"s" if len(findings)!=1 else ""} detected</div>'
            f'</div></div>', unsafe_allow_html=True)
        if findings:
            for f in findings:
                sev = f.get("severity", "Low")
                fg  = SEV_FG.get(sev, T3)
                with st.expander(f.get("issue", "Finding")):
                    st.markdown(_pill(sev, fg), unsafe_allow_html=True)
                    if f.get("location"):
                        st.markdown(
                            f'<code style="font-size:11px;background:{SURFACE};color:{T3};'
                            f'padding:2px 6px;border-radius:4px">{f["location"]}</code>',
                            unsafe_allow_html=True)
                    if f.get("recommendation"):
                        st.markdown(_box(f'<strong style="color:{ACCENT}">Fix:</strong> {f["recommendation"]}', accent=ACCENT), unsafe_allow_html=True)
        else:
            st.success("No significant security findings detected.")

    # ── DEPENDENCIES ──────────────────────────────────────────────────────────
    with tab_dep:
        deps = report.get("dependencies", {})
        dl, dr = st.columns([1, 2])
        with dl:
            st.markdown(
                f'<div style="background:{SURFACE};border:1px solid {BORDER};border-radius:10px;'
                f'padding:20px;text-align:center">'
                f'<div style="font-size:2.8rem;font-weight:700;color:{ACCENT}">{deps.get("total_count","?")}</div>'
                f'<div style="font-size:10px;color:{T4};text-transform:uppercase;letter-spacing:.07em;'
                f'font-weight:600;margin-top:5px">total deps</div></div>',
                unsafe_allow_html=True)
            if deps.get("notes"):
                st.markdown(_box(deps["notes"], accent=ACCENT), unsafe_allow_html=True)
        with dr:
            if deps.get("notable"):
                st.markdown(_lbl("Notable packages"), unsafe_allow_html=True)
                nc1, nc2 = st.columns(2)
                for i, d in enumerate(deps["notable"]):
                    (nc1 if i % 2 == 0 else nc2).markdown(
                        f'<div style="font-family:JetBrains Mono,monospace;font-size:11px;'
                        f'background:{SURFACE};border:1px solid {BORDER};border-radius:6px;'
                        f'padding:5px 9px;margin-bottom:5px;color:{ACCENT}">{d}</div>',
                        unsafe_allow_html=True)
            if deps.get("outdated_or_risky"):
                st.markdown(_lbl("Outdated / risky"), unsafe_allow_html=True)
                for r in deps["outdated_or_risky"]:
                    st.markdown(_box(r, accent=AMBER), unsafe_allow_html=True)

    # ── BUGS ──────────────────────────────────────────────────────────────────
    with tab_bug:
        bugs = report.get("bugs_and_issues", [])
        if bugs:
            st.markdown(_lbl(f"{len(bugs)} issue(s) detected"), unsafe_allow_html=True)
            for bug in bugs:
                sev = bug.get("severity", "Low")
                fg  = SEV_FG.get(sev, T3)
                with st.expander(bug.get("description", "Issue")[:90]):
                    st.markdown(_pill(sev, fg), unsafe_allow_html=True)
                    if bug.get("location"):
                        st.code(bug["location"], language="text")
                    if bug.get("fix"):
                        st.markdown(_box(f'<strong style="color:{GREEN}">Fix:</strong> {bug["fix"]}', accent=GREEN), unsafe_allow_html=True)
        else:
            st.success("No bugs or issues flagged by the agent.")

    # ── IMPROVEMENTS ──────────────────────────────────────────────────────────
    with tab_imp:
        improvements = report.get("improvements", [])
        if improvements:
            SORT = {"High": 0, "Medium": 1, "Low": 2}
            for imp in sorted(improvements, key=lambda x: SORT.get(x.get("priority", "Low"), 3)):
                pri    = imp.get("priority", "Low")
                effort = imp.get("effort", "?")
                pfg    = PRI_FG.get(pri, T3)
                efg    = {"Low": GREEN, "Medium": AMBER, "High": RED}.get(effort, T3)
                st.markdown(
                    f'<div style="background:{SURFACE};border:1px solid {BORDER};border-radius:10px;'
                    f'padding:13px 16px;margin-bottom:8px">'
                    f'<div style="display:flex;justify-content:space-between;align-items:flex-start;'
                    f'gap:10px;margin-bottom:7px">'
                    f'<div style="font-size:13px;font-weight:500;color:{T1}">{imp.get("title","")}</div>'
                    f'<div style="display:flex;gap:5px;flex-shrink:0">'
                    f'{_pill(pri, pfg)} {_pill(effort, efg)}</div></div>'
                    f'<div style="font-size:12px;color:{T3};line-height:1.65">'
                    f'{imp.get("description","")}</div></div>',
                    unsafe_allow_html=True)
        else:
            st.info("No improvement suggestions generated.")

    # ── DOWNLOAD ──────────────────────────────────────────────────────────────
    st.markdown("---")
    col_dl, _ = st.columns([1, 3])
    with col_dl:
        st.download_button(
            "⬇  Download report (JSON)",
            data=json.dumps(report, indent=2),
            file_name=f"{repo_meta.get('name', 'repo')}_analysis.json",
            mime="application/json",
            use_container_width=True,
        )
