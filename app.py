from flask import Flask, request, send_file, redirect
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone
import io
import os

app = Flask(__name__)

WIDTH = 1200
HEIGHT = 300
FONT_SIZE = 160
FRAME_COUNT = 5
FRAME_DURATION = 1000

target_time = None


def format_remaining(target):
    now = datetime.now(timezone.utc)
    total_seconds = int((target - now).total_seconds())

    if total_seconds <= 0:
        return "you missed the session"

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    return f"{days}d {hours}h {minutes}m"


def generate_gif(target):
    frames = []

    font = ImageFont.load_default()

    text = format_remaining(target)

    for _ in range(FRAME_COUNT):
        img = Image.new("RGB", (WIDTH, HEIGHT), "black")
        draw = ImageDraw.Draw(img)

        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        draw.text(
            ((WIDTH - w) // 2, (HEIGHT - h) // 2),
            text,
            font=font,
            fill=(white)
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
    global target_time

    if request.method == "POST":
        value = request.form.get("target")
        try:
            dt = datetime.fromisoformat(value)
            target_time = dt.replace(tzinfo=timezone.utc)
            return redirect("/")
        except:
            pass

    current = target_time.isoformat() if target_time else ""

    return f"""
    <html>
    <body style="background:#111;color:white;text-align:center;font-family:sans-serif;">
        <h1>Set Countdown</h1>
        <form method="post">
            <input type="datetime-local" name="target" required>
            <br><br>
            <button type="submit">Set</button>
        </form>
        <p>Current target: {current or "Not set"}</p>
        <p>Public image: /mut_f1_timer</p>
    </body>
    </html>
    """


@app.route("/mut_f1_timer")
def countdown_gif():
    if not target_time:
        return "Countdown not set", 404

    gif = generate_gif(target_time)
    return send_file(gif, mimetype="image/gif")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
