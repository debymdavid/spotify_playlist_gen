import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH = "spotify_data.db"

COLORS = {
    "bg":        "#0d0d1a",
    "card":      "#16213e",
    "border":    "#2a2a4a",
    "maroon":    "#800020",
    "maroon2":   "#a8003a",
    "navy":      "#1a237e",
    "navy2":     "#283593",
    "gold":      "#c9a84c",
    "text":      "#e8e8f0",
    "subtext":   "#9090b0",
}

PALETTE = [
    "#800020", "#1a237e", "#a8003a", "#283593",
    "#c9a84c", "#4a0080", "#005f73", "#9b2226",
]

st.set_page_config(
    page_title="My Spotify Stats",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] {{
      font-family: 'Inter', sans-serif;
      background-color: {COLORS['bg']};
      color: {COLORS['text']};
  }}
  .block-container {{ padding: 2rem 2.5rem 2rem; }}

  /* metric cards */
  div[data-testid="metric-container"] {{
      background: {COLORS['card']};
      border: 1px solid {COLORS['border']};
      border-radius: 12px;
      padding: 1.2rem 1.5rem;
  }}
  div[data-testid="metric-container"] label {{
      color: {COLORS['subtext']} !important;
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
  }}
  div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
      color: {COLORS['gold']} !important;
      font-size: 2rem;
      font-weight: 700;
  }}

  /* section headers */
  .section-header {{
      font-size: 1.1rem;
      font-weight: 600;
      color: {COLORS['gold']};
      letter-spacing: 0.06em;
      text-transform: uppercase;
      margin: 1.8rem 0 0.8rem;
      padding-bottom: 0.4rem;
      border-bottom: 1px solid {COLORS['border']};
  }}

  /* track rows */
  .track-row {{
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 0.65rem 1rem;
      border-radius: 8px;
      transition: background 0.15s;
  }}
  .track-row:hover {{ background: {COLORS['border']}; }}
  .track-num {{
      color: {COLORS['subtext']};
      font-size: 0.85rem;
      width: 22px;
      text-align: right;
      flex-shrink: 0;
  }}
  .track-info {{ flex: 1; min-width: 0; }}
  .track-name {{
      color: {COLORS['text']};
      font-weight: 500;
      font-size: 0.92rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
  }}
  .track-artist {{
      color: {COLORS['subtext']};
      font-size: 0.78rem;
      margin-top: 1px;
  }}
  .track-plays {{
      color: {COLORS['maroon2']};
      font-size: 0.82rem;
      font-weight: 600;
      flex-shrink: 0;
  }}
  .track-time {{
      color: {COLORS['subtext']};
      font-size: 0.78rem;
      flex-shrink: 0;
  }}

  /* artist badge */
  .artist-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: {COLORS['card']};
      border: 1px solid {COLORS['border']};
      border-radius: 20px;
      padding: 0.3rem 0.85rem;
      margin: 0.25rem;
      font-size: 0.82rem;
      color: {COLORS['text']};
  }}
  .artist-plays {{ color: {COLORS['gold']}; font-weight: 600; }}

  /* chart container */
  .chart-wrap {{
      background: {COLORS['card']};
      border: 1px solid {COLORS['border']};
      border-radius: 12px;
      padding: 1rem;
  }}

  /* hide streamlit chrome */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .stDeployButton {{ display: none; }}
