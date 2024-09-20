#!/usr/bin/env python3

from tkinter.scrolledtext import ScrolledText
from screeninfo import get_monitors
from multiprocessing import Queue
from threading import Thread
from typing import Callable
from pynput import keyboard
from openai import OpenAI
from PIL import ImageGrab
from io import BytesIO
import tkinter as tk
import base64
import os

client = OpenAI()

def ask_chatgpt(prompt: str, window: tk.Tk, screenshot: bytes):
    window.destroy()

    b64_image = base64.b64encode(screenshot).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an AI powered computer assistant who can see what the user is doing on the computer. Analyze what you can see and help the user with their request.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64," + b64_image,
                        },
                    },
                ],
            }
        ],
    )

    response_content = response.choices[0].message.content

    show_chatgpt_response(response_content)

def show_chatgpt_response(response: str):
    window = tk.Toplevel(root)
    window.title("Assistant Response")

    text = ScrolledText(window, font=("Arial", 12))
    text.insert(tk.END, response)
    text.pack(pady=10, padx=10)

def submit_input(input: tk.Entry, function: Callable, **kwargs):
    def submit(_=None):
        function(input.get(), input.master, **kwargs)
    return submit

def show_assistant_window(screenshot):
    window = tk.Toplevel(root)
    window.title("Ask Assistant")

    label = tk.Label(window, text="Ask the Assistant:")
    label.pack(pady=10, padx=10)

    input_box = tk.Entry(window, width=50)
    submit_func = submit_input(input_box, ask_chatgpt, screenshot=screenshot)
    input_box.pack(pady=10, padx=10)
    input_box.bind('<Return>', submit_func)
    input_box.focus_set()

    submit_button = tk.Button(window, text="Ask", command=submit_func)
    submit_button.pack(pady=10, padx=10)

def take_screenshot():
    monitors = get_monitors()
    for monitor in monitors:
        if monitor.is_primary:
            size = (0, 0, monitor.width, monitor.height)
    screenshot = ImageGrab.grab(size)
    screenshot_data = BytesIO()
    screenshot.save(screenshot_data, format="PNG")

    return screenshot_data.getbuffer()

def worker(queue: Queue):
    while True:
        queue.get()

        screenshot = take_screenshot()
        show_assistant_window(screenshot)

def keyboard_listener(queue):
    def on_press(key):
        try:
            if key == keyboard.Key.f9:
                queue.put(True)
        except AttributeError:
            pass

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    worker_queue = Queue()

    worker_thread = Thread(target=worker, args=(worker_queue,))
    worker_thread.start()

    listener_thread = Thread(target=keyboard_listener, args=(worker_queue,))
    listener_thread.start()

    root = tk.Tk()
    root.title("GPT4V-Assistant")
    root.withdraw()

    print(f"Welcome to GPT4V Helper!")
    print(f"Press <F9> to send a message.")
    print(f"PID: {os.getpid()}")

    root.mainloop()

    worker_thread.join()
    listener_thread.join()
