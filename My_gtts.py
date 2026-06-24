from gtts import gTTS
import os
text = "Hello, world!"
language = 'hi'
output = gTTS(text=text, lang=language, slow=False)
output.save("output.mp3")
os.system("start output.mp3")