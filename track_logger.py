import logging
import spotipy
import requests
import config
from database import SpotifyDatabase
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LISTEN_THRESHOLD = 0.75


def get_last_logged_timestamp(db):
    """Get the most recent played_at from the DB as a UTC unix timestamp in ms."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT date_played, time_played FROM tracks ORDER BY date_played DESC, time_played DESC LIMIT 1"
        )
        row = cursor.fetchone()

    if not row:
        return None

    try:
        # Stored as local time — convert back to UTC for the Spotify API call
        local_dt = datetime.fromisoformat(f"{row[0]}T{row[1]}")
        local_dt = local_dt.astimezone()           # attach local tz
        utc_dt   = local_dt.astimezone(timezone.utc)
        return int(utc_dt.timestamp() * 1000)      # ms unix timestamp
    except Exception as e:
        logger.warning(f"Could not parse last stored timestamp: {e}")
        return None


def to_local(played_at_str):
    """Convert a Spotify UTC ISO string to the OS local timezone datetime."""
    utc_dt = datetime.fromisoformat(played_at_str.replace("Z", "+00:00"))
    return utc_dt.astimezone()   # converts to local tz automatically


def get_recent_songs(sp):
    try:
        db = SpotifyDatabase()
        after_ms = get_last_logged_timestamp(db)

        if after_ms:
            logger.info(f"Fetching tracks after last log ({datetime.fromtimestamp(after_ms/1000).strftime('%Y-%m-%d %H:%M:%S')} local time)")
            results = sp.current_user_recently_played(limit=config.LIMIT_SONGS, after=after_ms)
        else:
            logger.info("No previous data found — fetching last 50 tracks")
            results = sp.current_user_recently_played(limit=config.LIMIT_SONGS)

        if not results or 'items' not in results:
            logger.warning("No recent tracks returned from API")
            return []

        items = results['items']
        if not items:
            logger.info("No new tracks since last log run")
            return []

        logger.info(f"Fetched {len(items)} new tracks from Spotify API")

        # Parse — API returns newest first, convert to local time immediately
        parsed = []
        for item in items:
            track     = item['track']
            local_dt  = to_local(item['played_at'])
            parsed.append({
                'local_dt':    local_dt,
                'duration_ms': int(float(track['duration_ms'])),
                'track_id':    track['id'],
                'track_name':  track['name'],
                'artist_name': track['artists'][0]['name'],
            })

        # Log what we got
        for p in parsed:
            logger.info(f"  {p['track_name']} | {p['local_dt'].strftime('%Y-%m-%d %H:%M:%S %Z')} | {p['duration_ms']/1000:.1f}s")

        # Get last stored local datetime for evaluating the final item
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT date_played, time_played FROM tracks ORDER BY date_played DESC, time_played DESC LIMIT 1"
            )
            last_row = cursor.fetchone()


        last_stored_local = None
        if last_row:
            try:
                last_stored_local = datetime.fromisoformat(f"{last_row[0]}T{last_row[1]}")
                last_stored_local = last_stored_local.astimezone()
            except Exception:
                pass

        qualified = []
        for i, item in enumerate(parsed):
            duration_ms  = item['duration_ms']
            threshold_ms = duration_ms * LISTEN_THRESHOLD

            if i < len(parsed) - 1:
                listened_ms = (item['local_dt'] - parsed[i + 1]['local_dt']).total_seconds() * 1000
            else:
                if last_stored_local:
                    listened_ms = (item['local_dt'] - last_stored_local).total_seconds() * 1000
                    logger.info(f"Last item '{item['track_name']}': gap from DB = {listened_ms/1000:.1f}s, threshold = {threshold_ms/1000:.1f}s")
                else:
                    logger.info(f"Last item '{item['track_name']}': no DB reference — including by default")
                    listened_ms = threshold_ms

            passed = listened_ms >= threshold_ms
            logger.info(
                f"'{item['track_name']}': listened {listened_ms/1000:.1f}s / "
                f"needed {threshold_ms/1000:.1f}s — {'✅ PASS' if passed else '❌ SKIP'}"
            )

            if passed:
                qualified.append((
                    item['local_dt'].strftime('%Y-%m-%d'),
                    item['local_dt'].strftime('%H:%M:%S'),
                    item['track_id'],
                    item['track_name'],
                    item['artist_name'],
                ))

        logger.info(f"{len(qualified)} of {len(items)} tracks passed the threshold")
        return qualified

    except spotipy.SpotifyException as e:
        logger.error(f"Spotify API error: {e}")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("Network connection error")
        return []
    except Exception as e:
        logger.exception("Unexpected error in get_recent_songs")
        return []


def log_songs(sp):
    tracks = get_recent_songs(sp)
    if not tracks:
        return False
    db = SpotifyDatabase()
    inserted = db.add_tracks(tracks)
    logger.info(f"Logged {inserted} new tracks")
    return True