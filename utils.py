
'''
from main import authenticate
sp = authenticate()
'''
# playlist id from name 
#playlist_id = get_playlist_id_by_name("Test Playlist") 

def get_playlist_id_by_name(sp,name):
    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        if playlist['name'].lower() == name.lower():
            return playlist['id']
    return None

'''
input - dictionary containing the track details with its corresponding frequency 
output - sorted list of the track details in the descending order of frequency 
'''

def sort_freq(freq_dict,cond=0):
    sorted_dict = dict(sorted(freq_dict.items(), key=lambda kv: (kv[1], kv[0]),reverse=True))
    if cond == 1:
        return(list(sorted_dict.keys()))
    else:
        return(sorted_dict)
