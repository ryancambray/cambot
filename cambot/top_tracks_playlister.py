#!/usr/bin/env python
import datetime
import logging

import config
import cambot_utils as utils
import argparse
from collections import defaultdict, OrderedDict

add_to_database = False
TWEET = True


# We run this on the first day of each month in the early hours of the morning, so the month we actually want to
# insert into the playlist name is the previous month
def get_current_month():
    now = datetime.datetime.now()
    month = now.month
    if (month == 1):
        month = "December"
    elif (month == 2):
        month = "January"
    elif (month == 3):
        month = "February"
    elif (month == 4):
        month = "March"
    elif (month == 5):
        month = "April"
    elif (month == 6):
        month = "May"
    elif (month == 7):
        month = "June"
    elif (month == 8):
        month = "July"
    elif (month == 9):
        month = "August"
    elif (month == 10):
        month = "September"
    elif (month == 11):
        month = "October"
    elif (month == 12):
        month = "November"
    return month


def get_correct_year():
    now = datetime.datetime.now()
    year = now.year
    month = now.month

    if month == 1:
        return year - 1
    return year


def turn_time_range_into_english_sentence(time_range):
    if time_range == 'short_term':
        time_range = get_current_month()
    elif time_range == 'medium_term':
        time_range = "the last 6 months"
    else:
        time_range = "the last few years"
    return time_range


def create_playlist(time_range, limit):
    if time_range == 'short_term':
        playlist_name = "Top tracks of {} {}".format(get_current_month(), get_correct_year())
    elif time_range == 'medium_term':
        playlist_name = "Top tracks of the last 6 months as of {} {}".format(get_current_month(),
                                                                             get_correct_year())
    else:
        playlist_name = "Top tracks over the last few years as of {} {}".format(get_current_month(),
                                                                                get_correct_year())

    # Create a new playlist
    playlist = utils.sp.user_playlist_create(user=config.spotify_username, name=playlist_name, public=True)
    playlist_id = playlist.get('uri')

    # Get top tracks from the chosen time range and the limit
    top_tracks = utils.sp.current_user_top_tracks(time_range=time_range, limit=limit)

    list_of_tracks_to_add = []
    some_artists = []

    # Iterate through the tracks to get the relevant information
    for track in top_tracks['items']:

        # Store a list of artists to involve in the tweet
        artist = track['artists'][0].get('name')
        if artist not in some_artists:
            some_artists.append(artist)

        list_of_tracks_to_add.append(track['uri'])

    utils.sp.playlist_add_items(playlist_id=playlist_id, items=list_of_tracks_to_add)

    playlist_link_url = playlist['external_urls']
    playlist_link_url = playlist_link_url.get('spotify')
    tweet_str = "Here's a spotify playlist of my most listened to songs in {}\n{}\n\nThis includes artists such as: ".format(
        turn_time_range_into_english_sentence(time_range), playlist_link_url)
    for artist in some_artists:
        if len(tweet_str) + len(artist) <= 280:
            tweet_str += artist + ", "
    tweet_str = tweet_str[:-2] + "."
    logging.info(tweet_str)
    if TWEET:
        utils.api.update_status(status=tweet_str)


def check_number(value):
    ivalue = int(value)
    if ivalue <= 0 or ivalue > 50:
        raise argparse.ArgumentTypeError("%s is an invalid int value. The limit is between 1 and 50" % value)
    return ivalue


parser = argparse.ArgumentParser()
parser.add_argument("-t", "--timeframe",
                    help="Creates a playlist of the top songs from the past month, 6 months or years.",
                    choices=['short_term', 'medium_term', 'long_term'])
parser.add_argument("--limit", help="Specify how many tracks you want in the playlist", default=50, type=check_number)
parser.add_argument("--tweet",
                    help="If this has been entered, then the script will NOT tweet to the account provided.",
                    action="store_true")
parser.add_argument("-a", "--at",
                    help="Include this at runtime to replace mentions of artists names with their twitter handles. If add is selected, you will be prompted to enter twitter handles of the corresponding artist if it was not found in the database.",
                    default="leave", choices=['add', 'leave'])
args = parser.parse_args()

time_range = args.timeframe
limit = int(args.limit)
add = args.at
tweet = args.tweet

if add == 'add':
    logging.debug("adding artist names to the database.", flush=True)
    add_to_database = True

if tweet:
    logging.info("TEST MODE: not tweeting to the account provided")
    TWEET = False

create_playlist(time_range, limit)
