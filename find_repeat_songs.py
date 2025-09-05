import csv 
from utils import sort_freq
import config

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_file():
    freq_log = open(config.FREQ_LOG_FILE,'w',newline='')
    pen = csv.writer(freq_log)
    pen.writerow(['Track ID','Track Name','Artist Name','Frequency'])
    freq_log.close()

def get_freq():
    try:
        songs_dict = {}
        track_log = open(config.TRACK_LOG_FILE,'r')
        eye = csv.reader(track_log)
        next(eye)
        for row in eye:
            track_deet = (row[2],row[3],row[4])
            if track_deet in songs_dict:
                songs_dict[track_deet] += 1
            else:
                songs_dict[track_deet] = 1

        track_log.close()
        freq_log = open(config.FREQ_LOG_FILE,'a',newline='')
        pen = csv.writer(freq_log)
        
        artist_freq(songs_dict)
        keys = sort_freq(songs_dict,1)
        for key in keys:
            pen.writerow([key[0],key[1],key[2],songs_dict[key]])

    except FileNotFoundError:
        logger.error("Track Log file not found")
        return False
    except csv.Error as e:
        logger.error(f"CSV parsing error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error processing frequency data: {e}")
        return False

'''
input - dictionary containing the track details with its corresponding frequency 
output - new dictionary containing artist name and their corresponding frequency 

func counts the number of times any song by every artist is played by user 
'''
def artist_freq(songs_dict):

    count_artist = {}
    for deet_tuple in songs_dict:
        artist_name = deet_tuple[2]
        if artist_name not in count_artist:
            count_artist[artist_name] = songs_dict[deet_tuple]
        else:
            count_artist[artist_name] += songs_dict[deet_tuple]
    
    artist_log = open(config.ARTIST_LOG_FILE,'w',newline = '')
    pen = csv.writer(artist_log)
    pen.writerow(['Artist Name','Frequency'])
    keys = sort_freq(count_artist,1)
    for key in keys:
        pen.writerow([key,count_artist[key]])

    artist_log.close()
