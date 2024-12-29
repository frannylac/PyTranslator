#!/usr/bin/python3.8
# -*- coding: utf-8 -*-

import base64
import pyautogui
import pyperclip
import tkinter as tk
from io import BytesIO
from PIL import Image, ImageTk
from pydub import AudioSegment
from pydub.playback import play as playAudio
# from pynput.mouse import Button, Listener
from os.path import exists
from time import sleep, time
from tkinter import messagebox
from requests import get
from requests.exceptions import ReadTimeout
from sys import argv
from urllib.parse import quote

G_SUPPORTED_LANGUAGES_FILE = 'languages.txt'
G_DEFAULT_LANG_FROM = 'English'
G_DEFAULT_LANG_TARGET = 'Spanish'
ICONS_FOLDER = 'icons/'

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def error(msg: str, quit: bool=True, quiet: bool=False) -> None:
    '''Print error message and exit (code 1)'''
    if not quiet:
        print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {msg}")
    if quit:
        exit(1)

def info(msg: str, quiet: bool=False) -> None:
    '''Print info message'''
    if not quiet:
        print(f"{Colors.OKCYAN}[INFO]{Colors.ENDC} {msg}")

def load_supported_langs() -> dict:
    '''Reads G_SUPPORTED_LANGUAGES_FILE or die.
    {long: short} e.g: {"English": "en"}'''
    global G_SUPPORTED_LANGUAGES_FILE
    
    if not exists(G_SUPPORTED_LANGUAGES_FILE):
        error(f"File '{G_SUPPORTED_LANGUAGES_FILE}' do not exists!")

    with open(G_SUPPORTED_LANGUAGES_FILE, 'r') as f:
        return dict([(l.split('|')[1], l.split('|')[0]) for l in f.read().split("\n")])

# class MouseLeftClick:
#     '''Listen mouse left click.'''

#     def __init__(self):
#         self._doubleClickTimeMargin = 0.3 # seconds
#         self._lastClickAt = 0
#         self._leftClickCallback = lambda x,y: None
#         self._doubleLeftClickCallback = lambda x,y: None

#     def _on_click(self, x, y, button, pressed):
#         '''Detect mouse events.
#         - Left double click'''
#         if pressed and button == Button.left:
#             clickAt = time()

#             # Reset last click time
#             if clickAt - self._lastClickAt > self._doubleClickTimeMargin:
#                 self._lastClickAt = 0

#             # Register first click
#             if self._lastClickAt == 0:
#                 self._lastClickAt = clickAt
#                 self._leftClickCallback(x, y)
#                 return

#             # Register second click
#             if clickAt - self._lastClickAt < self._doubleClickTimeMargin:
#                 self._lastClickAt = 0
#                 self._doubleLeftClickCallback(x, y)
#                 return

#     def setLeftClickCallback(self, cb):
#         self._leftClickCallback = cb

#     def setDoubleLeftClickCallback(self, cb):
#         self._doubleLeftClickCallback = cb

#     def listen(self):
#         l = Listener(on_click=self._on_click)
#         l.start()
#         l.join()


class GTranslatorError(Exception):
    pass


class Translation:
    '''Represents a translation from Google Translate.'''

    def __init__(self, gto: dict):
        self.translation:str = gto["translation"]
        self.original:str = gto["sentences"][0]["orig"]
        self.sourceLanguage:str = gto["sourceLanguage"]

    def __str__(self):
        return self.translation


class TranslationSpeech:
    '''Represents a translation speech from Google Translate.'''
    _AUDIO_FORMAT = 'mp3'

    def __init__(self, content: dict):
        self._audio = AudioSegment.from_file(
                BytesIO(base64.b64decode(content["audioContent"])),
                TranslationSpeech._AUDIO_FORMAT
            )

    def play(self):
        playAudio(self._audio)


