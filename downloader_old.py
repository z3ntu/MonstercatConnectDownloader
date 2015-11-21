#!/usr/bin/python3

import json
import config
import os
import urllib.request
import http.cookiejar
import sys
import requests
from time import strftime

SIGNIN_URL = "https://connect.monstercat.com/signin"
COVER_ART_BASE = "https://connect.monstercat.com/img/labels/monstercat/albums/"
DATA_PATH = os.path.expanduser('~/.monstercatconnectdownloader/')
TMP_PATH = DATA_PATH + "tmp/"
COOKIE_FILE = DATA_PATH + "connect.cookies"
LOG_FILE = DATA_PATH + "output.log"

DOWNLOAD_BASE = "https://connect.monstercat.com/album/"

DOWNLOAD_FORMATS = dict(
    WAV="?format=wav",
    MP3_320="?format=mp3&bitRate=320",
    MP3_V0="?format=mp3&quality=0",
    MP3_V2="?format=mp3&quality=2",
    MP3_128="?format=mp3&bitRate=128",
    FLAC="?format=flac"
)

# temp
LOG = sys.__stdout__

REMOVED_COOKIE_FILE = False


def main():
    # create_directories()
    album_ids = load_from_json(os.getcwd() + "/monstercatconnect.json")
    for album_id in album_ids:
        download_link = DOWNLOAD_BASE + album_id + "/download" + DOWNLOAD_FORMATS["MP3_128"]
        session = requests.Session()
        sign_in(session)
        save_url(download_link, os.getcwd() + "/download.zip", session.cookies)
        break


def sign_in(session):
    log("Signing in...")
    payload = {"email": config.connect['email'], "password": config.connect['password']}
    response_raw = session.post(SIGNIN_URL, data=payload)
    response = json.loads(response_raw.text)
    if len(response) > 0:
        log("Sign in failed")
        raise Exception("Sign-In Error: " + response.get("message", "Unknown error"))


def create_directories():
    # log("Creating directories...")
    os.makedirs(DATA_PATH, exist_ok=True)
    os.makedirs(TMP_PATH, exist_ok=True)


def save_cookies(cj, filename):
    log("Saving cookies")
    cj.save(filename=filename)


def load_cookies(filename):
    log("Loading cookies")
    cj = http.cookiejar.MozillaCookieJar()
    if not os.path.isfile(filename):
        return cj, False
    cj.load(filename=filename)
    return cj, True


def load_from_json(path):
    content = open(path, "r").read()
    return json.loads(content)


def save_url(url, path, cj):
    log("Downloading " + url)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    r = opener.open(urllib.request.quote(url, safe="%/:=&?~#+!$,;'@()*[]"))
    output = open(path, "wb")
    output.write(r.read())
    output.close()
    log("Downloaded to " + path)


def save_url_new(url, session):
    log("not implemented yet")


def log(message):
    print("[" + strftime("%Y-%m-%d %H:%M:%S") + "] " + message)


if __name__ == '__main__':
    main()
