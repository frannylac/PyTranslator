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
        self.__transl = GTranslator(sourceLang=srcLang, targetLang=destLang)

    def __translate(self, text: str) -> str:
        '''Do translate text'''
        return self.__transl.query(text).translation

    def run(self)-> None:
        '''Run translation process'''
        while True:
            try:
                # WAIT FOR NEXT TEXT TO TRANSLATE
                text = pyperclip.waitForNewPaste()
                print( f"{Colors.WARNING}[Translating...]{Colors.ENDC}: {text}" )
                try:
                    text = self.__translate(text)
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
        TRANSLATE_BUTTON = 'Translate'

    def __init__(self, x: float=0, y: float=0, origenText: str=""):
        '''Creates a floating window at x,y position.'''
        global G_DEFAULT_LANG_FROM, G_DEFAULT_LANG_TARGET

        self._supportedLangs = load_supported_langs()

        # Icons
        self._iconReload = f"{ICONS_FOLDER}reload.png"
        self.__checkIcon(self._iconReload)

        self._rootSize = (500, 350)
        self._root = tk.Tk()
        self._root.protocol('WV_DELETE_WINDOW', self.__on_close)
        # Make floating window
        self._root.wm_attributes('-type', 'dialog')
        self._root.title(GTranslatorGui.Txt.TITLE)
        # self._root.resizable(width=False, height=False)

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
        self._mainFrame.config(background='#424242')
        self._mainFrame.config(height=self._rootSize[1])
        self._mainFrame.config(width=self._rootSize[0])
        self._mainFrame.config(padx=4, pady=4)
        self._mainFrame.place(x=0, y=0)

        # First row
        # ----------------------------------------------------------------------------
        # Input text to translate
        # fix: implementar ctrl-a para seleccionar todo
        self._sourceText = tk.Text(self._mainFrame)
        self._sourceText.bind('<Control-a>', self.__selectAll)
        self._sourceText.bind('<Control-v>', self.__paste)
        self._sourceText.bind('<Return>', self.__on_keyup_catch_enter)
        self._sourceText.config(background='#757575')
        self._sourceText.config(border=0)
        self._sourceText.config(font=('Calibri', 14))
        self._sourceText.config(highlightthickness=0)
        self._sourceText.config(padx=4, pady=3)
        # height: 1 line
        # width: 38 chars
        self._sourceText.config(height=1, width=48)
        self._sourceText.place(x=0, y=2)
        # ----------------------------------------------------------------------------

        # Second row
        # ----------------------------------------------------------------------------
        self._fromLabel = tk.Label(self._mainFrame)
        self._fromLabel.config(background="#424242")
        self._fromLabel.config(font=('Calibri', 14))
        self._fromLabel.config(padx=8, pady=4)
        self._fromLabel.config(text=GTranslatorGui.Txt.LANG_FROM)
        self._fromLabel.place(x=0, y=45)

        self._sourceLangValue = tk.StringVar()
        self._sourceLangValue.set(G_DEFAULT_LANG_FROM)
        self._sourceLangOM = tk.OptionMenu(
                self._mainFrame,
                self._sourceLangValue,
                *self._supportedLangs.keys(),
                command=self.__on_select_optionMenu
            )
        self._sourceLangOM.config(highlightthickness=0)
        self._sourceLangOM.config(background='#373737')
        self._sourceLangOM['menu'].config(background='#373737')
        self._sourceLangOM.config(font=('Calibri', 14))
        self._sourceLangOM.place(x=60, y=42)

        self._toLabel = tk.Label(self._mainFrame)
        self._toLabel.config(background="#424242")
        self._toLabel.config(font=('Calibri', 14))
        self._toLabel.config(padx=8, pady=4)
        self._toLabel.config(text=GTranslatorGui.Txt.LANG_TO)
        self._toLabel.place(x=165, y=45)

        self._targetLangValue = tk.StringVar()
        self._targetLangValue.set(G_DEFAULT_LANG_TARGET)
        self._targetLangOM = tk.OptionMenu(
                self._mainFrame,
                self._targetLangValue,
                *self._supportedLangs.keys(),
                command=self.__on_select_optionMenu
            )
        self._targetLangOM.config(highlightthickness=0)
        self._targetLangOM.config(background='#373737')
        self._targetLangOM['menu'].config(background='#373737')
        self._targetLangOM.config(font=('Calibri', 14))
        self._targetLangOM.place(x=203, y=42)

        # Reset button
        reloadIcon = ImageTk.PhotoImage(Image.open(self._iconReload))
        self._resetButton = tk.Button(self._mainFrame)
        self._resetButton.config(highlightthickness=0, highlightbackground='#424242', highlightcolor='#424242')
        self._resetButton.config(background='#424242', activebackground='#424242')
        self._resetButton.config(borderwidth=0)
        self._resetButton.config(cursor='hand1')
        self._resetButton.config(height=31, width=30)
        self._resetButton.config(padx=8, pady=4)
        self._resetButton.config(relief=tk.FLAT)
        self._resetButton.config(image=reloadIcon)
        self._resetButton.config(command=self.__on_click_resetButton)
        self._resetButton.place(x=350, y=43)

        # Translate button
        self._translateButton = tk.Button(self._mainFrame)
        self._translateButton.config(background='#373737', foreground='#F5F5F5')
        self._translateButton.config(cursor='hand1')
        self._translateButton.config(font=('Calibri', 14))
        self._translateButton.config(highlightthickness=0)
        self._translateButton.config(padx=8, pady=4)
        self._translateButton.config(text=GTranslatorGui.Txt.TRANSLATE_BUTTON)
        self._translateButton.config(command=self.__on_click_translateButton)
        self._translateButton.place(x=398, y=43)
        # ----------------------------------------------------------------------------

        # Third row
        # ----------------------------------------------------------------------------
        self._translationText = tk.Text(self._mainFrame)
        self._translationText.bind('<Control-a>', self.__selectAll)
        self._translationText.bind('<Control-v>', self.__paste)
        self._translationText.config(background='#757575')
        self._translationText.config(font=('Calibri', 14))
        self._translationText.config(highlightthickness=0)
        self._translationText.config(padx=4, pady=3)
        self._translationText.config(state=tk.DISABLED)
        self._translationText.config(height=10, width=48)
        self._translationText.place(x=0, y=88)
        # ----------------------------------------------------------------------------

        # Fourth row
        # ----------------------------------------------------------------------------
        self._listenLabel = tk.Label(self._mainFrame)
        self._listenLabel.config(background="#424242")
        self._listenLabel.config(font=('Calibri', 14))
        self._listenLabel.config(padx=8, pady=4)
        self._listenLabel.config(text=GTranslatorGui.Txt.LISTEN)
        self._listenLabel.place(x=228, y=308)

        self._listenSourceButton = tk.Button(self._mainFrame)
        self._listenSourceButton.config(background='#373737', foreground='#F5F5F5')
        self._listenSourceButton.config(command=lambda : self.__on_click_listen(self._listenSourceButton))
        self._listenSourceButton.config(cursor='hand1')
        self._listenSourceButton.config(font=('Calibri', 14))
        self._listenSourceButton.config(highlightthickness=0)
        self._listenSourceButton.config(padx=8, pady=4)
        self._listenSourceButton.config(text=GTranslatorGui.Txt.LISTEN_SOURCE)
        self._listenSourceButton.place(x=300, y=306)

        self._listenTranslationButton = tk.Button(self._mainFrame)
        self._listenTranslationButton.config(background='#373737', foreground='#F5F5F5')
        self._listenTranslationButton.config(command=lambda : self.__on_click_listen(self._listenTranslationButton))
        self._listenTranslationButton.config(cursor='hand1')
        self._listenTranslationButton.config(font=('Calibri', 14))
        self._listenTranslationButton.config(highlightthickness=0)
        self._listenTranslationButton.config(padx=8, pady=4)
        self._listenTranslationButton.config(text=GTranslatorGui.Txt.LISTEN_TRANSLATION)
        self._listenTranslationButton.place(x=384, y=306)
        # ----------------------------------------------------------------------------

        # Quick translation
        if len(origenText) > 0:
            self._sourceText.insert('1.0', origenText)
            self.__on_click_translateButton()

        self._root.mainloop()

    def __checkIcon(self, iconPath):
        '''Check if icon exists or die.'''
        if not exists(iconPath):
            error(f"Icon '{iconPath}' do not found!")

    def __error(self, msg):
        '''Show an error throw messagebox'''
        return messagebox.showerror(
            message=msg,
            title=GTranslatorGui.Txt.ERROR,
            parent=self._root
        )

    def __on_close(self):
        '''Closes app.'''
        self._root.destroy()

    def __on_click_listen(self, widget):
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
            self.__error(e)
        finally:
            widget.config(state=tk.NORMAL)

    def __on_click_resetButton(self):
        '''Reset gui.'''
        self._sourceText.delete('1.0', tk.END)
        self._translationText.delete('1.0', tk.END)
        self._translationText.config(state=tk.DISABLED)
        self._sourceLangValue.set(G_DEFAULT_LANG_FROM)
        self._targetLangValue.set(G_DEFAULT_LANG_TARGET)

    def __on_click_translateButton(self):
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
                self.__error(e)
            else:
                self._translationText.config(state=tk.NORMAL)
                self._translationText.insert('1.0', t.translation)
                # If this widget remains disabled, user can't do ^a to copy text
                # self._translationText.config(state=tk.DISABLED)

        self._translateButton.config(state=tk.NORMAL)

    def __on_select_optionMenu(self, widget):
        '''Deletes translation text at language option change'''
        self._translationText.delete('1.0', tk.END)

    def __on_keyup_catch_enter(self, e):
        '''Catch <Return> (Enter) and call translator method'''
        self.__on_click_translateButton()
        return 'break'

    def __paste(self, e):
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

    def __selectAll(self, e):
        '''Generate '<<SelectAll>>' virtual event at e.widget.'''
        e.widget.event_generate('<<SelectAll>>')

        # Disable widget after first select all event
        if id(e.widget) == id(self._translationText):
            self._translationText.config(state=tk.DISABLED)

        return 'break'


def main():
    if '--cli' in argv:
        ClipboardTranslator().run()
    elif '--listener-gui' in argv:
        while True:
            try:
                clipContent = pyperclip.waitForNewPaste()
                x, y = pyautogui.position()
                x = x + 10
                y = y + 15
                info(f"Mouse position: x: {x}; y: {y}")
                GTranslatorGui(x, y, clipContent)
                pyperclip.copy('') # clean clipboard
            except KeyboardInterrupt:
                info("Manually Abborted!")
                break
    elif '--gui' in argv:
        GTranslatorGui()

if __name__ == "__main__":
    main()