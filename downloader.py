#!/usr/bin/env python3
#
# Copyright (C) 2022 Alessio Orsini <alessiorsini.ao@proton.me>
# SPDX-License-Identifier: GPL-3.0-or-later
#

import click, os, sys, html, time
import requests as req
from loguru import logger

base_link = "https://genius.com"
time_from_last_get = 0

# I'm not using any API, and i don't really wont to overload the server.
# Even if I don't think that's gonna happen, you never know.
def get(link):
    logger.debug(f"making request to {link}")

    global time_from_last_get
    while time.time() * 1000 < time_from_last_get + 200: # Maybe 200ms is too mutch?
        time.sleep(0.01)

    res = req.get(link)
    time_from_last_get = int(time.time() * 1000)

    return res

# This replaces some characters from a string to match the pattern I saw used in genius links.
# I did not test this quite enough to see if this gets it always right.
def getLinkName(name):
    if name is None: return ""
    return name.replace("(", "").replace(")", "").replace("&", "and").replace(" ", "-").replace(".", '-')

# Simply strips invalid (linux) file name character from the string
def getValidFilename(name):
    invalid = '!\"$%#/\0'
    return "".join([ c for c in name if c not in invalid ])

# Parses the artist page to get a list of the albums.
def getAlbumsList(artist_page):
    logger.info("Searching for albums...")

    pattern = 'class="vertical_album_card"'
    name_pos = 3

    # if the artist has less than six albums, they will all be showed in the preview,
    # but if they're more then a page will be generated and I'll need to search trough that.
    if artist_page.find("/artists/albums?for_artist_page=") != -1:
        logger.debug("artist has more than 6 albums, loading albums list page")
        
        albums_list_link = artist_page[artist_page.find("/artists/albums?for_artist_page="):].split('"')[0]
        artist_page = get(f"{base_link}{albums_list_link}").text

        pattern = 'class="album_link"'
        name_pos = 4
    
    albums_list = []
    for i in range(artist_page.count(pattern)):
        useful = artist_page[artist_page[:artist_page.find(pattern)].rfind("href="):].split('"')

        albums_list.append({
            'name': getValidFilename(useful[name_pos].split("<")[0].replace(">", "")),
            'link': ("" if base_link in useful[1] else base_link) + useful[1] 
        })

        artist_page = artist_page[artist_page.find(pattern) + 1:]
    
    logger.debug(f"Number of albums found: {len(albums_list)}")
    return albums_list

# For every album page, this returns a list of all the songs.
def getSongsList(album):
    logger.debug(f"getting songs list for '{album['name']}'")

    album_page = get(album['link']).text

    songs = []    
    pattern = "u-display_block"
    logger.debug(f"number of songs found: {album_page.count(pattern)}")
    for i in range(album_page.count(pattern)):
        useful = album_page[album_page[:album_page.find(pattern)].rfind("href"):]

        try: song_name = getValidFilename(useful.split(">")[2].split("<")[0].strip())
        except IndexError: pass
        try: song_page_link = useful.split('\"')[1]
        except IndexError: pass
        # ! I DONT FKING KNOW WHY IT THROWS AN INDEXERROR BUT IT STILL WORKS SO FCK IT
        # Maybe Ishould test this to see what is going wrong

        songs.append({
            'name': song_name,
            'link': song_page_link
        })

        album_page = useful[useful.find(pattern) + 1:]
    
    return songs

# This parses the songs page to estrapolate the lyrics.
def downloadSong(song_page_link):
    song_page = get(song_page_link).text

    pattern = '<div data-lyrics-container="true"'
    lyrics = ''

    for i in range(song_page.count(pattern)):
        song_page = song_page[song_page.find(pattern):]
        part = song_page[:song_page.find('</div>')]

        for element in part.split('>'): 
            if element.split('<')[0] != "": lyrics += f"\n{element.split('<')[0]}"

        song_page = song_page[2:]

    return html.unescape(lyrics)

# Checks an album or song against the one the user specified (if any)
# returns true if there's a match
def choosenOne(test, ctrl):
    return ctrl is None or getLinkName(ctrl).upper() == getLinkName(test).upper()

@click.command()
@click.option(
    "--artist",
    "-a",
    help = "Artist's name",
    type = click.STRING
)
@click.option(
    "--album",
    "-A",
    help = "album to download",
    type = click.STRING,
    default = None
)
@click.option(
    "--song",
    "-s",
    help = "Song to download",
    type = click.STRING,
    default = None
)
@click.option(
    "--debug",
    "-d",
    is_flag = True,
    default = False
)

def main(artist: str, album: str, song: str, debug: bool):
    logger.remove()
    logger.add(
        sys.stdout, 
        colorize=True, 
        format = "<green>{time:YY.MM.DD HH:mm:ss}</green> - <level>{level}</level>: {message}", 
        level = 'DEBUG' if debug else 'INFO'
    )

    flag = False

    artist_page = get(f"{base_link}/artists/{getLinkName(artist)}").text
    albums_list = getAlbumsList(artist_page)

    print(albums_list)

    if len(albums_list) == 0:
        logger.warning("No album found. Check your parameters. (or the code, idk)")
        return

    for album_data in albums_list:
        if not choosenOne(album_data['name'], album): continue
        logger.info(f"downloading album '{album_data['name']}'...")

        os.makedirs(f"lyrics/{artist}/{album_data['name']}", exist_ok = True)

        songs = getSongsList(album_data)
        for song_data in songs:
            if not choosenOne(song_data['name'], song): continue
            logger.debug(f"Downloading song '{song_data['name']}'")
            flag = True

            lyrics = downloadSong(song_data['link'])
            with open(f"lyrics/{artist}/{album_data['name']}/{song_data['name']}.txt", 'w') as file:
                file.write(lyrics)
    
    if not flag:
        logger.warning("No song downloaded. Check your parameters. (or the code, idk)")

if __name__ == '__main__': main()