</style>
""", unsafe_allow_html=True)


# ── Data helpers ──────────────────────────────────────────────────────────────
@st.cache_resource
def get_conn():
    if not Path(DB_PATH).exists():
        return None
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

@st.cache_data(ttl=60)
def load_tracks():
    conn = get_conn()
    if conn is None:
        return pd.DataFrame()
    return pd.read_sql_query(
        "SELECT date_played, time_played, track_id, track_name, artist_name FROM tracks ORDER BY date_played DESC, time_played DESC",
        conn
    )

@st.cache_data(ttl=60)
def load_top_songs(n=20):
    conn = get_conn()
    if conn is None:
        return pd.DataFrame()
    return pd.read_sql_query(f"""
        SELECT track_name, artist_name, COUNT(*) as plays
        FROM tracks
        GROUP BY track_id, track_name, artist_name
        ORDER BY plays DESC
        LIMIT {n}
    """, conn)

@st.cache_data(ttl=60)
def load_top_artists(n=15):
    conn = get_conn()
    if conn is None:
        return pd.DataFrame()
    return pd.read_sql_query(f"""
        SELECT artist_name, COUNT(*) as plays
        FROM tracks
        GROUP BY artist_name
        ORDER BY plays DESC
        LIMIT {n}
    """, conn)

@st.cache_data(ttl=60)
def load_stats():
    conn = get_conn()
    if conn is None:
        return {}
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tracks")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT track_id) FROM tracks")
    unique = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT artist_name) FROM tracks")
    artists = cur.fetchone()[0]
    cur.execute("SELECT MIN(date_played), MAX(date_played) FROM tracks")
    dates = cur.fetchone()
    return {"total": total, "unique": unique, "artists": artists, "from": dates[0], "to": dates[1]}


# ── Chart helpers ─────────────────────────────────────────────────────────────
def chart_cfg():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=COLORS["text"], size=12),
        margin=dict(l=10, r=10, t=30, b=10),
    )

def bar_chart_songs(df):
    df = df.copy().iloc[::-1]   # flip so #1 is at top
    fig = go.Figure(go.Bar(
        x=df["plays"],
        y=df["track_name"],
        orientation="h",
        marker=dict(
            color=df["plays"],
            colorscale=[[0, COLORS["navy"]], [0.5, COLORS["maroon"]], [1, COLORS["gold"]]],
            line=dict(width=0),
        ),
        customdata=df["artist_name"],
        hovertemplate="<b>%{y}</b><br>%{customdata}<br>%{x} plays<extra></extra>",
        text=df["plays"],
        textposition="outside",
        textfont=dict(color=COLORS["subtext"], size=11),
    ))
    fig.update_layout(
        **chart_cfg(),
        height=460,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=11)),
        bargap=0.25,
    )
    return fig

def donut_chart_artists(df):
    fig = go.Figure(go.Pie(
        labels=df["artist_name"],
        values=df["plays"],
        hole=0.55,
        marker=dict(colors=PALETTE, line=dict(color=COLORS["bg"], width=2)),
        hovertemplate="<b>%{label}</b><br>%{value} plays (%{percent})<extra></extra>",
        textinfo="none",
    ))
    fig.update_layout(
        **chart_cfg(),
        height=360,
        legend=dict(
            font=dict(size=11, color=COLORS["text"]),
            bgcolor="rgba(0,0,0,0)",
            orientation="v",
            x=1.02, y=0.5,
        ),
        annotations=[dict(
            text=f"<b>{df['plays'].sum()}</b><br><span style='font-size:11px'>plays</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color=COLORS["gold"]),
        )],
    )
    return fig


# ── Page ──────────────────────────────────────────────────────────────────────
conn = get_conn()
if conn is None:
    st.error(f"Could not find `{DB_PATH}`. Make sure you run this from your project folder.")
    st.stop()

tracks_df   = load_tracks()
top_songs   = load_top_songs(20)
top_artists = load_top_artists(12)
stats       = load_stats()

# Header
st.markdown("""
<div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.5rem;">
  <span style="font-size:2.2rem;">🎵</span>
  <div>
    <div style="font-size:1.8rem;font-weight:700;letter-spacing:-0.02em;">My Spotify Stats</div>
    <div style="color:#9090b0;font-size:0.85rem;">Personal listening dashboard</div>
  </div>
</div>
""", unsafe_allow_html=True)

if stats.get("from"):
    st.caption(f"Data from {stats['from']} → {stats['to']}")

st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("Total Plays Logged", f"{stats.get('total', 0):,}")
c2.metric("Unique Tracks", f"{stats.get('unique', 0):,}")
c3.metric("Artists Listened To", f"{stats.get('artists', 0):,}")

# ── Charts row ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Top Songs & Artists</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.markdown("**Top 20 Most Played Songs**")
    if not top_songs.empty:
        st.plotly_chart(bar_chart_songs(top_songs), use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.markdown("**Top Artists by Plays**")
    if not top_artists.empty:
        st.plotly_chart(donut_chart_artists(top_artists), use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── Top songs list (ranked) ───────────────────────────────────────────────────
st.markdown('<div class="section-header">Song Rankings</div>', unsafe_allow_html=True)

left, right = st.columns(2)
mid = len(top_songs) // 2

def render_song_list(df_slice, offset=0):
    html = ""
    for i, row in enumerate(df_slice.itertuples(), start=offset + 1):
        name = row.track_name[:36] + "…" if len(row.track_name) > 36 else row.track_name
        html += f"""
        <div class="track-row">
          <span class="track-num">{i}</span>
          <div class="track-info">
            <div class="track-name">{name}</div>
            <div class="track-artist">{row.artist_name}</div>
          </div>
          <span class="track-plays">{row.plays} plays</span>
        </div>"""
    return html

with left:
    st.markdown(render_song_list(top_songs.iloc[:mid]), unsafe_allow_html=True)
with right:
    st.markdown(render_song_list(top_songs.iloc[mid:], offset=mid), unsafe_allow_html=True)

# ── Top artists badges ────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Top Artists</div>', unsafe_allow_html=True)

badges = ""
for row in top_artists.head(12).itertuples():
    badges += f'<span class="artist-badge">🎤 {row.artist_name} <span class="artist-plays">{row.plays}</span></span>'
st.markdown(f'<div style="display:flex;flex-wrap:wrap;">{badges}</div>', unsafe_allow_html=True)

# ── Recent tracks ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Recently Played</div>', unsafe_allow_html=True)

recent = tracks_df.head(30)
html = ""
for row in recent.itertuples():
    name = row.track_name[:40] + "…" if len(row.track_name) > 40 else row.track_name
    html += f"""
    <div class="track-row">
      <div class="track-info">
        <div class="track-name">{name}</div>
        <div class="track-artist">{row.artist_name}</div>
      </div>
      <span class="track-time">{row.time_played[:5]}  {row.date_played}</span>
    </div>"""
st.markdown(html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🔄  Refresh data"):
    st.cache_data.clear()
    st.rerun()