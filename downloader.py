#!/usr/bin/env python3

import click, os, sys, html
import requests as req
from loguru import logger

base_link = "https://genius.com"

def getLinkName(name):
    return name.replace("(", "").replace(")", "").replace("&", "and").replace(" ", "-")

def getValidFilename(name):
    invalid = '!\"$%#/\0'
    return "".join([ c for c in name if c not in invalid ])

@click.command()
@click.option(
    "--artist",
    "-a",
    help = "Nome dell'artista",
    type = click.STRING
)
@click.option(
    "--debug",
    "-d",
    is_flag = True,
    default = False
)

def main(artist: str, debug: bool):
    logger.remove()
    logger.add(
        sys.stdout, 
        colorize=True, 
        format = "<green>{time:YY.MM.DD HH:mm:ss}</green> - <level>{level}</level>: {message}", 
        level = 'DEBUG' if debug else 'INFO'
    )

    try: os.mkdir(artist)
    except FileExistsError: pass

    logger.debug(f"making request to {base_link}/artists/{getLinkName(artist)}")
    artist_page = req.get(f"{base_link}/artists/{getLinkName(artist)}").text
    albums_list_link = artist_page[artist_page.find("/artists/albums?for_artist_page="):].split('\"')[0]


    logger.debug(f"making request to {base_link}/{albums_list_link}")
    albums_list_page = req.get(f"{base_link}{albums_list_link}").text
    pattern = '<li><a href=\"/albums/'
    logger.debug(f"Number of '{pattern}' found: {albums_list_page.count(pattern)}")

    logger.info("Searching for albums...")
    albums_list = []
    for i in range(albums_list_page.count(pattern)):
        useful = albums_list_page[albums_list_page.find(pattern):]

        albums_list.append({
            'name': getValidFilename(useful.split('>')[2].split('<')[0]),
            'link': useful.split('\"')[1]
        })

        logger.debug(f"found album {albums_list[-1]['name']}")
        albums_list_page = useful[2:]

    for album in albums_list:
        logger.info(f"downloading album {album['name']}...")

        try: os.mkdir(f"{artist}/{album['name']}")
        except FileExistsError: pass
        album_page = req.get(f"{base_link}{album['link']}").text

        pattern = "u-display_block"
        logger.debug(f"number of '{pattern}' found: {album_page.count(pattern)}")
        for i in range(album_page.count(pattern)):
            useful = album_page[album_page[:album_page.find(pattern)].rfind("href"):]

            try: 
                song_name = getValidFilename(useful.split(">")[2].split("<")[0].strip())
                song_page_link = useful.split('\"')[1]
            except IndexError:
                # ! I DONT FKING KNOW WHY IT THROWS AN INDEXERROR BUT IT STILL WORKS SO FCK IT
                pass

            logger.debug(f"making request to {song_page_link}")
            song_page = req.get(song_page_link).text

            with open(f"{artist}/{album['name']}/{song_name}.txt", 'w') as file:
                lyrics = ''
                for i in range(song_page.count('<div data-lyrics-container="true"')):
                    song_page = song_page[song_page.find('<div data-lyrics-container="true"'):]
                    part = song_page[:song_page.find('</div>')]

                    for element in part.split('>'): 
                        if element.split('<')[0] != "": lyrics += f"\n{element.split('<')[0]}"

                    song_page = song_page[2:]

                file.write(html.unescape(lyrics))

            #logger.debug(f"pattern: {pattern}, useful[useful.find(pattern) + 1:102]: {useful[useful.find(pattern) + 1:102]}")
            album_page = useful[useful.find(pattern) + 1:]


if __name__ == '__main__': main()