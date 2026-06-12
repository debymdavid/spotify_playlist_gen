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

@st.cache_data(ttl=120)
def load_songs_by_artist(artist_name):
    conn = get_conn()
    if conn is None: return pd.DataFrame()
    return pd.read_sql_query(
        "SELECT track_id, track_name, COUNT(*) as plays, MAX(CAST(date_played AS TEXT)) as last_played "
        "FROM tracks WHERE LOWER(artist_name) = LOWER(%(a)s) "
        "GROUP BY track_id, track_name ORDER BY plays DESC",
        conn, params={"a": artist_name}
    )

@st.cache_data(ttl=120)
def load_all_artists():
    conn = get_conn()
    if conn is None: return pd.DataFrame()
    return pd.read_sql_query(
        "SELECT artist_name, COUNT(*) as plays, COUNT(DISTINCT track_id) as unique_tracks, "
        "MAX(CAST(date_played AS TEXT)) as last_played "
        "FROM tracks GROUP BY artist_name ORDER BY plays DESC",
        conn
    )

@st.cache_data(ttl=120)
def load_all_recent(n=200):
    conn = get_conn()
    if conn is None: return pd.DataFrame()
    return pd.read_sql_query(
        f"SELECT CAST(date_played AS TEXT) as date_played, CAST(time_played AS TEXT) as time_played, "
        f"track_id, track_name, artist_name FROM tracks "
        f"ORDER BY date_played DESC, time_played DESC LIMIT {n}",
        conn
    )

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

    # Support jumping to Artists page from Overview hero card
    if "nav_page" in st.session_state:
        default_page = ["Overview", "Top Charts", "Artists", "Recent Plays", "Activity"].index(st.session_state.pop("nav_page"))
    else:
        default_page = 0
    page = st.radio("", ["Overview", "Top Charts", "Artists", "Recent Plays", "Activity"], index=default_page, label_visibility="collapsed")

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

    # Shared CSS for rank table
    st.markdown(f'''<style>
      .rank-table {{ width:100%; border-collapse:collapse; }}
      .rank-table td {{ padding:0.45rem 0.5rem; vertical-align:middle; }}
      .rank-table tr:hover td {{ background:{C["card2"]}; border-radius:4px; }}
      .rank-num {{ color:{C["muted"]}; font-size:0.78rem; font-family:"Space Grotesk",sans-serif; width:24px; text-align:right; }}
      .rank-art img {{ width:34px; height:34px; border-radius:6px; object-fit:cover; display:block; }}
      .rank-art-ph {{ width:34px; height:34px; border-radius:6px; background:{C["card2"]}; display:flex; align-items:center; justify-content:center; font-size:0.85rem; }}
      .rank-song {{ color:{C["text"]}; font-size:0.86rem; font-weight:500; user-select:text; cursor:text; }}
      .rank-artist {{ color:{C["sub"]}; font-size:0.73rem; user-select:text; cursor:text; }}
      .rank-plays {{ color:{C["maroon3"]}; font-size:0.78rem; font-weight:600; font-family:"Space Grotesk",sans-serif; text-align:right; white-space:nowrap; }}
    </style>''', unsafe_allow_html=True)

    all_songs = load_top_songs(200)
    col_left, col_right = st.columns([2, 3], gap="large")

    # ── LEFT: Full rankings with search + sort above leaderboard ─────────────
    with col_left:
        st.markdown('<div class="sec-title">🏅 Full Rankings</div>', unsafe_allow_html=True)
        lf1, lf2, lf3 = st.columns([3, 2, 1], gap="small")
        with lf1:
            tc_search = st.text_input("", placeholder="🔍  Search...", label_visibility="collapsed", key="tc_search")
        with lf2:
            tc_sort = st.selectbox("", ["Most Played", "A → Z", "Z → A"], label_visibility="collapsed", key="tc_sort")
        with lf3:
            tc_min = st.number_input("", min_value=1, value=1, step=1, label_visibility="collapsed", key="tc_min", help="Min plays")

        filtered = all_songs.copy()
        if tc_search:
            q = tc_search.lower()
            filtered = filtered[filtered["track_name"].str.lower().str.contains(q) | filtered["artist_name"].str.lower().str.contains(q)]
        filtered = filtered[filtered["plays"] >= tc_min]
        if tc_sort == "A → Z":
            filtered = filtered.sort_values("track_name")
        elif tc_sort == "Z → A":
            filtered = filtered.sort_values("track_name", ascending=False)

        # Preserve original rank from all_songs for correct numbering
        all_songs_ranked = all_songs.reset_index(drop=True)
        all_songs_ranked["rank"] = all_songs_ranked.index + 1
        filtered = filtered.merge(all_songs_ranked[["track_id","rank"]], on="track_id", how="left")
        filtered = filtered.reset_index(drop=True)

        count_label = f"{len(filtered)} results" if (tc_search or tc_min > 1) else f"{len(filtered)} songs"
        st.caption(count_label)

        if filtered.empty:
            st.info("No songs match your search.")
        else:
            rows_html = ''
            for _, row in filtered.head(50).iterrows():
                img = get_track_image(row["track_id"])
                art = f'<img src="{img}" style="width:34px;height:34px;border-radius:6px;object-fit:cover;">' if img else '<div class="rank-art-ph">🎵</div>'
                rank_num = int(row["rank"]) if not pd.isna(row.get("rank", float("nan"))) else "—"
                rows_html += f'''<tr>
                  <td class="rank-num">{rank_num}</td>
                  <td style="padding:0.3rem;">{art}</td>
                  <td style="min-width:0;width:100%;padding:0.45rem 0.5rem;">
                    <div class="rank-song">{row["track_name"]}</div>
                    <div class="rank-artist">{row["artist_name"]}</div>
                  </td>
                  <td class="rank-plays">{int(row["plays"])}</td>
                </tr>'''
            st.markdown(f'<div class="panel" style="padding:0.5rem 0.6rem;max-height:660px;overflow-y:auto;"><table class="rank-table">{rows_html}</table></div>', unsafe_allow_html=True)

    # ── RIGHT: Bar chart (always top 15, unaffected by search) + top 5 artists
    with col_right:
        st.markdown('<div class="sec-title">🎵 Top Songs — Chart</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.plotly_chart(songs_bar(top_songs), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-title">🎤 Top 5 Artists</div>', unsafe_allow_html=True)
        top5_artists = load_all_artists().head(5)
        st.markdown('<div class="panel" style="padding:0.8rem 1rem;">', unsafe_allow_html=True)
        for row in top5_artists.itertuples():
            aimg = get_artist_image(row.artist_name)
            ihtml = f'<img class="artist-avatar" src="{aimg}">' if aimg else '<div class="artist-avatar" style="display:flex;align-items:center;justify-content:center;">🎤</div>'
            st.markdown(f'''<div class="artist-row">
              {ihtml}
              <div style="flex:1;min-width:0;">
                <div class="artist-name">{row.artist_name}</div>
                <div style="font-size:0.71rem;color:{C["muted"]};">{row.unique_tracks} unique tracks</div>
              </div>
              <span class="artist-plays">{row.plays}</span>
            </div>''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:0.72rem;color:{C["muted"]};text-align:right;margin-top:0.35rem;">See all artists → <b>Artists</b> page</div>', unsafe_allow_html=True)

elif page == "Artists":
    st.markdown(f'<div style="font-family:Space Grotesk,sans-serif;font-size:1.6rem;font-weight:800;color:{C["text"]};letter-spacing:-0.02em;margin-bottom:0.3rem;">Artists</div><div style="font-size:0.82rem;color:{C["sub"]};margin-bottom:1.5rem;">Click any artist to view their top songs</div>', unsafe_allow_html=True)

    st.markdown(f"""<style>
      .rank-table {{ width:100%; border-collapse:collapse; }}
      .rank-table td {{ padding:0.45rem 0.5rem; vertical-align:middle; }}
      .rank-table tr:hover td {{ background:{C["card2"]}; }}
      .rank-num {{ color:{C["muted"]}; font-size:0.78rem; font-family:"Space Grotesk",sans-serif; width:24px; text-align:right; }}
      .rank-art img {{ width:34px; height:34px; border-radius:6px; object-fit:cover; display:block; }}
      .rank-art-ph {{ width:34px; height:34px; border-radius:6px; background:{C["card2"]}; display:flex; align-items:center; justify-content:center; }}
      .rank-song {{ color:{C["text"]}; font-size:0.86rem; font-weight:500; user-select:text; cursor:text; }}
      .rank-artist {{ color:{C["sub"]}; font-size:0.73rem; }}
      .rank-plays {{ color:{C["maroon3"]}; font-size:0.78rem; font-weight:600; font-family:"Space Grotesk",sans-serif; text-align:right; white-space:nowrap; }}
    </style>""", unsafe_allow_html=True)

    all_artists = load_all_artists()

    # Search + sort
    a1, a2 = st.columns([3, 1], gap="medium")
    with a1:
        ar_search = st.text_input("", placeholder="🔍  Search artists...", label_visibility="collapsed", key="ar_search")
    with a2:
        ar_sort = st.selectbox("", ["Most Played", "A → Z", "Most Unique Tracks"], label_visibility="collapsed", key="ar_sort")

    ar_filtered = all_artists.copy()
    if ar_search:
        ar_filtered = ar_filtered[ar_filtered["artist_name"].str.lower().str.contains(ar_search.lower())]
    if ar_sort == "A → Z":
        ar_filtered = ar_filtered.sort_values("artist_name")
    elif ar_sort == "Most Unique Tracks":
        ar_filtered = ar_filtered.sort_values("unique_tracks", ascending=False)
    ar_filtered = ar_filtered.reset_index(drop=True)

    # Session state for selected artist
    if "selected_artist" not in st.session_state:
        st.session_state["selected_artist"] = None
    # Auto-select if search matches exactly one
    if ar_search and len(ar_filtered) == 1:
        st.session_state["selected_artist"] = ar_filtered.iloc[0]["artist_name"]
    # Handle nav from other pages
    if "go_artist" in st.session_state:
        st.session_state["selected_artist"] = st.session_state.pop("go_artist")

    selected = st.session_state["selected_artist"]

    # ── Drill-down shown ABOVE artist list ────────────────────────────────────
    if selected and selected in all_artists["artist_name"].values:
        artist_songs = load_songs_by_artist(selected)
        aimg_big     = get_artist_image(selected)

        st.markdown(f'<div style="height:1px;background:linear-gradient(90deg,{C["maroon"]},{C["navy2"]},transparent);margin:0.2rem 0 1rem;"></div>', unsafe_allow_html=True)

        h1, h2, h3 = st.columns([1, 4, 1], gap="medium")
        with h1:
            if aimg_big:
                st.markdown(f'<img src="{aimg_big}" style="width:100%;max-width:130px;border-radius:12px;object-fit:cover;">', unsafe_allow_html=True)
        with h2:
            total_plays = int(artist_songs["plays"].sum()) if not artist_songs.empty else 0
            unique_t    = len(artist_songs)
            st.markdown(f"""<div style="padding-top:0.4rem;">
              <div style="font-family:Space Grotesk,sans-serif;font-size:1.4rem;font-weight:800;color:{C['text']};">{selected}</div>
              <div style="font-size:0.8rem;color:{C['sub']};margin-top:0.25rem;">{total_plays:,} plays &middot; {unique_t} unique tracks</div>
              <div style="display:flex;gap:1.5rem;margin-top:0.85rem;">
                <div><div style="font-size:0.65rem;color:{C['muted']};text-transform:uppercase;letter-spacing:0.08em;">Total Plays</div>
                  <div style="font-family:Space Grotesk;font-size:1.25rem;font-weight:700;color:{C['text']};">{total_plays:,}</div></div>
                <div><div style="font-size:0.65rem;color:{C['muted']};text-transform:uppercase;letter-spacing:0.08em;">Unique Tracks</div>
                  <div style="font-family:Space Grotesk;font-size:1.25rem;font-weight:700;color:{C['text']};">{unique_t}</div></div>
              </div></div>""", unsafe_allow_html=True)
        with h3:
            if st.button("✕  Reset", key="reset_artist"):
                st.session_state["selected_artist"] = None
                st.rerun()

        if not artist_songs.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            d1, d2 = st.columns([2, 3], gap="large")
            with d1:
                st.markdown(f"<div class='sec-title'>🎵 {selected}'s Songs</div>", unsafe_allow_html=True)
                rows_html = ""
                for i, row in enumerate(artist_songs.itertuples(), start=1):
                    img = get_track_image(row.track_id)
                    art = f'<img src="{img}" style="width:34px;height:34px;border-radius:6px;object-fit:cover;">' if img else '<div class="rank-art-ph">🎵</div>'
                    rows_html += f"""<tr>
                      <td class="rank-num">{i}</td>
                      <td style="padding:0.3rem;">{art}</td>
                      <td style="min-width:0;width:100%;padding:0.45rem 0.5rem;">
                        <div class="rank-song">{row.track_name}</div>
                        <div class="rank-artist" style="color:{C['muted']};">Last: {row.last_played}</div>
                      </td>
                      <td class="rank-plays">{row.plays}</td>
                    </tr>"""
                st.markdown(f'<div class="panel" style="padding:0.5rem 0.6rem;max-height:460px;overflow-y:auto;"><table class="rank-table">{rows_html}</table></div>', unsafe_allow_html=True)

            with d2:
                st.markdown('<div class="sec-title">📊 Play Distribution</div>', unsafe_allow_html=True)
                d = artist_songs.head(12).copy().iloc[::-1]
                d["label"] = d["track_name"].apply(lambda x: x[:24]+"…" if len(x)>24 else x)
                fig = go.Figure(go.Bar(
                    x=d["plays"], y=d["label"], orientation="h",
                    marker=dict(color=d["plays"], colorscale=[[0,C["navy"]],[0.5,C["maroon"]],[1,C["maroon3"]]], line=dict(width=0)),
                    hovertemplate="<b>%{customdata}</b><br>%{x} plays<extra></extra>",
                    customdata=d["track_name"], text=d["plays"], textposition="outside",
                    textfont=dict(color=C["sub"], size=10),
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color=C["sub"], size=11),
                    margin=dict(l=8,r=8,t=24,b=8), height=420,
                    xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0, d["plays"].max()*1.2]),
                    yaxis=dict(showgrid=False, tickfont=dict(size=10, color=C["text"]), automargin=True),
                    bargap=0.28, showlegend=False,
                )
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(f'<div style="height:1px;background:{C["border"]};margin:1.5rem 0 1rem;"></div>', unsafe_allow_html=True)

    # ── Artist grid — click View to select ────────────────────────────────────
    st.markdown(f'<div class="sec-title">🎤 All Artists ({len(ar_filtered)})</div>', unsafe_allow_html=True)
    if ar_filtered.empty:
        st.info("No artists match your search.")
    else:
        cols = st.columns(2, gap="medium")
        for idx, row in enumerate(ar_filtered.itertuples()):
            with cols[idx % 2]:
                aimg = get_artist_image(row.artist_name)
                ihtml = f'<img class="artist-avatar" style="width:42px;height:42px;" src="{aimg}">' if aimg else '<div class="artist-avatar" style="width:42px;height:42px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;">🎤</div>'
                is_sel = (row.artist_name == selected)
                bg = f"background:{C['maroon_dim']};border:1px solid {C['maroon']};" if is_sel else f"border:1px solid {C['border']};"
                card_col, btn_col = st.columns([5, 1], gap="small")
                with card_col:
                    st.markdown(f"""<div style="display:flex;align-items:center;gap:0.75rem;padding:0.55rem 0.7rem;
                      border-radius:9px;margin-bottom:0.1rem;{bg}">
                      {ihtml}
                      <div style="flex:1;min-width:0;">
                        <div class="artist-name">{row.artist_name}</div>
                        <div style="font-size:0.72rem;color:{C['muted']};">{row.unique_tracks} tracks · last {row.last_played}</div>
                      </div>
                      <span class="artist-plays">{row.plays}</span>
                    </div>""", unsafe_allow_html=True)
                with btn_col:
                    if st.button("View", key=f"sel_{idx}"):
                        st.session_state["selected_artist"] = row.artist_name
                        st.rerun()

elif page == "Recent Plays":
    st.markdown(f'<div style="font-family:Space Grotesk,sans-serif;font-size:1.6rem;font-weight:800;color:{C["text"]};letter-spacing:-0.02em;margin-bottom:0.3rem;">Recent Plays</div><div style="font-size:0.82rem;color:{C["sub"]};margin-bottom:1.5rem;">Your play history</div>', unsafe_allow_html=True)

    r1, r2, r3 = st.columns([3, 1, 1], gap="medium")
    with r1:
        rp_search = st.text_input("", placeholder="🔍  Search songs or artists...", label_visibility="collapsed", key="rp_search")
    with r2:
        rp_sort = st.selectbox("", ["Newest First", "Oldest First", "A → Z"], label_visibility="collapsed", key="rp_sort")
    with r3:
        rp_limit = st.selectbox("Show", [50, 100, 200], label_visibility="collapsed", key="rp_limit")

    all_recent = load_all_recent(200)
    rp_filtered = all_recent.copy()
    if rp_search:
        q = rp_search.lower()
        rp_filtered = rp_filtered[rp_filtered["track_name"].str.lower().str.contains(q) | rp_filtered["artist_name"].str.lower().str.contains(q)]
    if rp_sort == "Oldest First":
        rp_filtered = rp_filtered.sort_values(["date_played", "time_played"])
    elif rp_sort == "A → Z":
        rp_filtered = rp_filtered.sort_values("track_name")
    rp_filtered = rp_filtered.head(rp_limit).reset_index(drop=True)

    count_label = f"{len(rp_filtered)} tracks" + (f" matching '{rp_search}'" if rp_search else "")
    st.markdown(f'<div class="sec-title">🎵 {count_label}</div>', unsafe_allow_html=True)

    if rp_filtered.empty:
        st.info("No tracks match your search.")
    else:
        st.markdown('<div class="panel" style="padding:0.6rem 1rem;">', unsafe_allow_html=True)
        for row in rp_filtered.itertuples():
            img = get_track_image(row.track_id)
            ihtml = f'<img class="track-img" src="{img}">' if img else '<div class="track-img" style="display:flex;align-items:center;justify-content:center;background:#1e1e3a;border-radius:6px;">🎵</div>'
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