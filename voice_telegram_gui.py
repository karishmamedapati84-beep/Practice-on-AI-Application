import tkinter as tk
from tkinter import ttk
import threading
import speech_recognition as sr
import pyttsx3
import requests
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import time
import os

# ───────── CONFIG ─────────
BOT_TOKEN   = "8856828420:AAHsQIpu1qGi_B5hTqBefvLLkZD2T_4xvFs"
CHAT_ID     = "7214834118"

# ───────── VOICE ENGINE ─────────
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

# ───────── TELEGRAM ─────────
def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except:
        print("Telegram message failed")

def send_voice(file):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVoice"
        with open(file, "rb") as f:
            requests.post(url, data={"chat_id": CHAT_ID}, files={"voice": f})
    except:
        print("Voice send failed")

# ───────── RECORD AUDIO (FIXED) ─────────
def record_audio(filename="voice.wav", duration=5):
    fs = 44100
    status_label.config(text="Recording...", fg="orange")

    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    write(filename, fs, recording)

# ───────── RECOGNITION ─────────
recognizer = sr.Recognizer()

def listen_and_send():
    try:
        status_label.config(text="Listening...", fg="green")
        animate()

        speak("Say something")

        record_audio("voice.wav", 5)

        if os.path.getsize("voice.wav") == 0:
            raise Exception("Empty audio file")

        with sr.AudioFile("voice.wav") as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio)

        output_box.delete(0, tk.END)
        output_box.insert(0, text)

        speak(text)

        send_message(text)
        send_voice("voice.wav")

        status_label.config(text="Sent to Telegram ✅", fg="cyan")

    except Exception as e:
        print(e)
        status_label.config(text="Error! Try again", fg="red")
        output_box.delete(0, tk.END)
        output_box.insert(0, "Could not understand")

# ───────── ANIMATION (SMOOTH GLOW) ─────────
def animate():
    for _ in range(8):
        canvas.itemconfig(circle, fill="#4ade80")
        root.update()
        time.sleep(0.05)
        canvas.itemconfig(circle, fill="#22c55e")
        root.update()
        time.sleep(0.05)

# ───────── GUI ─────────
root = tk.Tk()
root.title("Voice Telegram Assistant")
root.geometry("420x520")
root.configure(bg="#0f172a")

# Title
title = tk.Label(root, text="🎙 Voice Assistant",
                 font=("Arial", 20, "bold"),
                 bg="#0f172a", fg="white")
title.pack(pady=15)

# Canvas (circle animation)
canvas = tk.Canvas(root, width=400, height=250,
                   bg="#0f172a", highlightthickness=0)
canvas.pack()

circle = canvas.create_oval(140, 60, 260, 180, fill="#22c55e")

# Status label
status_label = tk.Label(root, text="Click to Speak",
                        bg="#0f172a", fg="white",
                        font=("Arial", 12))
status_label.pack(pady=10)

# Output box
output_box = ttk.Entry(root, font=("Arial", 14), justify="center")
output_box.pack(pady=10, ipadx=10, ipady=6)

# Button
def start():
    threading.Thread(target=listen_and_send, daemon=True).start()

btn = tk.Button(root, text="🎤 Speak",
                command=start,
                font=("Arial", 14, "bold"),
                bg="#22c55e",
                fg="black",
                activebackground="#16a34a",
                padx=25, pady=10)
btn.pack(pady=25)

# Run app
root.mainloop()