class GTranslator:
    '''Google Tranlater implementation from Chromium based extension.'''
    _TRANSLATE_API_URL = 'https://translate-pa.googleapis.com/v1/translate'
    _TRANSLATE_API_KEY = 'AIzaSyDLEeFI5OtFBwYBIoK_jj5m32rZK5CkCXA'
    _SPEECH_API_URL = 'https://translate-pa.googleapis.com/v1/textToSpeech'
    _SPEECH_API_KEY = 'AIzaSyDLEeFI5OtFBwYBIoK_jj5m32rZK5CkCXA'
    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    MAX_CHARS = 200

    def __init__(self, sourceLang: str = "auto", targetLang:str = "es"):
        # Default parameters
        self.displayLanguage = "en-US" # ISO 639-1: https://www.andiamo.co.uk/resources/iso-language-codes/
        self.sourceLang = sourceLang
        self.targetLanguage = targetLang

    def query(self, text) -> Translation:
        """Request a translation."""
        url = GTranslator._TRANSLATE_API_URL + '?' \
            + 'params.client=gtx' \
            + f"&query.source_language={self.sourceLang}" \
            + f"&query.target_language={self.targetLanguage}" \
            + f"&query.display_language={self.displayLanguage}" \
            + f"&query.text={quote(text)}" \
            + f"&key={GTranslator._TRANSLATE_API_KEY}" \
            + '&data_types=TRANSLATION' \
            + '&data_types=SENTENCE_SPLITS' \
            + '&data_types=BILINGUAL_DICTIONARY_FULL'
        headers = {'content-type': 'application/json', 'user-agent': GTranslator.USER_AGENT}
        try:
            with get(url, headers=headers, timeout=30) as r:
                if r.status_code == 200:
                    return Translation(r.json())
                else:
                    raise GTranslatorError(f"Error HTTP {r.status_code}: {r.text}")
        except ReadTimeout:
            raise GTranslatorError(f"Error: Conection timeout!")

    def speech(self, text: str, language:str = "end", speed: int=1):
        '''Request text to speech from Google Translate'''
        if len(text) > GTranslator.MAX_CHARS:
            raise GTranslatorError("Only 200 characters allowed to speech!")

        url = GTranslator._SPEECH_API_URL + '?' \
            + 'client=gtx' \
            + f"&language={language}" \
            + f"&text={quote(text)}" \
            + f"&voice_speed={str(speed)}" \
            + f"&key={GTranslator._SPEECH_API_KEY}"
        headers = {'content-type': 'application/json', 'user-agent': GTranslator.USER_AGENT}
        try:
            with get(url, headers=headers, timeout=30) as r:
                if r.status_code == 200:
                    return TranslationSpeech(r.json())
                else:
                    raise GTranslatorError(f"Error HTTP {r.status_code}: {r.text}")
        except ReadTimeout:
            raise GTranslatorError(f"Error: Conection timeout!")


class ClipboardTranslator:
    '''Use Google Translate to translate text from cliboard'''
    def __init__(self, srcLang: str='en', destLang: str='es') -> None:
        '''
        srcLang: source language to translate from
        destLang: destination language to translate to
        '''
        sleep(1) # FOR AVOID GOOGLE RATE LIMIT
        self._transl = GTranslator(sourceLang=srcLang, targetLang=destLang)

    def _translate(self, text: str) -> str:
        '''Do translate text'''
        return self._transl.query(text).translation

    def run(self)-> None:
        '''Run translation process'''
        while True:
            try:
                # WAIT FOR NEXT TEXT TO TRANSLATE
                text = pyperclip.waitForNewPaste()
                print( f"{Colors.WARNING}[Translating...]{Colors.ENDC}: {text}" )
                try:
                    text = self._translate(text)
                    print( f"{Colors.WARNING}[Result]{Colors.ENDC}: {text}", end='\n\n' )
                except Exception:
                    error(quit=False, msg="Rate limit!\n")
            except KeyboardInterrupt:
                print( f"\nbye" )
                break


