import csv 
from utils import sort_freq
from utils import get_playlist_id_by_name
import random 
import spotipy
import config

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

num_songs = config.PLAYLIST_SIZE

'''
returns True - if playlist exists 
        False - if it doesn't 
'''
def if_playlist_exists(sp,playlist_name):
    all_playlists = []
    results = sp.current_user_playlists()

    for playlist in results['items']:
        all_playlists.append(playlist['name'].lower())

    return(playlist_name.lower() in all_playlists)

def get_songs():
    song_dict = {}
    prev_freq = 0
    count = 0 

    freq_log = open(config.FREQ_LOG_FILE,'r')
    eye = csv.reader(freq_log)
    next(eye)

    for row in eye:

        freq = row[3]
        track_id = row[0]
        artist_name = row[2]
        deet = (track_id,artist_name)

        if count >= num_songs and prev_freq != freq:
            break    

        if freq in song_dict:
            song_dict[freq].append(deet)
        else:
            song_dict[freq] = [deet]
        count += 1
        prev_freq = freq
    freq_log.close()
    '''
    for key, value in song_dict.items():
        print(f"{key}: {value}")
    '''
    return (song_dict,count)

def final_songs(song_dict,count):

    track_ids = []
    string_list = list(song_dict.keys())
    integer_list = [int(s) for s in string_list]
    least_freq = min(integer_list)
    least_freq = str(least_freq)

    #CreateOnRepeat.random_order(song_dict)
    '''
    for key, value in song_dict.items():
        print(f"{key}: {value}")
    '''

    for freq in song_dict:
        #print(freq)
        if freq != least_freq:

            for song in song_dict[freq]:
                track_ids.append(song[0])
                #print(song[0])
    #print(song_dict[least_freq])
    if count == num_songs:
        for song in song_dict[least_freq]:
            track_ids.append(song[0])

    else:
        no_songs = num_songs - len(track_ids)
        req_songs = get_low_freq(song_dict[least_freq],no_songs) 
        track_ids.extend(req_songs)

    return track_ids


def get_low_freq(song_deet,no_songs):
    artist_freq = open(config.ARTIST_LOG_FILE,'r')
    eye = csv.reader(artist_freq)
    next(eye)

    req_songs = []
    freq_songs = {}
    count = no_songs

    for row in eye:
        for deet in song_deet:
            if row[0] == deet[1]:
                freq = int(row[1])
                #freq_songs[int(row[1])] = deet[0]
                #freq_songs[deet[0]] = int(row[1])
    
                if freq in freq_songs:
                    freq_songs[freq].append(deet[0])
                else:
                    freq_songs[freq] = [deet[0]]
        
                count -= 1
                break
        if count == 0:
            break

    artist_freq.close()
    #freq_songs = sort_freq(freq_songs)
    '''
    for key, value in freq_songs.items():
        print(f"{key}: {value}")
    '''

    random_order(freq_songs)
    count = 0
    for freq in freq_songs:
        for song in freq_songs[freq]:
            if count < no_songs:
                req_songs.append(song)
                count += 1

    return req_songs

def random_order(song_dict):
    for freq in song_dict:
        random.shuffle(song_dict[freq])

def create_playlist(sp,user_id):
    try:
        (song_dict,count) = get_songs()
        playlist_songs = final_songs(song_dict,count)
        playlist_name = 'the better On Repeat'

        if if_playlist_exists(sp,playlist_name):
            playlist_id = get_playlist_id_by_name(sp,playlist_name)
            sp.playlist_replace_items(playlist_id,playlist_songs)
        else:
            sp.user_playlist_create(user=user_id,name=playlist_name,public=True)
            playlist_id = get_playlist_id_by_name(sp,playlist_name)
            sp.user_playlist_add_tracks(user_id,playlist_id,playlist_songs)
        print('_________ ADDED SONGS TO ON REPEAT PLAYLIST ______')
    except spotipy.SpotifyException as e:
        if e.http_status == 403:
            logger.error("Insufficient permissions to create playlist")
        else:
            logger.error(f"Playlist creation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating playlist: {e}")
        return None





            
'''
        for key, value in freq_songs.items():
            print(f"{key}: {value}")
'''





'''
steps when count > 30

1. check the least freq list 
2. get the song for the most frequent artist from there 
3. if 2 or more songs have same artist freq - put those in a sep list 
4. get a random song from that sep list 
'''           

'''
        while results:
            all_playlists.extend(results['items'])

            if results['next']:
                results = sp.next(results)
            else:
                break
        
        for playlist in all_playlists:
            print(playlist['name'])

'''