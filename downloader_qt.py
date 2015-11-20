#!/usr/bin/python3

import sys
import json
import os
import requests
import re
import urllib.request
from PyQt5.QtWidgets import QApplication, QComboBox, QGridLayout, QWidget, QLabel, QFileDialog, QPushButton, \
    QMessageBox, QDialog, QLineEdit

DOWNLOAD_FORMATS = dict(
        WAV="?format=wav",
        MP3_320="?format=mp3&bitRate=320",
        MP3_V0="?format=mp3&quality=0",
        MP3_V2="?format=mp3&quality=2",
        MP3_128="?format=mp3&bitRate=128",
        FLAC="?format=flac"
)
SIGNIN_URL = "https://connect.monstercat.com/signin"
DOWNLOAD_BASE = "https://connect.monstercat.com/album/"


class SignInDialog(QDialog):
    username = None
    password = None
    session = None
    downloader = None

    def __init__(self, downloader):
        super().__init__()
        self.init_ui()
        self.session = downloader.session
        self.downloader = downloader

    def init_ui(self):
        grid = QGridLayout()
        self.setLayout(grid)
        self.setWindowTitle("Log-In to Monstercat Connect")

        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        login = QPushButton("Login")
        login.pressed.connect(self.login)

        grid.addWidget(QLabel("E-Mail: "), *(1, 1))
        grid.addWidget(self.username, *(1, 2))
        grid.addWidget(QLabel("Password: "), *(2, 1))
        grid.addWidget(self.password, *(2, 2))
        grid.addWidget(login, *(3, 2))

    def login(self):
        print("Signing in...")
        payload = {"email": self.username.text(), "password": self.password.text()}
        response_raw = self.session.post(SIGNIN_URL, data=payload)
        response = json.loads(response_raw.text)
        if len(response) > 0:
            show_popup("Sign-In failed!", "Sign-In Error: " + response.get("message", "Unknown error"))
            return False
        self.close()
        show_popup("Sign-In successful!", "You are successfully logged in!")
        self.downloader.loggedIn = True
        return True


def show_popup(title, text):
    msgbox = QMessageBox()
    msgbox.setWindowTitle(title)
    msgbox.setText(text)
    msgbox.exec_()


def save_url(url, path, cj):
    print("TELL THE DEV TO CHANGE THIS!!")
    print("Downloading " + url)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    r = opener.open(urllib.request.quote(url, safe="%/:=&?~#+!$,;'@()*[]"))
    output = open(path, "wb")
    output.write(r.read())
    output.close()
    print("Downloaded to " + path)


def download_file(url, path, session):
    # NOTE the stream=True parameter
    r = session.get(url, stream=True)
    filename = path + "/" + (str.replace(re.findall("filename=(.+)", r.headers['content-disposition'])[0], "\"", ""))
    print(filename)
    diff = (100/int(r.headers['Content-Length']))
    count = 0
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                # print("new chunk")
                f.write(chunk)
                print(count*1024*diff)
                count += 1
                # f.flush() commented by recommendation from J.F.Sebastian
    return filename


class Downloader(QWidget):
    combobox = None
    grid = None
    selected_file = None
    session = None
    loggedIn = False

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.init_ui()

    def init_ui(self):
        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.combobox = QComboBox()
        download_qualities = [
            ("WAV", "?format=wav"),
            ("MP3 320", "?format=mp3&bitRate=320"),
            ("MP3 V0", "?format=mp3&quality=0"),
            ("MP3 V2", "?format=mp3&quality=2"),
            ("MP3 128", "?format=mp3&bitRate=128"),
            ("FLAC", "?format=flac")
        ]
        for i in range(len(download_qualities)):
            self.combobox.addItem(download_qualities[i][0], download_qualities[i][1])

        openbutton = QPushButton("Select file")
        openbutton.clicked.connect(self.show_dialog)

        download_button = QPushButton("Download")
        download_button.clicked.connect(self.download)

        # ADD WIDGETS
        self.grid.addWidget(QLabel("Select your quality: "), *(1, 1))
        self.grid.addWidget(self.combobox, *(1, 2))
        self.grid.addWidget(QLabel("Please select your JSON file: "), *(2, 1))
        self.grid.addWidget(openbutton, *(2, 2))
        self.grid.addWidget(QLabel(""), *(3, 1))
        self.grid.addWidget(download_button, *(4, 2))

        self.move(300, 150)
        self.setWindowTitle('MonstercatConnectDownloader')
        self.show()

    def show_dialog(self):
        filepicker = QFileDialog.getOpenFileName(self, 'Open file', os.path.expanduser("~"), "JSON file (*.json)")
        if filepicker[0]:
            self.selected_file = filepicker[0]

    def show_sign_in_dialog(self):
        dialog = SignInDialog(self)
        dialog.exec_()

    def download(self):
        # GET FILE
        if not self.selected_file:
            show_popup("Error", "Please select a file first.")
            return False
        with open(self.selected_file) as f:
            album_ids = json.loads(f.read())

        save_dir = QFileDialog.getExistingDirectory(self, "Select folder to download", os.path.expanduser("~"))

        # GET SELECTED QUALITY
        quality = self.combobox.currentData()

        # GET SESSION
        if not self.loggedIn:
            self.show_sign_in_dialog()

        # CHECK IF LOGIN SUCESSFUL
        if not self.loggedIn:
            show_popup("Error", "Login failed.")
            return

        # DOWNLOAD
        for album_id in album_ids:
            download_link = DOWNLOAD_BASE + album_id + "/download" + quality
            download_file(download_link, save_dir, self.session)
            break

        show_popup("Success!", "Download finished!")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dl = Downloader()
    sys.exit(app.exec_())
