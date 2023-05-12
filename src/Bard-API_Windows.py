import argparse
import json
import random
import re
import string
import os
import sys
import requests
from prompt_toolkit import prompt
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.markdown import Markdown
import PySimpleGUI as sg
from tkinter import messagebox
import tkinter as tk
import threading
from pynput import keyboard
import keyboard
import time
global logo
logo = ''

# Create the window
layout = [
    [sg.Text("Session ID: ")],
    [sg.Input("")],
    [sg.Ok()]
]
window = sg.Window("Google Bard", layout)
event, session_id_raw = window.read()
window.close()
session_id = session_id_raw[0]

def __create_session() -> PromptSession:
    return PromptSession(history=InMemoryHistory())

def __create_completer(commands: list, pattern_str: str = "$") -> WordCompleter:
    return WordCompleter(words=commands, pattern=re.compile(pattern_str))

import PySimpleGUI as sg

def __get_input(
    message: str,
    completer: WordCompleter = None,
) -> str:


    layout = [
        [sg.Text("Input:")],
        [sg.InputText()],
        [sg.Button('Submit'), sg.Button('Cancel')]
    ]

    window = sg.Window('Input', layout, element_justification='c')

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':
            break
        elif event == 'Submit':
            message = values[0]
            window.close()
            return message

    window.close()





class Chatbot:
    
    __slots__ = [
        "headers",
        "_reqid",
        "SNlM0e",
        "conversation_id",
        "response_id",
        "choice_id",
        "session",
    ]

    def __init__(self, session_id: str = session_id):
        headers = {
            "Host": "bard.google.com",
            "X-Same-Domain": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Origin": "https://bard.google.com",
            "Referer": "https://bard.google.com/",
        }
        self._reqid = int("".join(random.choices(string.digits, k=4)))
        self.conversation_id = ""
        self.response_id = ""
        self.choice_id = ""
        self.session = requests.Session()
        self.session.headers = headers
        self.session.cookies.set("__Secure-1PSID", session_id)
        self.SNlM0e = self.__get_snlm0e()

    def __get_snlm0e(self):
        resp = self.session.get(url="https://bard.google.com/", timeout=10)
        if resp.status_code != 200:
            raise Exception("Could not get Google Bard")
        SNlM0e = re.search(r"SNlM0e\":\"(.*?)\"", resp.text).group(1)
        return SNlM0e

    def ask(self, message: str) -> dict:
        
        params = {
            "bl": "boq_assistant-bard-web-server_20230419.00_p1",
            "_reqid": str(self._reqid),
            "rt": "c",
        }

        message_struct = [
            [message],
            None,
            [self.conversation_id, self.response_id, self.choice_id],
        ]
        data = {
            "f.req": json.dumps([None, json.dumps(message_struct)]),
            "at": self.SNlM0e,
        }

        resp = self.session.post(
            "https://bard.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate",
            params=params,
            data=data,
            timeout=120,
        )

        chat_data = json.loads(resp.content.splitlines()[3])[0][2]
        if not chat_data:
            return {"content": f"Google Bard encountered an error: {resp.content}."}
        json_chat_data = json.loads(chat_data)
        results = {
            "content": json_chat_data[0][0],
            "conversation_id": json_chat_data[1][0],
            "response_id": json_chat_data[1][1],
            "factualityQueries": json_chat_data[3],
            "textQuery": json_chat_data[2][0] if json_chat_data[2] is not None else "",
            "choices": [{"id": i[0], "content": i[1]} for i in json_chat_data[4]],
        }
        self.conversation_id = results["conversation_id"]
        self.response_id = results["response_id"]
        self.choice_id = results["choices"][0]["id"]
        self._reqid += 100000
        return results

if __name__ == "__main__":
    
    console = Console()
    if os.getenv("BARD_QUICK"):
        session = os.getenv("BARD_SESSION")
        if not session:
            print("BARD_SESSION environment variable not set.")
            sys.exit(1)
        chatbot = Chatbot(session)
        MESSAGE = " ".join(sys.argv[1:])
        console.print(Markdown(chatbot.ask(MESSAGE)["content"]))
        sys.exit(0)
    parser = argparse.ArgumentParser()
    parser.add_argument(
    "--session",
    help="__Secure-1PSID cookie.",
    type=str,
    required=False,
    default="",
)
    args = parser.parse_args()

    chatbot = Chatbot(args.session if args.session else session_id)

    prompt_session = __create_session()
    completions = __create_completer(["!exit", "!reset"])

import threading
import tkinter as tk

def wait_for_key(key_pressed):
    keyboard.wait('`')
    key_pressed.set()

def create_window(content_str, window_ready):
    window = tk.Tk()
    window.title("Bard")
    text_label = tk.Label(window, font=("Arial", 10), wraplength=500, pady=10, padx=10)
    def update_text(text):
        text_label.config(text=text)
    update_text(content_str)
    text_label.pack(pady=20)
    window_ready.set()
    window.mainloop()

try:
    while True:
        print()
        user_prompt = __get_input(message="Input:", completer=completions)
        console.print()
        if user_prompt == "!exit":
            break
        elif user_prompt == "!reset":
            chatbot.conversation_id = ""
            chatbot.response_id = ""
            chatbot.choice_id = ""
            continue
        response = chatbot.ask(user_prompt)
        content_str = (response["content"])

        # Create an event to signal when the window is ready to be displayed
        window_ready = threading.Event()

        # Start the window creation thread
        window_thread = threading.Thread(target=create_window, args=(content_str, window_ready))
        window_thread.daemon = True
        window_thread.start()

        # Wait for the window to be created before continuing
        window_ready.wait()

        # Create an event to signal when the key is pressed
        key_pressed = threading.Event()

        # Start the keyboard listener thread
        key_thread = threading.Thread(target=wait_for_key, args=(key_pressed,))
        key_thread.daemon = True
        key_thread.start()

        # Wait for the key to be pressed before continuing
        key_pressed.wait()

except KeyboardInterrupt:
    print("Exiting...")
