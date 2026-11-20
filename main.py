import os
import json
import subprocess
from datetime import date
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from google import genai

WIDTH, HEIGHT = 1080, 1920
OUTPUT = "output"
os.makedirs(OUTPUT, exist_ok=True)

def generate_riddle():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY secret is missing!")

    client = genai.Client(api_key=api_key)

    prompt = f"""
Create ONE original, difficult and clever English brain teaser
for a USA YouTube Shorts audience.

Today's date: {date.today()}

Requirements:
- Make it genuinely challenging but logically solvable.
- Avoid common overused riddles.
- Use natural American English.
- Question should be short and intriguing.
- Answer must be correct.
- Explanation must clearly prove the answer.
- Do not repeat a basic textbook riddle.

Return ONLY valid JSON:
{{
  "question": "Your original riddle",
  "answer": "SHORT ANSWER",
  "explanation": "Clear explanation"
}}
"""

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )

    raw = response.text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    start = raw.find("{")
    end = raw.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError("Gemini did not return valid JSON")

    riddle = json.loads(raw[start:end])

    for key in ["question", "answer", "explanation"]:
        if not isinstance(riddle.get(key), str) or not riddle[key].strip():
            raise ValueError(f"Invalid riddle field: {key}")

    print("Today's AI riddle:", riddle)
    return riddle


def get_font(size):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    return ImageFont.truetype(path, size)


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = (current + " " + word).strip()

        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def draw_centered(draw, text, y, font, fill, max_width=900):
    lines = wrap_text(draw, text, font, max_width)
    line_height = font.size + 24

    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        x = (WIDTH - (box[2] - box[0])) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height


def make_background(riddle):
    img = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = img.load()

    for y in range(HEIGHT):
        for x in range(WIDTH):
            glow = int(20 * (1 - y / HEIGHT))
            pixels[x, y] = (8 + glow, 12 + glow, 35 + glow)

    draw = ImageDraw.Draw(img)

    draw_centered(
        draw, "CAN YOU SOLVE THIS?", 220,
        get_font(65), "#FFD700"
    )

    draw_centered(
        draw, "ONLY 1% GET IT RIGHT", 400,
        get_font(38), "#FFFFFF"
    )

    draw_centered(
        draw, riddle["question"], 650,
        get_font(58), "#FFFFFF", 920
    )

    draw_centered(
        draw, "THINK CAREFULLY...", 1320,
        get_font(46), "#00E5FF"
    )

    draw_centered(
        draw, "ANSWER REVEALED SOON", 1510,
        get_font(36), "#FFD700"
    )

    img.save(f"{OUTPUT}/background.png")


def make_answer(riddle):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle(
        (65, 760, 1015, 1200),
        radius=45,
        fill=(10, 20, 55, 245),
        outline=(255, 215, 0, 255),
        width=8
    )

    draw_centered(
        draw, "THE ANSWER IS", 830,
        get_font(48), "#FFD700"
    )

    draw_centered(
        draw, riddle["answer"].upper(), 960,
        get_font(65), "#FFFFFF", 850
    )

    img.save(f"{OUTPUT}/answer.png")


def main():
    print("Generating a new AI riddle...")

    riddle = generate_riddle()

    narration = (
        "Here is today's brain teaser. "
        + riddle["question"]
        + " Think carefully. "
        + "The answer is... "
        + riddle["answer"]
        + ". "
        + riddle["explanation"]
        + " Did you solve it? Comment below!"
    )

    print("Generating American English voice...")

    gTTS(
        text=narration,
        lang="en",
        tld="com"
    ).save(f"{OUTPUT}/voice.mp3")

    make_background(riddle)
    make_answer(riddle)

    duration = float(subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        f"{OUTPUT}/voice.mp3"
    ]).decode().strip())

    reveal = max(4, duration - 5)

    command = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "30",
        "-i", f"{OUTPUT}/background.png",
        "-loop", "1", "-framerate", "30",
        "-i", f"{OUTPUT}/answer.png",
        "-i", f"{OUTPUT}/voice.mp3",
        "-filter_complex",
        (
            "[0:v]zoompan=z='min(zoom+0.0003,1.08)':"
            "d=1:s=1080x1920:fps=30,format=yuv420p[bg];"
            "[1:v]format=rgba[ans];"
            f"[bg][ans]overlay=0:0:enable='gte(t,{reveal})'[v]"
        ),
        "-map", "[v]",
        "-map", "2:a",
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        f"{OUTPUT}/riddle.mp4"
    ]

    print("Rendering video...")
    subprocess.run(command, check=True)

    with open(f"{OUTPUT}/title.txt", "w") as f:
        f.write(
            "Can You Solve This Brain Teaser? #shorts\n\n"
            + riddle["question"]
            + "\n\nAnswer: "
            + riddle["answer"]
        )

    print("SUCCESS: AI video generated!")


if __name__ == "__main__":
    main()
