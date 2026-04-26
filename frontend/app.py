"""
Streamlit UI for `commec screen`.

Run with:
    uv run streamlit run frontend/app.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_DIR = REPO_ROOT / "commec-dbs"
EXAMPLE_FASTA = REPO_ROOT / "example_data" / "commec-examples.fasta"
LOGO_PATH = Path(__file__).parent / "assets" / "logo.svg"
LOGO_SVG = LOGO_PATH.read_text() if LOGO_PATH.exists() else ""

STATUS_COLORS = {
    "Pass":    ("#1f7a3a", "#dcfce7"),
    "Warning": ("#92400e", "#fef3c7"),
    "Flag":    ("#7f1d1d", "#fee2e2"),
    "Error":   ("#7f1d1d", "#fee2e2"),
    "Skip":    ("#475569", "#e2e8f0"),
    "Cleared": ("#1f7a3a", "#dcfce7"),
}

CSS = """
<style>
    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
    }
    .commec-hero {
        display: flex;
        align-items: center;
        gap: 1.4rem;
        padding: 1.6rem 2rem;
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, #0a2942 0%, #1d6fa5 60%, #2c8ec7 100%);
        color: white;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(15,58,95,0.22);
    }
    .commec-hero .logo { flex-shrink: 0; width: 92px; height: 108px; }
    .commec-hero .logo svg { width: 100%; height: 100%; display: block; }
    .commec-hero .copy { flex: 1; min-width: 0; }
    .commec-hero h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1;
    }
    .commec-hero .subtitle {
        margin: 0.25rem 0 0 0;
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #f6c24e;
    }
    .commec-hero p.tagline {
        margin: 0.7rem 0 0 0;
        opacity: 0.92;
        font-size: 0.97rem;
        line-height: 1.45;
        max-width: 720px;
    }
    .pill {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .query-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 1px 3px rgba(15,23,42,0.04);
    }
    .query-card h4 {
        margin: 0 0 0.4rem 0;
        font-size: 1rem;
        color: #0f172a;
        word-break: break-all;
    }
    .query-card .meta {
        color: #64748b;
        font-size: 0.82rem;
        margin-bottom: 0.6rem;
    }
    .query-card .rationale {
        margin-top: 0.6rem;
        color: #334155;
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .pill-row { display: flex; flex-wrap: wrap; gap: 0.4rem; }
    .step-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748b;
        margin-right: 0.3rem;
    }
    .running-banner {
        display: flex;
        align-items: center;
        gap: 0.9rem;
        padding: 1rem 1.25rem;
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(15,23,42,0.04);
    }
    .running-banner .label {
        font-weight: 600;
        color: #0f3a5f;
        font-size: 0.98rem;
    }
    .running-banner .sub {
        color: #64748b;
        font-size: 0.82rem;
        margin-top: 0.15rem;
    }
    .spinner-ring {
        width: 22px;
        height: 22px;
        border-radius: 50%;
        border: 3px solid #cbd5e1;
        border-top-color: #1d6fa5;
        animation: spin 0.9s linear infinite;
        flex-shrink: 0;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .progress-bar {
        height: 4px;
        background: #e2e8f0;
        border-radius: 2px;
        overflow: hidden;
        margin-top: 0.8rem;
        position: relative;
    }
    .progress-bar::after {
        content: "";
        position: absolute;
        left: -40%;
        top: 0;
        height: 100%;
        width: 40%;
        background: linear-gradient(90deg, transparent, #1d6fa5, transparent);
        animation: indeterminate 1.4s ease-in-out infinite;
    }
    @keyframes indeterminate {
        0%   { left: -40%; }
        100% { left: 100%; }
    }
    .file-card {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.7rem 0.9rem;
        background: white;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        margin-top: 0.4rem;
    }
    .file-card .icon {
        width: 34px; height: 34px;
        background: #0f172a;
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        color: white; font-size: 1rem;
    }
    .file-card .name { font-weight: 600; color: #0f172a; }
    .file-card .size { color: #64748b; font-size: 0.8rem; }
</style>
"""

st.set_page_config(
    page_title="Bio Bouncer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="commec-hero">
        <div class="logo">{LOGO_SVG}</div>
        <div class="copy">
            <div class="subtitle">Screening DNA at the door</div>
            <h1>Bio Bouncer</h1>
            <p class="tagline">Bio Bouncer checks every sequence against curated biorisk profiles and pathogen databases — powered by the IBBIS Common Mechanism. Upload a FASTA, and the bouncer says who gets in.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


def pill(label: str, status: str) -> str:
    fg, bg = STATUS_COLORS.get(status, ("#334155", "#e2e8f0"))
    return (
        f'<span class="pill" style="color:{fg};background:{bg};">'
        f'<span class="step-label" style="color:{fg};opacity:0.75;">{label}</span>'
        f"{status}</span>"
    )


def build_command(
    fasta_path: Path,
    output_dir: Path,
    skip_tx: bool,
    skip_nt: bool,
    protein_tool: str,
    threads: int,
    db_dir: str | None,
    verbose: bool,
) -> list[str]:
    cmd = ["commec", "screen", str(fasta_path), "--force", "-o", str(output_dir)]
    if skip_tx:
        cmd.append("--skip-tx")
    if skip_nt:
        cmd.append("--skip-nt")
    if protein_tool:
        cmd += ["-p", protein_tool]
    if threads:
        cmd += ["-t", str(threads)]
    if db_dir:
        cmd += ["-d", db_dir]
    if verbose:
        cmd.append("-v")
    return cmd


def run_screen(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace(" ", "&nbsp;")
    )


def render_summary_table(queries: dict) -> None:
    rows = []
    for name, q in queries.items():
        status = q.get("status") or {}
        rows.append({
            "Query": name,
            "Length": q.get("length", ""),
            "Overall": status.get("screen_status", ""),
            "Biorisk": status.get("biorisk", ""),
            "Taxonomy (AA)": status.get("protein_taxonomy", ""),
            "Taxonomy (NT)": status.get("nucleotide_taxonomy", ""),
            "Low-concern": status.get("low_concern", ""),
        })
    if not rows:
        st.info("No queries in the output.")
        return

    df = pd.DataFrame(rows)

    def color_cell(v):
        fg, bg = STATUS_COLORS.get(v, (None, None))
        if not bg:
            return ""
        return f"color: {fg}; background-color: {bg}; font-weight: 600;"

    status_cols = ["Overall", "Biorisk", "Taxonomy (AA)", "Taxonomy (NT)", "Low-concern"]
    styled = df.style.map(color_cell, subset=status_cols)
    st.dataframe(styled, use_container_width=True, hide_index=True)


def render_query_cards(queries: dict) -> None:
    for name, q in queries.items():
        status = q.get("status") or {}
        overall = status.get("screen_status", "")
        rationale = status.get("rationale", "—")
        length = q.get("length", "")
        pills_html = "".join([
            pill("Overall", overall),
            pill("Biorisk", status.get("biorisk", "")),
            pill("Tax (AA)", status.get("protein_taxonomy", "")),
            pill("Tax (NT)", status.get("nucleotide_taxonomy", "")),
            pill("Cleared", status.get("low_concern", "")),
        ])
        st.markdown(
            f"""
            <div class="query-card">
              <h4>{_escape(name)}</h4>
              <div class="meta">Length: {length} nt</div>
              <div class="pill-row">{pills_html}</div>
              <div class="rationale">{_escape(rationale)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        hits = q.get("hits") or {}
        if hits:
            with st.expander(f"Hits for {name} ({sum(len(v) if isinstance(v, list) else 1 for v in hits.values())})", expanded=False):
                st.json(hits)


def find_outputs(output_dir: Path, fasta_stem: str) -> dict:
    json_files = list(output_dir.glob(f"{fasta_stem}.output.json")) or list(output_dir.glob("*.output.json"))
    log_files = list(output_dir.glob(f"{fasta_stem}.screen.log")) or list(output_dir.glob("*.screen.log"))
    html_files = list(output_dir.glob(f"{fasta_stem}_summary.html")) or list(output_dir.glob("*_summary.html"))
    return {
        "json": json_files[0] if json_files else None,
        "log": log_files[0] if log_files else None,
        "html": html_files[0] if html_files else None,
    }


# ---- Sidebar: options ---------------------------------------------------

with st.sidebar:
    st.markdown("### ⚙️ Screening options")
    skip_tx = st.checkbox(
        "Skip taxonomy search",
        value=True,
        help="`--skip-tx` — skip protein (BLASTX/DIAMOND) and nucleotide (BLASTN) homology searches. Useful if you only have the biorisk database installed.",
    )
    skip_nt = st.checkbox(
        "Skip nucleotide search only",
        value=False,
        help="`--skip-nt` — skip the nucleotide search but keep the protein search.",
        disabled=skip_tx,
    )
    protein_tool = st.selectbox(
        "Protein search tool",
        options=["blastx", "diamond"],
        index=0,
        disabled=skip_tx,
        help="Tool for protein homology search.",
    )
    threads = st.number_input("Threads", min_value=1, max_value=64, value=4, step=1)

    st.markdown("---")
    st.markdown("### 📂 Database directory")
    use_default_db = st.checkbox(
        f"Use {DEFAULT_DB_DIR.relative_to(REPO_ROOT)}",
        value=DEFAULT_DB_DIR.exists(),
        help="If unchecked, type a path below or rely on the YAML config defaults.",
    )
    if use_default_db:
        db_dir_input = str(DEFAULT_DB_DIR)
        st.caption(f"`{db_dir_input}`")
    else:
        db_dir_input = st.text_input("Custom database path", value="")

    st.markdown("---")
    verbose = st.checkbox("Verbose log output (`-v`)", value=False)


# ---- Main: input + run --------------------------------------------------

col_upload, col_meta = st.columns([2, 1])

with col_upload:
    st.markdown("#### Input FASTA")

    if "fasta_blob" not in st.session_state:
        st.session_state.fasta_blob = None

    if st.session_state.fasta_blob is None:
        uploader_key = st.session_state.get("uploader_key", 0)
        new_upload = st.file_uploader(
            "Upload a FASTA file",
            type=["fasta", "fa", "fna", "ffn", "txt"],
            accept_multiple_files=False,
            key=f"fasta_uploader_{uploader_key}",
        )
        if new_upload is not None:
            st.session_state.fasta_blob = {
                "name": new_upload.name,
                "data": new_upload.getvalue(),
            }
            st.rerun()
    else:
        blob = st.session_state.fasta_blob
        size_kb = len(blob["data"]) / 1024
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(
                f"""
                <div class="file-card">
                  <div class="icon">📄</div>
                  <div>
                    <div class="name">{_escape(blob['name'])}</div>
                    <div class="size">{size_kb:.1f} KB</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            if st.button("Remove", use_container_width=True):
                st.session_state.fasta_blob = None
                st.session_state.uploader_key = st.session_state.get("uploader_key", 0) + 1
                st.rerun()

    use_example = st.checkbox(
        f"Use bundled example ({EXAMPLE_FASTA.name})",
        value=False,
        disabled=not EXAMPLE_FASTA.exists() or st.session_state.fasta_blob is not None,
    )

with col_meta:
    st.markdown("#### Run")
    run_clicked = st.button("▶ Run screen", type="primary", use_container_width=True)
    st.caption("Runs `commec screen` in a temp directory and renders the JSON output here.")


# ---- Action -------------------------------------------------------------

if run_clicked:
    blob = st.session_state.get("fasta_blob")
    if blob is None and not use_example:
        st.error("Upload a FASTA file or tick the example checkbox.")
        st.stop()

    with tempfile.TemporaryDirectory(prefix="commec-ui-") as tmp:
        tmp_path = Path(tmp)
        if blob is not None:
            fasta_path = tmp_path / blob["name"]
            fasta_path.write_bytes(blob["data"])
        else:
            fasta_path = tmp_path / EXAMPLE_FASTA.name
            shutil.copy(EXAMPLE_FASTA, fasta_path)

        output_dir = tmp_path / "out"
        output_dir.mkdir()

        cmd = build_command(
            fasta_path=fasta_path,
            output_dir=output_dir,
            skip_tx=skip_tx,
            skip_nt=skip_nt,
            protein_tool=protein_tool,
            threads=threads,
            db_dir=db_dir_input or None,
            verbose=verbose,
        )

        progress_slot = st.empty()
        progress_slot.markdown(
            f"""
            <div class="running-banner">
              <div class="spinner-ring"></div>
              <div>
                <div class="label">Screening in progress…</div>
                <div class="sub">Running <code>commec screen</code> on {_escape(fasta_path.name)} — this may take a while.</div>
                <div class="progress-bar"></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        result = run_screen(cmd)
        progress_slot.empty()

        if result.returncode != 0:
            st.error(f"`commec screen` exited with code {result.returncode}.")
            stderr = (result.stderr or "").strip()
            if stderr:
                with st.expander("Error details", expanded=True):
                    st.code(stderr, language=None)

        outputs = find_outputs(output_dir, fasta_path.stem)

        if outputs["json"]:
            data = json.loads(outputs["json"].read_text())
            queries = data.get("queries") or {}

            st.markdown("#### Summary")
            render_summary_table(queries)

            st.markdown("#### Per-query details")
            render_query_cards(queries)

            st.markdown("#### Downloads")
            dl_cols = st.columns(3)
            with dl_cols[0]:
                st.download_button(
                    "⬇ JSON results",
                    data=outputs["json"].read_bytes(),
                    file_name=outputs["json"].name,
                    mime="application/json",
                    use_container_width=True,
                )
            if outputs["html"]:
                with dl_cols[1]:
                    st.download_button(
                        "⬇ HTML report",
                        data=outputs["html"].read_bytes(),
                        file_name=outputs["html"].name,
                        mime="text/html",
                        use_container_width=True,
                    )
            if outputs["log"]:
                with dl_cols[2]:
                    st.download_button(
                        "⬇ Log file",
                        data=outputs["log"].read_bytes(),
                        file_name=outputs["log"].name,
                        mime="text/plain",
                        use_container_width=True,
                    )
        else:
            st.warning(
                "No JSON output file found. The run probably failed before writing results — "
                "check the log above."
            )
else:
    st.info(
        "Upload a FASTA (or tick the example) on the left, choose options in the sidebar, "
        "then click **Run screen**."
    )
