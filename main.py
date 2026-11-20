import os
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from google import genai

# VIDEO SETTINGS
W, H = 480, 854
FPS = 15
OUT = Path("output")
FRAMES = Path("frames")

OUT.mkdir(exist_ok=True)
FRAMES.mkdir(exist_ok=True)

# GEMINI RIDDLE GENERATION
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing")

client = genai.Client(api_key=api_key)

prompt = """
Create one original, clever logic riddle for an American audience.
Keep the question short enough to speak in 10 seconds.
Return ONLY valid JSON:
{
 "question": "question",
 "answer": "short answer",
 "explanation": "one short sentence"
}
No famous or overused riddles. Make it surprising but fair.
"""

response = client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents=prompt
)

raw = response.text.strip()
raw = raw.replace("```json", "").replace("```", "").strip()
riddle = json.loads(raw)

question = riddle["question"]
answer = riddle["answer"]
explanation = riddle["explanation"]

# AMERICAN ENGLISH VOICE
voice_text = (
    "Detective challenge! " + question +
    " Think carefully. The answer is " +
    answer + ". " + explanation
)

gTTS(text=voice_text, lang="en", tld="com").save("voice.mp3")

# FONTS
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font_title = ImageFont.truetype(FONT_PATH, 27)
font_question = ImageFont.truetype(FONT_PATH, 22)
font_answer = ImageFont.truetype(FONT_PATH, 30)
font_small = ImageFont.truetype(FONT_PATH, 17)

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    line = ""

    for word in words:
        test = (line + " " + word).strip()
        width = draw.textbbox((0, 0), test, font=font)[2]

        if width <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word

    if line:
        lines.append(line)

    return lines

def centered_text(draw, text, y, font, color):
    lines = wrap_text(draw, text, font, 410)

    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        x = (W - (box[2] - box[0])) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += font.size + 9

def detective(draw, frame):
    bob = int(math.sin(frame * 0.15) * 6)
    cy = 485 + bob

    # Shadow
    draw.ellipse((145, 730, 335, 750), fill=(10, 15, 35))

    # Body
    draw.rounded_rectangle(
        (170, cy + 55, 310, cy + 240),
        radius=38,
        fill=(35, 75, 145)
    )

    # Shirt
    draw.polygon(
        [(210, cy + 60), (240, cy + 125), (270, cy + 60)],
        fill=(245, 245, 245)
    )

    # Moving arms
    arm = int(math.sin(frame * 0.18) * 18)

    draw.line(
        (180, cy + 100, 120, cy + 150 + arm),
        fill=(225, 165, 110),
        width=25
    )
    draw.line(
        (300, cy + 100, 360, cy + 150 - arm),
        fill=(225, 165, 110),
        width=25
    )

    # Face
    draw.ellipse(
        (155, cy - 110, 325, cy + 90),
        fill=(235, 180, 125),
        outline=(65, 40, 30),
        width=4
    )

    # Hair
    draw.arc(
        (155, cy - 130, 325, cy + 20),
        180, 355,
        fill=(50, 32, 25),
        width=24
    )

    # Detective hat
    draw.rounded_rectangle(
        (180, cy - 165, 300, cy - 100),
        radius=16,
        fill=(110, 75, 45)
    )
    draw.ellipse(
        (150, cy - 115, 330, cy - 90),
        fill=(90, 60, 38)
    )

    # Blinking eyes
    blink = frame % 100 < 4

    if blink:
        draw.line((190, cy - 5, 220, cy - 5),
                  fill=(30, 25, 20), width=5)
        draw.line((260, cy - 5, 290, cy - 5),
                  fill=(30, 25, 20), width=5)
    else:
        draw.ellipse((190, cy - 18, 220, cy + 10), fill="white")
        draw.ellipse((260, cy - 18, 290, cy + 10), fill="white")
        draw.ellipse((200, cy - 10, 212, cy + 6), fill=(20, 25, 35))
        draw.ellipse((270, cy - 10, 282, cy + 6), fill=(20, 25, 35))

    # Eyebrows
    draw.line((188, cy - 28, 220, cy - 32),
              fill=(45, 30, 25), width=6)
    draw.line((260, cy - 32, 292, cy - 28),
              fill=(45, 30, 25), width=6)

    # Moving mouth
    mouth = 7 + int(abs(math.sin(frame * 0.3)) * 13)
    draw.ellipse(
        (222, cy + 35, 258, cy + 35 + mouth),
        fill=(100, 25, 35)
    )

def make_frame(i, total):
    img = Image.new("RGB", (W, H), (17, 24, 52))
    d = ImageDraw.Draw(img)

    # Moving stars
    for j in range(20):
        x = (j * 83 + i * (j % 3 + 1)) % W
        y = (j * 137) % H
        d.ellipse((x, y, x + 5, y + 5),
                  fill=(110, 145, 210))

    # Header
    d.rounded_rectangle(
        (30, 25, 450, 88),
        radius=20,
        fill=(245, 185, 55)
    )
    centered_text(d, "THE DAILY RIDDLE", 43, font_title, (25, 25, 45))

    # Floating question marks
    for j in range(3):
        x = 65 + j * 165
        y = 330 + int(math.sin(i * 0.12 + j) * 20)
        d.text((x, y), "?", font=font_title, fill=(255, 215, 70))

    detective(d, i)

    # Question and answer cards
    if i < total * 0.72:
        d.rounded_rectangle(
            (25, 110, 455, 285),
            radius=24,
            fill=(37, 51, 91)
        )
        centered_text(
            d, "CAN YOU SOLVE THIS?",
            128, font_title, (255, 215, 75)
        )
        centered_text(
            d, question,
            185, font_question, (255, 255, 255)
        )
    else:
        d.rounded_rectangle(
            (25, 110, 455, 285),
            radius=24,
            fill=(25, 105, 78)
        )
        centered_text(
            d, "THE ANSWER IS...",
            130, font_title, (255, 230, 100)
        )
        centered_text(
            d, answer,
            185, font_answer, (255, 255, 255)
        )

        centered_text(
            d, explanation,
            290, font_small, (255, 235, 180)
        )

    return img

# GET VOICE DURATION
result = subprocess.run(
    [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        "voice.mp3"
    ],
    capture_output=True,
    text=True,
    check=True
)

duration = float(result.stdout.strip()) + 2
total_frames = int(duration * FPS)

# CREATE CARTOON FRAMES
for i in range(total_frames):
    frame = make_frame(i, total_frames)
    frame.save(FRAMES / f"{i:05d}.png")

# CREATE FINAL VIDEO
subprocess.run(
    [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", "frames/%05d.png",
        "-i", "voice.mp3",
        "-vf",
        "scale=1080:1920:flags=lanczos,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "24",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        "output/daily-riddle.mp4"
    ],
    check=True
)

print("SUCCESS: Cartoon riddle video created!")
