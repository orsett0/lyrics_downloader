#!/usr/bin/env python3

import click, os, sys, html
import requests as req
from loguru import logger

base_link = "https://genius.com"

def getLinkName(name):
    return name.replace("(", "").replace(")", "").replace("&", "and").replace(" ", "-").replace(".", '.')

def getValidFilename(name):
    invalid = '!\"$%#/\0'
    return "".join([ c for c in name if c not in invalid ])

def getArtistPage(artist):
    logger.debug(f"making request to {base_link}/artists/{getLinkName(artist)}")
    return req.get(f"{base_link}/artists/{getLinkName(artist)}").text

def getAlbumsList(artist_page):
    logger.info("Searching for albums...")

    pattern = 'class="vertical_album_card"'
    name_pos = 3

    if artist_page.find("/artists/albums?for_artist_page=") != -1:
        logger.debug("artist has more than 6 albums, loading albums list page")
        
        albums_list_link = artist_page[artist_page.find("/artists/albums?for_artist_page="):].split('"')[0]
        
        logger.debug(f"making request to {base_link}/{albums_list_link}")
        artist_page = req.get(f"{base_link}{albums_list_link}").text

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

def getSongsList(album):
    logger.debug(f"getting songs list for {album['name']}")

    songs = []

    logger.debug(f"Making request to {album['link']}")
    album_page = req.get(album['link']).text
    
    pattern = "u-display_block"
    logger.debug(f"number of songs found: {album_page.count(pattern)}")
    for i in range(album_page.count(pattern)):
        useful = album_page[album_page[:album_page.find(pattern)].rfind("href"):]

        try: song_name = getValidFilename(useful.split(">")[2].split("<")[0].strip())
        except IndexError: pass
        try: song_page_link = useful.split('\"')[1]
        except IndexError: pass
        # ! I DONT FKING KNOW WHY IT THROWS AN INDEXERROR BUT IT STILL WORKS SO FCK IT

        songs.append({
            'name': song_name,
            'link': song_page_link
        })

        album_page = useful[useful.find(pattern) + 1:]
    
    return songs

def downloadSong(song_page_link):
    logger.debug(f"making request to {song_page_link}")
    song_page = req.get(song_page_link).text

    pattern = '<div data-lyrics-container="true"'
    lyrics = ''

    for i in range(song_page.count(pattern)):
        song_page = song_page[song_page.find(pattern):]
        part = song_page[:song_page.find('</div>')]

        for element in part.split('>'): 
            if element.split('<')[0] != "": lyrics += f"\n{element.split('<')[0]}"

        song_page = song_page[2:]

    return html.unescape(lyrics)

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

    artist_page = getArtistPage(artist)
    albums_list = getAlbumsList(artist_page)

    for album_data in albums_list:
        if album is not None and getLinkName(album) != getLinkName(album_data['name']): continue
        logger.info(f"downloading album {album_data['name']}...")

        os.makedirs(f"lyrics/{artist}/{album_data['name']}", exist_ok = True)

        songs = getSongsList(album_data)
        for song_data in songs:
            if song is not None and getLinkName(song) != getLinkName(song_data['name']): continue
            logger.debug(f"Downloading song {song_data['name']}")

            lyrics = downloadSong(song_data['link'])
            with open(f"lyrics/{artist}/{album_data['name']}/{song_data['name']}.txt", 'w') as file:
                file.write(lyrics)

if __name__ == '__main__': main()