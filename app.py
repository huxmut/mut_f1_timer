from flask import Flask, request, send_file, redirect
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone, timedelta
import io
import os

app = Flask(__name__)

# Image and font settings
WIDTH = 1200
HEIGHT = 300
FONT_SIZE = 160
FRAME_COUNT = 3
FRAME_DURATION = 1000

# AEST timezone
AEST = timezone(timedelta(hours=10))

# Global target time
mut_f1_timer = None

# Format remaining time (days, hours, minutes)
def format_remaining(target):
    now = datetime.now(AEST)
    total_seconds = int((target - now).total_seconds())

    if total_seconds <= 0:
        return "0d 0h 0m"

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    return f"{days}d {hours}h {minutes}m"

# Generate the countdown GIF
def generate_gif(target):
    frames = []

    # Try large font, fallback to default
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", FONT_SIZE)
    except:
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
            fill="white"  # ✅ MUST be a string
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

# HTML form to set target date/time
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
    </body>
    </html>
    """

# Serve the countdown GIF
@app.route("/mut_f1_timer.gif")
def countdown_gif():
    if not mut_f1_timer:
        return "Countdown not set", 404

    gif = generate_gif(mut_f1_timer)
    return send_file(gif, mimetype="image/gif")

# Run server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
