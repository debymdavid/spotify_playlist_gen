import os
import subprocess
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

import spotipy
from spotipy.oauth2 import SpotifyOAuth

DB_PATH = "spotify_data.db"

C = {
    "bg":         "#0b0b18",
    "surface":    "#131325",
    "card":       "#181830",
    "card2":      "#1e1e3a",
    "border":     "#38386a",
    "maroon":     "#8b0000",
    "maroon2":    "#b3002d",
    "maroon3":    "#e0003a",
    "maroon_dim": "#4a0018",
    "navy":       "#1228aa",
    "navy2":      "#1e3abf",
    "navy3":      "#3358e8",
    "navy_dim":   "#0a1245",
    "gold":       "#c8a84b",
    "gold2":      "#eacb6e",
    "text":       "#f2f2ff",
    "sub":        "#a0a0c8",
    "muted":      "#55557a",
}

st.set_page_config(page_title="Spotify Stats", page_icon="🎵", layout="wide", initial_sidebar_state="expanded")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif; background-color: {C['bg']}; color: {C['text']}; }}
.block-container {{ padding: 2.2rem 2rem 2rem; max-width: 1400px; }}
[data-testid="stSidebar"] {{ background: {C['surface']} !important; border-right: 1px solid {C['border']}; }}
[data-testid="stSidebar"] .block-container {{ padding: 1.5rem 1rem; }}
div[data-testid="metric-container"] {{ background: {C['card']}; border: 1px solid {C['border']}; border-radius: 14px; padding: 1.2rem 1.4rem; position: relative; overflow: hidden; }}
div[data-testid="metric-container"]::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, {C['maroon']}, {C['navy2']}); }}
div[data-testid="metric-container"] label {{ color: {C['sub']} !important; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; }}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{ color: {C['text']} !important; font-size: 1.9rem; font-weight: 700; font-family: 'Space Grotesk', sans-serif; }}
.sec-title {{ font-family: 'Space Grotesk', sans-serif; font-size: 0.72rem; font-weight: 600; color: {C['sub']}; text-transform: uppercase; letter-spacing: 0.12em; margin: 1.6rem 0 0.9rem; display: flex; align-items: center; gap: 0.5rem; }}
.sec-title::after {{ content: ''; flex: 1; height: 1px; background: {C['border']}; }}
.panel {{ background: {C['card']}; border: 1px solid {C['border']}; border-radius: 14px; padding: 1.2rem 1.4rem; height: 100%; }}
.hero-card {{ background: {C['card']}; border: 1px solid {C['border']}; border-radius: 14px; overflow: hidden; position: relative; display: flex; align-items: flex-end; min-height: 190px; }}
.hero-img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; opacity: 0.55; }}
.hero-overlay {{ position: relative; z-index: 2; padding: 1rem 1.2rem; width: 100%; background: linear-gradient(0deg, {C['bg']}dd 0%, transparent 100%); }}
.hero-label {{ font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: {C['gold']}; margin-bottom: 0.25rem; }}
.hero-name {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.15rem; font-weight: 700; color: {C['text']}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.hero-sub {{ font-size: 0.78rem; color: {C['sub']}; margin-top: 0.15rem; }}
.hero-badge {{ display: inline-block; background: {C['maroon']}; color: white; font-size: 0.68rem; font-weight: 600; padding: 0.18rem 0.55rem; border-radius: 20px; margin-top: 0.4rem; }}
.track-row {{ display: flex; align-items: center; gap: 0.85rem; padding: 0.55rem 0.7rem; border-radius: 8px; transition: background 0.12s; }}
.track-row:hover {{ background: {C['card2']}; }}
.track-num {{ color: {C['muted']}; font-size: 0.78rem; width: 20px; text-align: right; flex-shrink: 0; font-family: 'Space Grotesk', sans-serif; }}
.track-img {{ width: 36px; height: 36px; border-radius: 6px; object-fit: cover; flex-shrink: 0; background: {C['card2']}; }}
.track-info {{ flex: 1; min-width: 0; }}
.track-name {{ color: {C['text']}; font-weight: 500; font-size: 0.88rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.track-artist {{ color: {C['sub']}; font-size: 0.74rem; margin-top: 1px; }}
.track-plays {{ color: {C['maroon3']}; font-size: 0.78rem; font-weight: 600; flex-shrink: 0; font-family: 'Space Grotesk', sans-serif; }}
.track-time {{ color: {C['sub']}; font-size: 0.74rem; flex-shrink: 0; }}
.artist-row {{ display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0.6rem; border-radius: 8px; transition: background 0.12s; }}
.artist-row:hover {{ background: {C['card2']}; }}
.artist-avatar {{ width: 38px; height: 38px; border-radius: 50%; object-fit: cover; flex-shrink: 0; background: {C['navy_dim']}; border: 2px solid {C['border']}; }}
.artist-name {{ flex: 1; font-size: 0.88rem; font-weight: 500; color: {C['text']}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.artist-plays {{ color: {C['gold']}; font-size: 0.78rem; font-weight: 600; flex-shrink: 0; font-family: 'Space Grotesk', sans-serif; }}
.stButton > button {{ background: linear-gradient(135deg, {C['maroon']}, {C['maroon2']}) !important; color: white !important; border: none !important; border-radius: 9px !important; font-weight: 600 !important; font-size: 0.82rem !important; padding: 0.5rem 1.1rem !important; letter-spacing: 0.03em !important; }}
hr {{ border-color: {C['border']} !important; margin: 1rem 0 !important; }}
#MainMenu, footer {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}
[data-testid="stSidebarNav"] {{ display: none; }}
[data-testid="stSidebarCollapseButton"] {{ visibility: visible !important; opacity: 1 !important; display: flex !important; }}
[data-testid="collapsedControl"] {{ visibility: visible !important; opacity: 1 !important; display: flex !important; color: #f2f2ff !important; }}
button[kind="header"] {{ visibility: visible !important; }}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_conn():
    url = os.getenv('SUPABASE_DB_URL')
    if url:
        from sqlalchemy import create_engine
        return create_engine(url)
    if Path(DB_PATH).exists():
        from sqlalchemy import create_engine
        return create_engine(f"sqlite:///{DB_PATH}")
    return None

@st.cache_resource
def get_sp():
    try:
        return spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-recently-played", cache_path=".cache"))
    except Exception:
        return None

@st.cache_data(ttl=120)
def load_top_songs(n=20):
    conn = get_conn()
    if conn is None: return pd.DataFrame()
    return pd.read_sql_query(f"SELECT track_id, track_name, artist_name, COUNT(*) as plays FROM tracks GROUP BY track_id, track_name, artist_name ORDER BY plays DESC LIMIT {n}", conn)

@st.cache_data(ttl=120)
def load_top_artists(n=12):
    conn = get_conn()
    if conn is None: return pd.DataFrame()
    return pd.read_sql_query(f"SELECT artist_name, COUNT(*) as plays, MAX(track_id) as sample_track_id FROM tracks GROUP BY artist_name ORDER BY plays DESC LIMIT {n}", conn)

@st.cache_data(ttl=120)
def load_recent(n=30):
    conn = get_conn()
    if conn is None: return pd.DataFrame()
    return pd.read_sql_query(f"SELECT CAST(date_played AS TEXT) as date_played, CAST(time_played AS TEXT) as time_played, track_id, track_name, artist_name FROM tracks ORDER BY date_played DESC, time_played DESC LIMIT {n}", conn)

@st.cache_data(ttl=120)
def load_stats():
    conn = get_conn()
    if conn is None: return {}
    df = pd.read_sql_query("SELECT COUNT(*) as total, COUNT(DISTINCT track_id) as unique_tracks, COUNT(DISTINCT artist_name) as artists, CAST(MIN(date_played) AS TEXT) as date_from, CAST(MAX(date_played) AS TEXT) as date_to FROM tracks", conn)
    r = df.iloc[0]
    return {"total": int(r["total"]), "unique": int(r["unique_tracks"]), "artists": int(r["artists"]), "from": str(r["date_from"]), "to": str(r["date_to"])}

@st.cache_data(ttl=120)
def load_hourly():
    conn = get_conn()
    if conn is None: return pd.DataFrame()
    return pd.read_sql_query("SELECT CAST(SUBSTR(CAST(time_played AS TEXT), 1, 2) AS INTEGER) as hour, COUNT(*) as plays FROM tracks GROUP BY hour ORDER BY hour", conn)

@st.cache_data(ttl=120)
def load_daily():
    conn = get_conn()
    if conn is None: return pd.DataFrame()
    return pd.read_sql_query("SELECT CAST(date_played AS TEXT) as date_played, COUNT(*) as plays FROM tracks GROUP BY date_played ORDER BY date_played DESC LIMIT 30", conn)

@st.cache_data(ttl=3600)
def get_track_image(track_id):
    sp = get_sp()
    if not sp or not track_id: return None
    try:
        t = sp.track(track_id)
        imgs = t['album']['images']
        return imgs[1]['url'] if len(imgs) > 1 else imgs[0]['url']
    except Exception:
        return None

@st.cache_data(ttl=3600)
def get_artist_image(artist_name):
    sp = get_sp()
    if not sp: return None
    try:
        r = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
        items = r['artists']['items']
        if items and items[0]['images']:
            return items[0]['images'][0]['url']
    except Exception:
        pass
    return None

def base_layout(**kwargs):
    d = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter", color=C["sub"], size=11), margin=dict(l=8, r=8, t=24, b=8), showlegend=False)
    d.update(kwargs)
    return d

def songs_bar(df):
    d = df.head(15).copy()
    d["label"] = d["track_name"].apply(lambda x: x[:22]+"…" if len(x)>22 else x)
    d = d.iloc[::-1]
    fig = go.Figure(go.Bar(
        x=d["plays"], y=d["label"], orientation="h",
        marker=dict(color=d["plays"], colorscale=[[0, C["navy"]], [0.4, C["maroon"]], [1, C["maroon3"]]], line=dict(width=0)),
        customdata=list(zip(d["track_name"], d["artist_name"])),
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{x} plays<extra></extra>",
        text=d["plays"], textposition="outside", textfont=dict(color=C["sub"], size=10),
    ))
    fig.update_layout(
        **base_layout(height=460),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0, d["plays"].max()*1.18]),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, color=C["text"]), automargin=True),
        bargap=0.28,
    )
    return fig

def hourly_chart(df):
    if df.empty: return go.Figure()
    fig = go.Figure(go.Bar(x=df["hour"], y=df["plays"], marker=dict(color=df["plays"], colorscale=[[0, C["navy_dim"]], [0.5, C["navy2"]], [1, C["maroon2"]]], line=dict(width=0)), hovertemplate="<b>%{x}:00</b><br>%{y} plays<extra></extra>"))
    fig.update_layout(**base_layout(height=200), xaxis=dict(showgrid=False, tickmode='array', tickvals=list(range(0,24,3)), ticktext=[f"{h}:00" for h in range(0,24,3)], tickfont=dict(size=9)), yaxis=dict(showgrid=True, gridcolor=C["border"], zeroline=False, tickfont=dict(size=9)), bargap=0.15)
    return fig

def daily_area(df):
    if df.empty: return go.Figure()
    df = df.iloc[::-1]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date_played"], y=df["plays"], mode="lines", fill="tozeroy", line=dict(color=C["maroon2"], width=2), fillcolor="rgba(158,0,48,0.18)", hovertemplate="%{x}<br><b>%{y} plays</b><extra></extra>"))
    fig.update_layout(**base_layout(height=165), xaxis=dict(showgrid=False, tickfont=dict(size=9)), yaxis=dict(showgrid=True, gridcolor=C["border"], zeroline=False, tickfont=dict(size=9)))
    return fig

def daily_area_tall(df):
    if df.empty: return go.Figure()
    df = df.iloc[::-1]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date_played"], y=df["plays"], mode="lines+markers", fill="tozeroy",
        line=dict(color=C["maroon2"], width=2.5),
        marker=dict(size=5, color=C["maroon3"], line=dict(width=1, color=C["bg"])),
        fillcolor="rgba(179,0,45,0.15)",
        hovertemplate="<b>%{x}</b><br>%{y} plays<extra></extra>"))
    fig.update_layout(**base_layout(height=260),
        xaxis=dict(showgrid=False, tickfont=dict(size=10), tickangle=-30),
        yaxis=dict(showgrid=True, gridcolor=C["border"], zeroline=False, tickfont=dict(size=10)))
    return fig

# ── Load ──────────────────────────────────────────────────────────────────────
conn = get_conn()
if conn is None:
    st.error("Could not connect to database.")
    st.stop()

top_songs   = load_top_songs(20)
top_artists = load_top_artists(12)
recent      = load_recent(30)
hourly      = load_hourly()
daily       = load_daily()
stats       = load_stats()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1.8rem;padding:0 0.4rem;">
      <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,{C['maroon']},{C['navy2']});display:flex;align-items:center;justify-content:center;font-size:1.1rem;flex-shrink:0;">🎵</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:0.95rem;color:{C['text']};">Spotify Stats</div>
        <div style="font-size:0.7rem;color:{C['sub']};">Personal Dashboard</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("", ["Overview", "Top Charts", "Recent Plays", "Activity"], label_visibility="collapsed")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.68rem;color:{C["muted"]};text-transform:uppercase;letter-spacing:0.1em;padding:0 0.4rem;margin-bottom:0.5rem;">Controls</div>', unsafe_allow_html=True)

    if st.button("▶  Log Tracks Now", use_container_width=True):
        with st.spinner("Logging..."):
            result = subprocess.run(["python3", "main.py"], capture_output=True, text=True, cwd=str(Path(__file__).parent))
            if result.returncode == 0:
                st.success("Done!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(result.stderr[:200])

    if st.button("↺  Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="padding:0 0.4rem;">
      <div style="font-size:0.68rem;color:{C['muted']};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.7rem;">Your Library</div>
      <div style="display:flex;flex-direction:column;gap:0.5rem;">
        <div style="display:flex;justify-content:space-between;"><span style="font-size:0.8rem;color:{C['sub']};">Total plays</span><span style="font-family:'Space Grotesk';font-weight:700;color:{C['text']};font-size:0.9rem;">{stats.get('total',0):,}</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="font-size:0.8rem;color:{C['sub']};">Unique tracks</span><span style="font-family:'Space Grotesk';font-weight:700;color:{C['text']};font-size:0.9rem;">{stats.get('unique',0):,}</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="font-size:0.8rem;color:{C['sub']};">Artists</span><span style="font-family:'Space Grotesk';font-weight:700;color:{C['text']};font-size:0.9rem;">{stats.get('artists',0):,}</span></div>
        <div style="margin-top:0.3rem;font-size:0.7rem;color:{C['muted']};">{stats.get('from','—')} → {stats.get('to','—')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.markdown(f'<div style="font-family:Space Grotesk,sans-serif;font-size:1.6rem;font-weight:800;color:{C["text"]};letter-spacing:-0.02em;margin-bottom:0.3rem;">Overview</div><div style="font-size:0.82rem;color:{C["sub"]};margin-bottom:1.5rem;">Your listening at a glance</div>', unsafe_allow_html=True)

    if not top_songs.empty and not top_artists.empty:
        col1, col2, col3 = st.columns(3, gap="medium")

        with col1:
            t = top_songs.iloc[0]
            img = get_track_image(t['track_id'])
            bg = f'<img class="hero-img" src="{img}">' if img else f'<div style="position:absolute;inset:0;background:linear-gradient(135deg,{C["maroon_dim"]},{C["navy_dim"]});"></div>'
            st.markdown(f'<div class="hero-card">{bg}<div class="hero-overlay"><div class="hero-label">🏆 Top Track</div><div class="hero-name">{t["track_name"]}</div><div class="hero-sub">{t["artist_name"]}</div><div class="hero-badge">{t["plays"]} plays</div></div></div>', unsafe_allow_html=True)

        with col2:
            a = top_artists.iloc[0]
            aimg = get_artist_image(a['artist_name'])
            bg2 = f'<img class="hero-img" src="{aimg}">' if aimg else f'<div style="position:absolute;inset:0;background:linear-gradient(135deg,{C["navy_dim"]},{C["maroon_dim"]});"></div>'
            st.markdown(f'<div class="hero-card">{bg2}<div class="hero-overlay"><div class="hero-label" style="color:{C["gold2"]};">🎤 Top Artist</div><div class="hero-name">{a["artist_name"]}</div><div class="hero-sub">Most played artist</div><div class="hero-badge" style="background:{C["navy2"]};">{a["plays"]} plays</div></div></div>', unsafe_allow_html=True)

        with col3:
            if not recent.empty:
                rec = recent.iloc[0]
                rimg = get_track_image(rec['track_id'])
                bg3 = f'<img class="hero-img" src="{rimg}">' if rimg else f'<div style="position:absolute;inset:0;background:linear-gradient(135deg,{C["card"]},{C["card2"]});"></div>'
                st.markdown(f'<div class="hero-card">{bg3}<div class="hero-overlay"><div class="hero-label" style="color:{C["sub"]};">⏱ Last Played</div><div class="hero-name">{rec["track_name"]}</div><div class="hero-sub">{rec["artist_name"]}</div><div class="hero-badge" style="background:{C["muted"]};">{str(rec["time_played"])[:5]}  {rec["date_played"]}</div></div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 2: daily activity full width
    st.markdown('<div class="sec-title">📅 Daily Activity — last 30 days</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.plotly_chart(daily_area_tall(daily), use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    # Row 3: hourly + top 5 songs side by side
    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        st.markdown('<div class="sec-title">🕐 Listening by Hour</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.plotly_chart(hourly_chart(hourly), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="sec-title">🏅 Quick Top 5</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel" style="padding:0.6rem 0.9rem;">', unsafe_allow_html=True)
        if not top_songs.empty:
            for i, row in enumerate(top_songs.head(5).itertuples(), start=1):
                img = get_track_image(row.track_id)
                ihtml = f'<img class="track-img" src="{img}">' if img else f'<div class="track-img" style="display:flex;align-items:center;justify-content:center;background:{C["card2"]};border-radius:6px;">🎵</div>'
                st.markdown(f'''<div class="track-row">
                  <span class="track-num">{i}</span>{ihtml}
                  <div class="track-info"><div class="track-name">{row.track_name}</div><div class="track-artist">{row.artist_name}</div></div>
                  <span class="track-plays">{row.plays}</span></div>''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif page == "Top Charts":
    st.markdown(f'<div style="font-family:Space Grotesk,sans-serif;font-size:1.6rem;font-weight:800;color:{C["text"]};letter-spacing:-0.02em;margin-bottom:0.3rem;">Top Charts</div><div style="font-size:0.82rem;color:{C["sub"]};margin-bottom:1.5rem;">Your most played songs and artists</div>', unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 3], gap="large")

    # ── LEFT: Full rankings with selectable/copyable song & artist names ──────
    with col_left:
        st.markdown('<div class="sec-title">🏅 Full Rankings</div>', unsafe_allow_html=True)
        st.markdown(f'''
        <style>
          .rank-table {{ width:100%; border-collapse:collapse; }}
          .rank-table td {{ padding: 0.45rem 0.5rem; vertical-align:middle; }}
          .rank-table tr:hover td {{ background:{C["card2"]}; border-radius:6px; }}
          .rank-num {{ color:{C["muted"]}; font-size:0.78rem; font-family:"Space Grotesk",sans-serif; width:24px; text-align:right; }}
          .rank-art {{ width:34px; }}
          .rank-art img {{ width:34px; height:34px; border-radius:6px; object-fit:cover; display:block; }}
          .rank-art-placeholder {{ width:34px; height:34px; border-radius:6px; background:{C["card2"]}; display:flex; align-items:center; justify-content:center; font-size:0.85rem; }}
          .rank-song {{ color:{C["text"]}; font-size:0.86rem; font-weight:500; user-select:text; cursor:text; }}
          .rank-artist {{ color:{C["sub"]}; font-size:0.73rem; user-select:text; cursor:text; }}
          .rank-plays {{ color:{C["maroon3"]}; font-size:0.78rem; font-weight:600; font-family:"Space Grotesk",sans-serif; text-align:right; white-space:nowrap; }}
        </style>
        ''', unsafe_allow_html=True)

        if not top_songs.empty:
            rows_html = ''
            for i, row in enumerate(top_songs.head(20).itertuples(), start=1):
                img = get_track_image(row.track_id)
                art = f'<img src="{img}" style="width:34px;height:34px;border-radius:6px;object-fit:cover;">' if img else f'<div class="rank-art-placeholder">🎵</div>'
                rows_html += f'''<tr>
                  <td class="rank-num">{i}</td>
                  <td class="rank-art">{art}</td>
                  <td style="min-width:0;width:100%;padding:0.45rem 0.5rem;">
                    <div class="rank-song">{row.track_name}</div>
                    <div class="rank-artist">{row.artist_name}</div>
                  </td>
                  <td class="rank-plays">{row.plays}</td>
                </tr>'''
            st.markdown(f'<div class="panel" style="padding:0.5rem 0.6rem;"><table class="rank-table">{rows_html}</table></div>', unsafe_allow_html=True)

    # ── RIGHT: Bar chart on top, artists list below ───────────────────────────
    with col_right:
        st.markdown('<div class="sec-title">🎵 Top Songs</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        if not top_songs.empty:
            st.plotly_chart(songs_bar(top_songs), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-title">🎤 Top Artists</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel" style="padding:0.8rem 1rem;">', unsafe_allow_html=True)
        for row in top_artists.head(8).itertuples():
            aimg = get_artist_image(row.artist_name)
            ihtml = f'<img class="artist-avatar" src="{aimg}">' if aimg else f'<div class="artist-avatar" style="display:flex;align-items:center;justify-content:center;">🎤</div>'
            st.markdown(f'<div class="artist-row">{ihtml}<span class="artist-name">{row.artist_name}</span><span class="artist-plays">{row.plays}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif page == "Recent Plays":
    st.markdown(f'<div style="font-family:Space Grotesk,sans-serif;font-size:1.6rem;font-weight:800;color:{C["text"]};letter-spacing:-0.02em;margin-bottom:0.3rem;">Recent Plays</div><div style="font-size:0.82rem;color:{C["sub"]};margin-bottom:1.5rem;">Last 30 tracks logged</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel" style="padding:0.6rem 1rem;">', unsafe_allow_html=True)
    for row in recent.itertuples():
        img = get_track_image(row.track_id)
        ihtml = f'<img class="track-img" src="{img}">' if img else f'<div class="track-img" style="display:flex;align-items:center;justify-content:center;">🎵</div>'
        name = row.track_name[:42]+"…" if len(row.track_name)>42 else row.track_name
        st.markdown(f'<div class="track-row">{ihtml}<div class="track-info"><div class="track-name">{name}</div><div class="track-artist">{row.artist_name}</div></div><span class="track-time">{str(row.time_played)[:5]}&nbsp;&nbsp;{row.date_played}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Activity":
    st.markdown(f'<div style="font-family:Space Grotesk,sans-serif;font-size:1.6rem;font-weight:800;color:{C["text"]};letter-spacing:-0.02em;margin-bottom:0.3rem;">Activity</div><div style="font-size:0.82rem;color:{C["sub"]};margin-bottom:1.5rem;">When and how much you listen</div>', unsafe_allow_html=True)

    # Row 1: stat cards across full width
    if not hourly.empty and not daily.empty:
        peak_h  = hourly.loc[hourly["plays"].idxmax()]
        avg_d   = daily["plays"].mean()
        peak_d  = daily.loc[daily["plays"].idxmax()]
        total_w = int(daily.head(7)["plays"].sum())
        s1, s2, s3, s4 = st.columns(4, gap="medium")
        s1.metric("Peak Hour",   f'{int(peak_h["hour"]):02d}:00',    f'{int(peak_h["plays"])} plays')
        s2.metric("Best Day",    str(peak_d["date_played"])[-5:],     f'{int(peak_d["plays"])} plays')
        s3.metric("Daily Avg",   f'{avg_d:.1f}',                     "plays / day")
        s4.metric("Last 7 Days", f'{total_w:,}',                     "total plays")

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 2: daily trend full width, taller
    st.markdown('<div class="sec-title">📅 Daily Plays — last 30 days</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.plotly_chart(daily_area_tall(daily), use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 3: hourly chart + top days bar
    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        st.markdown('<div class="sec-title">🕐 Plays by Hour of Day</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.plotly_chart(hourly_chart(hourly), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="sec-title">📆 Top 8 Days</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel" style="padding:0.8rem 1rem;">', unsafe_allow_html=True)
        if not daily.empty:
            top_days = daily.nlargest(8, "plays")
            max_plays = int(top_days["plays"].max())
            for row in top_days.itertuples():
                pct = int(row.plays / max_plays * 100)
                st.markdown(f'''<div style="margin-bottom:0.65rem;">
                  <div style="display:flex;justify-content:space-between;margin-bottom:0.22rem;">
                    <span style="font-size:0.82rem;color:{C["text"]};">{row.date_played}</span>
                    <span style="font-size:0.82rem;font-weight:600;color:{C["maroon3"]};font-family:Space Grotesk,sans-serif;">{row.plays}</span>
                  </div>
                  <div style="height:5px;background:{C["border"]};border-radius:3px;">
                    <div style="height:5px;width:{pct}%;background:linear-gradient(90deg,{C["navy2"]},{C["maroon2"]});border-radius:3px;"></div>
                  </div></div>''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)