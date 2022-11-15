# Lyrics Downloader

Script to download music lyrics from [genius](https://genius.com/). It doesn't use genius' API, so it can work without any particular configuration. <br>
To download the lyrics, you can either simply specify an artist, or his album or song. <br>
**Note that to download the lyrics of a single song it is necessary to specify both the artist and the album to which it belongs (the same goes for a single album).**

## Installation

There's really nothing mutch to do. Just download the code and install the requirements with

    git clone https://github.com/orsetto42/lyrics_downloader.git
    cd lyrics_downloader
    pip install -r requirements.txt

## Use

If you specify only the artist name, this program will download all the lyrics of that artist that it can find on genius. <br>
You can also specify an album to download only the lyrics from that album, or a song to download only that song. <br>
You also need to specify names between quotation marks if they contain spaces or special characters. This program tries to convert names in a way that they are accepted from genius, but it may fail. I'm working on it.

## Plans for the future

Nothing special. Just add the possibility to pass directly a link as a parameter (for songs, albums, or artists).

**DISCLAIMER: if you're looking into the code and it looks bad, I know. I wrote this at 3AM and the next day i tried to clean it but it looks bad to me too.**