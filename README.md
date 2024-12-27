# PyTranslator

## Why?
Have you ever downloaded Google Translate extension to your browser?

![image](https://github.com/user-attachments/assets/88ac40a4-4d67-4cd9-be4d-157251f4aca1)

Total size is 9.6MB and 9.5MB is from JavaScript files. This is not all, if you look inside, there are many duplicated code and request your translations is not the only one thing the extension does as background work.

## Too much bullshit for only two important requests!
If you look at [translator.py](https://github.com/frannylac/PyTranslator/blob/a2d9b035f53ff2753401f838419b7d4f9e8eab86/translator.py#L87C7-L87C18) you will see **GTranslator** class. It have two methods, query and speech. That class has only 57 lines and the entire translator is about 450 lines of code (Gui included). There is no hidden functionality or something else. Google Translator otherhand it has.

I think is clear now **why**.

## Instalation

- If you doesn't have pip installed, proceed with it installation [here](https://pip.pypa.io/en/stable/installation/).
- Python3.8+ is required (i didn't tested with another version).

`pip3 install -r requirements.txt`

## Operation modes
- `--cli` Waits at terminal level for any clipboard contents and print translation on it.
- `--listener-gui` Waits as running process for any clipboard contents and show the gui with the content already translated. (Usefull for read documents outside browser). But becarefull, everything you copy will be sended to Google's API servers.
- `--gui` Show the gui to user interactive use.

## Listener mode
The process keeps waiting for clipboard contents, once you copy something the will gui appears with the translation already done. After the popup window is closed clipboard is cleaned automatically.
To start the process again just copy some text and the gui will appears inmediatelly.

## Exit
`Ctrl-c` at terminal level or `kill -2 $(ps a | grep translator.py | awk 'NR == 1 {print $1;}')` if was started as background process.

## Not tested on Windows/Mac
I use Ubuntu widh dwm, dmenu and clipmenu as a minimal setup, i think it shoud run at least on Mac but not sure about Window.

## Screenshots

![image](https://github.com/user-attachments/assets/de7fd0fc-e052-48e6-ada3-a4c7af25117a)

As you can see is a minimal gui with dark mode, you can customize/modify everything as you like, but becarefull night reading with day mode colors could fry your eyes.

## Languages file

[This is the file](https://github.com/frannylac/PyTranslator/blob/main/languages.txt) where you must put all available languages you want. There is a complete list of supported languages at [this file](https://github.com/frannylac/PyTranslator/blob/main/languages-all.txt) to take from. Again you must customized to your needs.