class GTranslatorGui:
    '''Small gui for translator'''

    class Txt:
        ERROR = 'Error'
        LANG_FROM = 'From'
        LANG_TO = 'To'
        LISTEN = 'Listen'
        LISTEN_SOURCE = 'Source'
        LISTEN_TRANSLATION = 'Translation'
        TITLE = 'PyTranslator'

    class Colors:
        BACKGROUND = '#212830'
        BUTTON_BACKGROUND = '#2a313c'
        BUTTON_BACKGROUND_ACTIVE = '#2f3742'
        BUTTON_HIGHLIGHT_BACKGROUND = '#3d444d'
        BUTTON_TEXT_COLOR = '#d1d7e0'
        LABEL_TEXT_COLOR = '#d1d7e0'
        OPTION_MENU_BACKGROUND = '#2a313c'
        OPTION_MENU_BACKGROUND_ACTIVE = '#2f3742'
        OPTION_MENU_HIGHLIGHT_BACKGROUND = '#3d444d'
        OPTION_MENU_MENU_BACKGROUND = '#212830'
        OPTION_MENU_MENU_ACTIVE_BACKGROUND = '#d1d7e0'
        OPTION_MENU_MENU_ACTIVE_FOREGROUND = '#212830'
        OPTION_MENU_TEXT_COLOR = '#d1d7e0'
        OPTION_MENU_MENU_TEXT_COLOR = '#d1d7e0'
        TEXT_BACKGROUND = '#2b353f'
        TEXT_COLOR = '#d1d7e0'
        TEXT_TAG_BACKGROUND = '#5F748A'
        TEXT_HIGHLIGHT_BACKGROUND = '#3d444d'

    def __init__(self, x: float=0, y: float=0, origenText: str=""):
        '''Creates a floating window at x,y position.'''
        global G_DEFAULT_LANG_FROM, G_DEFAULT_LANG_TARGET

        self._supportedLangs = load_supported_langs()

        # Icons
        self._iconReload = f"{ICONS_FOLDER}reload.png"
        self._checkIcon(self._iconReload)
        self._iconRepeat = f"{ICONS_FOLDER}repeat.png"
        self._checkIcon(self._iconRepeat)
        self._iconLanguage = f"{ICONS_FOLDER}language.png"
        self._checkIcon(self._iconLanguage)
        self._iconPaste = f"{ICONS_FOLDER}paste.png"
        self._checkIcon(self._iconPaste)

        self._rootSize = (500, 390)
        self._root = tk.Tk()
        self._root.protocol('WV_DELETE_WINDOW', self._on_close)
        # Make floating window
        self._root.wm_attributes('-type', 'dialog')
        self._root.title(GTranslatorGui.Txt.TITLE)
        self._root.resizable(width=False, height=False)

        # Position of window (on dimensions overflow, window is centered at middle of screen)
        if x < 0 or x + self._rootSize[0] > self._root.winfo_screenwidth():
            error(f"X overflow: {x}", False)
            x = int((self._root.winfo_screenwidth() / 2) - (self._rootSize[0] / 2))

        if y < 0 or  y + self._rootSize[1] > self._root.winfo_screenheight():
            error(f"Y overflow: {y}", False)
            y = int((self._root.winfo_screenheight() / 2) - (self._rootSize[1] / 2))

        self._root.geometry(f"{self._rootSize[0]}x{self._rootSize[1]}+{x}+{y}")

        # Main Frame Widget
        self._mainFrame = tk.Frame(self._root)
        self._mainFrame.config(background=GTranslatorGui.Colors.BACKGROUND)
        self._mainFrame.config(height=self._rootSize[1])
        self._mainFrame.config(width=self._rootSize[0])
        self._mainFrame.config(padx=4, pady=4)
        self._mainFrame.place(x=0, y=0)

        # First row
        # ----------------------------------------------------------------------------
        # Input text to translate
        self._sourceText = tk.Text(self._mainFrame)
        self._sourceText.bind('<Control-a>', self._selectAll)
        self._sourceText.bind('<Control-v>', self._paste)
        self._sourceText.bind('<Return>', self._on_keyup_catch_enter)
        self._sourceText.config(background=GTranslatorGui.Colors.TEXT_BACKGROUND)
        self._sourceText.config(border=0)
        self._sourceText.config(font=('Calibri', 14))
        self._sourceText.config(foreground=GTranslatorGui.Colors.TEXT_COLOR)
        self._sourceText.config(highlightbackground=GTranslatorGui.Colors.TEXT_HIGHLIGHT_BACKGROUND)
        self._sourceText.config(highlightcolor=GTranslatorGui.Colors.TEXT_HIGHLIGHT_BACKGROUND)
        self._sourceText.config(highlightthickness=1)
        self._sourceText.config(insertbackground=GTranslatorGui.Colors.TEXT_COLOR)
        self._sourceText.config(padx=4, pady=3)
        self._sourceText.config(relief=tk.FLAT)
        self._sourceText.tag_config('tag', background="red")
        # height: 1 line
        # width: 38 chars
        self._sourceText.config(height=1, width=48)
        self._sourceText.place(x=0, y=2)
        # ----------------------------------------------------------------------------

        # Second row
        # ----------------------------------------------------------------------------
        self._fromLabel = tk.Label(self._mainFrame)
        self._fromLabel.config(background=GTranslatorGui.Colors.BACKGROUND)
        self._fromLabel.config(foreground=GTranslatorGui.Colors.LABEL_TEXT_COLOR)
        self._fromLabel.config(font=('Calibri', 14))
        self._fromLabel.config(padx=8, pady=4)
        self._fromLabel.config(text=GTranslatorGui.Txt.LANG_FROM)
        self._fromLabel.place(x=0, y=43)

        self._sourceLangValue = tk.StringVar()
        self._sourceLangValue.set(G_DEFAULT_LANG_FROM)
        self._sourceLangOM = tk.OptionMenu(
                self._mainFrame,
                self._sourceLangValue,
                *self._supportedLangs.keys(),
                command=self._on_select_optionMenu
            )
        self._sourceLangOM.config(background=GTranslatorGui.Colors.OPTION_MENU_BACKGROUND)
        self._sourceLangOM.config(activebackground=GTranslatorGui.Colors.OPTION_MENU_BACKGROUND_ACTIVE)
        self._sourceLangOM.config(activeforeground=GTranslatorGui.Colors.OPTION_MENU_TEXT_COLOR)
        self._sourceLangOM.config(cursor='hand1')
        self._sourceLangOM.config(foreground=GTranslatorGui.Colors.OPTION_MENU_TEXT_COLOR)
        self._sourceLangOM.config(highlightbackground=GTranslatorGui.Colors.OPTION_MENU_HIGHLIGHT_BACKGROUND)
        self._sourceLangOM.config(highlightthickness=1)
        self._sourceLangOM.config(justify='left')
        self._sourceLangOM.config(font=('Calibri', 14))
        self._sourceLangOM.config(relief=tk.FLAT)
        self._sourceLangOM['menu'].config(background=GTranslatorGui.Colors.OPTION_MENU_MENU_BACKGROUND)
        self._sourceLangOM['menu'].config(foreground=GTranslatorGui.Colors.OPTION_MENU_MENU_TEXT_COLOR)
        self._sourceLangOM['menu'].config(activebackground=GTranslatorGui.Colors.OPTION_MENU_MENU_ACTIVE_BACKGROUND)
        self._sourceLangOM['menu'].config(activeforeground=GTranslatorGui.Colors.OPTION_MENU_MENU_ACTIVE_FOREGROUND)
        self._sourceLangOM.place(x=60, y=42)

        self._toLabel = tk.Label(self._mainFrame)
        self._toLabel.config(background=GTranslatorGui.Colors.BACKGROUND)
        self._toLabel.config(foreground=GTranslatorGui.Colors.LABEL_TEXT_COLOR)
        self._toLabel.config(font=('Calibri', 14))
        self._toLabel.config(padx=8, pady=4)
        self._toLabel.config(text=GTranslatorGui.Txt.LANG_TO)
        self._toLabel.place(x=0, y=83)

        self._targetLangValue = tk.StringVar()
        self._targetLangValue.set(G_DEFAULT_LANG_TARGET)
        self._targetLangOM = tk.OptionMenu(
                self._mainFrame,
                self._targetLangValue,
                *self._supportedLangs.keys(),
                command=self._on_select_optionMenu
            )
        self._targetLangOM.config(activebackground=GTranslatorGui.Colors.OPTION_MENU_BACKGROUND_ACTIVE)
        self._targetLangOM.config(activeforeground=GTranslatorGui.Colors.OPTION_MENU_TEXT_COLOR)
        self._targetLangOM.config(background=GTranslatorGui.Colors.OPTION_MENU_BACKGROUND)
        self._targetLangOM.config(cursor='hand1')
        self._targetLangOM.config(foreground=GTranslatorGui.Colors.OPTION_MENU_TEXT_COLOR)
        self._targetLangOM.config(highlightbackground=GTranslatorGui.Colors.OPTION_MENU_HIGHLIGHT_BACKGROUND)
        self._targetLangOM.config(highlightthickness=1)
        self._targetLangOM.config(font=('Calibri', 14))
        self._targetLangOM.config(relief=tk.FLAT)
        self._targetLangOM['menu'].config(background=GTranslatorGui.Colors.OPTION_MENU_MENU_BACKGROUND)
        self._targetLangOM['menu'].config(foreground=GTranslatorGui.Colors.OPTION_MENU_MENU_TEXT_COLOR)
        self._targetLangOM['menu'].config(activebackground=GTranslatorGui.Colors.OPTION_MENU_MENU_ACTIVE_BACKGROUND)
        self._targetLangOM['menu'].config(activeforeground=GTranslatorGui.Colors.OPTION_MENU_MENU_ACTIVE_FOREGROUND)
        self._targetLangOM.place(x=60, y=82)

        # Switch languages button
        switchIcon = ImageTk.PhotoImage(Image.open(self._iconRepeat))
        self._switchButton = tk.Button(self._mainFrame)
        self._switchButton.config(background=GTranslatorGui.Colors.BACKGROUND)
        self._switchButton.config(activebackground=GTranslatorGui.Colors.BACKGROUND)
        self._switchButton.config(borderwidth=0)
        self._switchButton.config(cursor='hand1')
        self._switchButton.config(highlightthickness=0)
        self._switchButton.config(highlightbackground=GTranslatorGui.Colors.BACKGROUND)
        self._switchButton.config(highlightcolor=GTranslatorGui.Colors.BACKGROUND)
        self._switchButton.config(padx=8, pady=4)
        self._switchButton.config(image=switchIcon)
        self._switchButton.config(command=self._on_click_switchLangs)
        self._switchButton.place(x=321, y=65)

        # Reset button
        reloadIcon = ImageTk.PhotoImage(Image.open(self._iconReload))
        self._resetButton = tk.Button(self._mainFrame)
        self._resetButton.config(background=GTranslatorGui.Colors.BACKGROUND)
        self._resetButton.config(activebackground=GTranslatorGui.Colors.BACKGROUND)
        self._resetButton.config(borderwidth=0)
        self._resetButton.config(cursor='hand1')
        self._resetButton.config(highlightthickness=0)
        self._resetButton.config(highlightbackground=GTranslatorGui.Colors.BACKGROUND)
        self._resetButton.config(highlightcolor=GTranslatorGui.Colors.BACKGROUND)
        self._resetButton.config(padx=8, pady=4)
        self._resetButton.config(image=reloadIcon)
        self._resetButton.config(command=self._on_click_resetButton)
        self._resetButton.place(x=362, y=62)
        
        # Paste button
        pasteIcon = ImageTk.PhotoImage(Image.open(self._iconPaste))
        self._pasteButton = tk.Button(self._mainFrame)
        self._pasteButton.config(background=GTranslatorGui.Colors.BACKGROUND)
        self._pasteButton.config(activebackground=GTranslatorGui.Colors.BACKGROUND)
        self._pasteButton.config(borderwidth=0)
        self._pasteButton.config(cursor='hand1')
        self._pasteButton.config(highlightthickness=0)
        self._pasteButton.config(highlightbackground=GTranslatorGui.Colors.BACKGROUND)
        self._pasteButton.config(highlightcolor=GTranslatorGui.Colors.BACKGROUND)
        self._pasteButton.config(padx=8, pady=4)
        self._pasteButton.config(image=pasteIcon)
        self._pasteButton.config(command=self._on_click_pasteSource)
        self._pasteButton.place(x=404, y=62)

        # Translate button
        languageIcon = ImageTk.PhotoImage(Image.open(self._iconLanguage))
        self._translateButton = tk.Button(self._mainFrame)
        self._translateButton.config(activebackground=GTranslatorGui.Colors.BACKGROUND)
        self._translateButton.config(background=GTranslatorGui.Colors.BACKGROUND)
        self._translateButton.config(borderwidth=0)
        self._translateButton.config(cursor='hand1')
        self._translateButton.config(highlightthickness=0)
        self._translateButton.config(highlightbackground=GTranslatorGui.Colors.BACKGROUND)
        self._translateButton.config(highlightcolor=GTranslatorGui.Colors.BACKGROUND)
        self._translateButton.config(padx=8, pady=4)
        self._translateButton.config(image=languageIcon)
        self._translateButton.config(command=self._on_click_translateButton)
        self._translateButton.place(x=447, y=62) #398
        # ----------------------------------------------------------------------------

        # Third row
        # ----------------------------------------------------------------------------
        self._translationText = tk.Text(self._mainFrame)
        self._translationText.bind('<Control-a>', self._selectAll)
        self._translationText.bind('<Control-v>', self._paste)
        self._translationText.config(background=GTranslatorGui.Colors.TEXT_BACKGROUND)
        self._translationText.config(font=('Calibri', 14))
        self._translationText.config(foreground=GTranslatorGui.Colors.TEXT_COLOR)
        self._translationText.config(height=10, width=48)
        self._translationText.config(highlightbackground=GTranslatorGui.Colors.TEXT_HIGHLIGHT_BACKGROUND)
        self._translationText.config(highlightcolor=GTranslatorGui.Colors.TEXT_HIGHLIGHT_BACKGROUND)
        self._translationText.config(highlightthickness=1)
        self._translationText.config(insertbackground=GTranslatorGui.Colors.TEXT_COLOR)
        self._translationText.config(padx=4, pady=3)
        self._translationText.config(state=tk.DISABLED)
        self._translationText.config(relief=tk.FLAT)
        self._translationText.place(x=0, y=126)
        # ----------------------------------------------------------------------------

        # Fourth row
        # ----------------------------------------------------------------------------
        self._listenLabel = tk.Label(self._mainFrame)
        self._listenLabel.config(background=GTranslatorGui.Colors.BACKGROUND)
        self._listenLabel.config(foreground=GTranslatorGui.Colors.LABEL_TEXT_COLOR)
        self._listenLabel.config(font=('Calibri', 14))
        self._listenLabel.config(padx=8, pady=4)
        self._listenLabel.config(text=GTranslatorGui.Txt.LISTEN)
        self._listenLabel.place(x=232, y=347)

        self._listenSourceButton = tk.Button(self._mainFrame)
        self._listenSourceButton.config(activebackground=GTranslatorGui.Colors.BUTTON_BACKGROUND_ACTIVE)
        self._listenSourceButton.config(activeforeground=GTranslatorGui.Colors.BUTTON_TEXT_COLOR)
        self._listenSourceButton.config(background=GTranslatorGui.Colors.BUTTON_BACKGROUND)
        self._listenSourceButton.config(foreground=GTranslatorGui.Colors.BUTTON_TEXT_COLOR)
        self._listenSourceButton.config(command=lambda : self._on_click_listen(self._listenSourceButton))
        self._listenSourceButton.config(cursor='hand1')
        self._listenSourceButton.config(font=('Calibri', 14))
        self._listenSourceButton.config(highlightthickness=1)
        self._listenSourceButton.config(highlightbackground=GTranslatorGui.Colors.BUTTON_HIGHLIGHT_BACKGROUND)
        self._listenSourceButton.config(padx=8, pady=4)
        self._listenSourceButton.config(relief=tk.FLAT)
        self._listenSourceButton.config(text=GTranslatorGui.Txt.LISTEN_SOURCE)
        self._listenSourceButton.place(x=300, y=346)

        self._listenTranslationButton = tk.Button(self._mainFrame)
        self._listenTranslationButton.config(activebackground=GTranslatorGui.Colors.BUTTON_BACKGROUND_ACTIVE)
        self._listenTranslationButton.config(activeforeground=GTranslatorGui.Colors.BUTTON_TEXT_COLOR)
        self._listenTranslationButton.config(background=GTranslatorGui.Colors.BUTTON_BACKGROUND)
        self._listenTranslationButton.config(foreground=GTranslatorGui.Colors.BUTTON_TEXT_COLOR)
        self._listenTranslationButton.config(command=lambda : self._on_click_listen(self._listenTranslationButton))
        self._listenTranslationButton.config(cursor='hand1')
        self._listenTranslationButton.config(font=('Calibri', 14))
        self._listenTranslationButton.config(highlightbackground=GTranslatorGui.Colors.BUTTON_HIGHLIGHT_BACKGROUND)
        self._listenTranslationButton.config(highlightthickness=1)
        self._listenTranslationButton.config(padx=8, pady=4)
        self._listenTranslationButton.config(relief=tk.FLAT)
        self._listenTranslationButton.config(text=GTranslatorGui.Txt.LISTEN_TRANSLATION)
        self._listenTranslationButton.place(x=384, y=346)
        # ----------------------------------------------------------------------------

        # Quick translation
        if len(origenText) > 0:
            self._sourceText.insert('1.0', origenText)
            self._on_click_translateButton()

        self._root.mainloop()

    def _checkIcon(self, iconPath):
        '''Check if icon exists or die.'''
        if not exists(iconPath):
            error(f"Icon '{iconPath}' do not found!")

    def _error(self, msg):
        '''Show an error throw messagebox'''
        return messagebox.showerror(
            message=msg,
            title=GTranslatorGui.Txt.ERROR,
            parent=self._root
        )

    def _on_close(self):
        '''Closes app.'''
        self._root.destroy()

    def _on_click_listen(self, widget):
        '''Play origen/translation text'''
        widget.config(state=tk.DISABLED)
        try:
            if id(widget) == id(self._listenSourceButton):
                origenText = self._sourceText.get("1.0", tk.END)[:-1].replace("\n", "")
                if len(origenText) > 0:
                    GTranslator().speech(origenText, self._supportedLangs[self._sourceLangValue.get()]).play()
            elif id(widget) == id(self._listenTranslationButton):
                translationText = self._translationText.get("1.0", tk.END)[:-1].replace("\n", "")
                if len(translationText) > 0:
                    GTranslator().speech(translationText, self._supportedLangs[self._targetLangValue.get()]).play()
        except Exception as e:
            self._error(e)
        finally:
            widget.config(state=tk.NORMAL)

    def _on_click_resetButton(self):
        '''Reset gui.'''
        self._sourceText.delete('1.0', tk.END)
        self._translationText.delete('1.0', tk.END)
        self._translationText.config(state=tk.DISABLED)
        self._sourceLangValue.set(G_DEFAULT_LANG_FROM)
        self._targetLangValue.set(G_DEFAULT_LANG_TARGET)

    def _on_click_translateButton(self):
        '''Translate text'''
        self._translateButton.config(state=tk.DISABLED)
        origenText = self._sourceText.get("1.0", tk.END)[:-1]
        self._translationText.config(state=tk.NORMAL)
        self._translationText.delete('1.0', tk.END)
        self._translationText.config(state=tk.DISABLED)

        # When origen text is has more than 200 chars, liste button must be disabled
        if len(origenText) > GTranslator.MAX_CHARS:
            self._listenSourceButton.configure(cursor='circle', state=tk.DISABLED)
            self._listenTranslationButton.configure(cursor='circle', state=tk.DISABLED)
        else:
            self._listenSourceButton.configure(cursor='hand1', state=tk.NORMAL)
            self._listenTranslationButton.configure(cursor='hand1', state=tk.NORMAL)

        # Do translation
        if len(origenText) > 0:
            try:
                t = GTranslator(
                        sourceLang=self._supportedLangs[self._sourceLangValue.get()],
                        targetLang=self._supportedLangs[self._targetLangValue.get()]
                    ).query(origenText)
            except Exception as e:
                self._error(e)
            else:
                self._translationText.config(state=tk.NORMAL)
                self._translationText.insert('1.0', t.translation)
                # If this widget remains disabled, user can't do ^a to copy text
                # self._translationText.config(state=tk.DISABLED)

        self._translateButton.config(state=tk.NORMAL)

    def _on_click_pasteSource(self):
        '''Reads clipboard and set source text.'''
        self._sourceText.delete('1.0', tk.END)
        self._sourceText.insert('1.0', pyperclip.paste())

    def _on_click_switchLangs(self):
        '''Switch option menus languages.'''
        source = self._sourceLangValue.get()
        target = self._targetLangValue.get()
        self._sourceLangValue.set(target)
        self._targetLangValue.set(source)

        # Do translation
        sourceText = self._sourceText.get('1.0', tk.END)[:-1]
        translationText = self._translationText.get('1.0', tk.END)[:-1]
        if len(sourceText) > 0 and len(translationText) > 0:
            self._sourceText.delete('1.0', tk.END)
            self._sourceText.insert('1.0', translationText)
            self._translationText.delete('1.0', tk.END)
            self._translationText.insert('1.0', sourceText)
            self._on_click_translateButton()

    def _on_select_optionMenu(self, widget):
        '''Deletes translation text at language option change'''
        self._translationText.delete('1.0', tk.END)

    def _on_keyup_catch_enter(self, e):
        '''Catch <Return> (Enter) and call translator method'''
        self._on_click_translateButton()
        return 'break'

    def _paste(self, e):
        '''Manage ^v event.'''
        tranges = e.widget.tag_ranges(tk.SEL)

        # This make works Text inputs like text editors
        # You can select text and paste replacing the selection
        # e.g: ^a ^v and all text is replaced by clipboard text
        if len(tranges) == 2 and tranges[0] != tranges[1]:
            e.widget.delete(tranges[0], tranges[1])
            e.widget.insert(tranges[0], pyperclip.paste())
        # No text was selected, text is paste at cursor position wherever it is
        elif len(tranges) == 0:
            cursorPosition = e.widget.index(tk.INSERT)
            e.widget.insert(cursorPosition, pyperclip.paste())

        return 'break'

    def _selectAll(self, e):
        '''Generate '<<SelectAll>>' virtual event at e.widget.'''
        e.widget.event_generate('<<SelectAll>>')

        # Disable widget after first select all event
        if id(e.widget) == id(self._translationText):
            self._translationText.config(state=tk.DISABLED)

        return 'break'

    # @staticmethod
    # def doubleClickClipboardDetection(x: float, y: float):
    #     info(f"Mouse position (double click): x: {x}; y: {y}")
    #     data = pyperclip.paste()
    #     # is data?
    #     if len(data) > 0 and data != ' ':
    #         pyperclip.copy(' ') # clean clipboard copying blank space
    #         x = x + 10
    #         y = y + 15
    #         GTranslatorGui(x, y, data)

def main():
    if '--cli' in argv:
        ClipboardTranslator().run()
    elif '--clipboard-detection' in argv or '-cbd' in argv:
        while True:
            try:
                data = pyperclip.waitForNewPaste()
                x, y = pyautogui.position()
                x = x + 10
                y = y + 15
                info(f"Mouse position: x: {x}; y: {y}")
                GTranslatorGui(x, y, data)
                pyperclip.copy(' ') # clean clipboard
                # mlc = MouseLeftClick()
                # mlc.setDoubleLeftClickCallback(GTranslatorGui.doubleClickClipboardDetection)
                # mlc.listen()
            except KeyboardInterrupt:
                info("Manually Abborted!")
                break

    elif '--gui' in argv:
        GTranslatorGui()

if __name__ == "__main__":
    main()