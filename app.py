from flask import Flask, request, send_file, redirect
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone, timedelta
import io
import os

app = Flask(__name__)

# Image settings
WIDTH = 1200
HEIGHT = 300
BASE_FONT_SIZE = 130

FRAME_COUNT = 60
FRAME_DURATION = 1000  # 1 second per frame

LOGO_PATH = "/mnt/data/ocau_xenforo_logo.png"

# AEST timezone
AEST = timezone(timedelta(hours=10))

mut_f1_timer = None


def format_remaining_with_seconds(target, offset=0):
    now = datetime.now(AEST) + timedelta(seconds=offset)
    total_seconds = int((target - now).total_seconds())

    if total_seconds <= 0:
        return "0d 0h 0m 0s"

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{days}d {hours}h {minutes}m {seconds}s"


def get_fitting_font(draw, text):
    size = BASE_FONT_SIZE

    while size > 20:
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= WIDTH - 60:
            return font

        size -= 5

    return font


def load_background():
    bg = Image.open(LOGO_PATH).convert("RGB")
    bg = bg.resize((WIDTH, HEIGHT))

    # Add subtle dark overlay for text contrast
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 120))
    bg = bg.convert("RGBA")
    bg = Image.alpha_composite(bg, overlay)

    return bg.convert("RGB")


def generate_gif(target):
    frames = []
    background = load_background()

    for i in range(FRAME_COUNT):
        text = format_remaining_with_seconds(target, offset=i)

        img = background.copy()
        draw = ImageDraw.Draw(img)

        font = get_fitting_font(draw, text)

        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        draw.text(
            ((WIDTH - w) // 2, (HEIGHT - h) // 2),
            text,
            font=font,
            fill="white"
        )

        frames.append(img)

    output = io.BytesIO()

    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION,
        loop=0
    )

    output.seek(0)
    return output


@app.route("/", methods=["GET", "POST"])
def set_time():
    global mut_f1_timer

    if request.method == "POST":
        value = request.form.get("target")
        try:
            dt = datetime.fromisoformat(value)
            mut_f1_timer = dt.replace(tzinfo=AEST)
            return redirect("/")
        except:
            pass

    current = mut_f1_timer.isoformat() if mut_f1_timer else ""

    return f"""
    <html>
    <body style="background:#000;color:white;text-align:center;font-family:sans-serif;">
        <h1>Set Countdown</h1>
        <form method="post">
            <input type="datetime-local" name="target" required style="font-size:1.2em;padding:8px;">
            <br><br>
            <button type="submit" style="font-size:1.2em;padding:8px 16px;">Set</button>
        </form>
        <p>Current target: {current or "Not set"}</p>
        <p>Public image: /mut_f1_timer.gif</p>
        <br>
        <img src="/mut_f1_timer.gif" style="max-width:100%;">
    </body>
    </html>
    """


@app.route("/mut_f1_timer.gif")
def countdown_gif():
    if not mut_f1_timer:
        return "Countdown not set", 404

    gif = generate_gif(mut_f1_timer)
    return send_file(gif, mimetype="image/gif")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
