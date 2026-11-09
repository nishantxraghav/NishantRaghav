# Body Flicker

An anime-style body flicker for video calls. Hold a ninja hand sign and you vanish in
a crack of lightning: you overload white-hot, zip into a line of light and are gone in
a strike and a flash. Hold it again and you reappear. It runs on your laptop and
shows up in your call as a camera. Your video stays on your machine.

## Setup

1. Install [OBS Studio](https://obsproject.com). It provides the virtual camera driver.
   You only need it installed, not open.
2. Install [Python 3.13](https://www.python.org/downloads/) if you don't have it.
3. Double-click `run.bat`. The first run installs everything and downloads two small
   tracking models from Google, so it needs internet.

## Using it

1. Start `run.bat`. After the 5-second countdown, leave the frame completely and stay
   out, with no arm or shoulder showing. Leaning is not enough, because the app has no
   way of knowing what is behind you.
2. Wait for the beep, about 2 to 3 seconds after you are fully out of view. Then sit
   back down and press **T** in the preview to test the effect.
3. In your call, choose **OBS Virtual Camera** as your camera:
   - **Zoom:** Settings > Video > Camera
   - **Google Meet:** Settings > Video > Camera. Reload the tab if it isn't listed.
   - **Teams:** Settings > Devices > Camera

### The sign

Raise one hand. Straighten your index and middle fingers and press them together. Curl
your ring and little fingers, and tuck your thumb in. Hold for 0.6 seconds, until the
green ring in the preview closes. Do the same thing to come back.

The preview tells you what it sees, such as "Sign: curl ring finger". Coloured dots mark
your fingertips, so you can find your hand even while the picture shows an empty room.
Nobody on the call sees the preview or the dots.

### Keys

These work when the preview window is focused.

| Key | Action |
| --- | --- |
| B | Recapture the background |
| T | Trigger the effect without the sign |
| Q | Quit |

## Getting a clean vanish

- Keep the laptop still. If it moves, press B to recapture the background.
- Keep the lighting steady. Daylight changes can make the empty room look different
  from the live picture.
- Wait for the beep. If you never fully leave, the hidden area is painted in after 30
  seconds and leaves a person-shaped smudge. The preview warns you, and B starts again.
- Your empty chair stays in the picture. Put it where you want it before capturing.
- Part of you still showing after you vanish means the capture caught you. Press B and
  leave the frame further.

## Settings

Everything is in `config.toml`, including hold time, cooldown, effect length, and
camera number. A missing line uses its default.

To tune the effect, look under `[effect]`. `style` picks the look: `"electric"` (the
default) or `"smoke"` for the older puff of smoke and falling leaves. `spark_seconds`
sets how long the electric sparks last, and `smoke_seconds` and `leaf_seconds` set how
long the smoke and falling leaves last. `shake_pixels` and `flash_strength` set the
camera shake and flash of light, and 0 turns either one off.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Preview says "Preview only" | Install OBS. If OBS is open, click Stop Virtual Camera in it, then restart this app. |
| "Could not open camera" or "sent no picture" | Close other apps that use the camera. Check Windows Settings > Privacy & security > Camera. |
| Wrong camera, or a blank OBS picture in the preview | Change `index` under `[camera]` in `config.toml`. |
| OBS Virtual Camera is not listed in the call app | Restart the call app, or reload the browser tab, after starting this app. |
| Others see a mirrored picture | They don't. Call apps mirror only your own self-view. |
| Sign doesn't fire | Follow the hint in the preview. Keep your hand clearly in view and not too far away. If your touching fingers are rejected, raise `max_tip_gap`. |
| A peace sign fires it | Lower `max_tip_gap`. |
| Video stutters | Close heavy apps, or lower `max_rate_hz` or `input_width` under `[vision]`. Lowering `spark_seconds` (or `smoke_seconds` and `leaf_seconds`) also helps. |
| Part of your body stays visible during the effect | Use better lighting and a plainer background. The body outline depends on how clearly you stand out. |
| Console shows INFO or WARNING lines at startup | These come from MediaPipe and are harmless. |

## Development

```
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest
```

To try it without a webcam, run `main.py --source some_video.mp4`. It also accepts
`--no-vcam`, `--no-preview`, and `--duration SECONDS`.

The tests in `tests/test_real_models.py` run the real models on photos. They are
skipped unless `FLICKER_SAMPLES` points to a folder with MediaPipe's sample images.
