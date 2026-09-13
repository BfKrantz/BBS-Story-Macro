# bleach-autofarm

A small desktop app that auto-clicks the repetitive menu/dialogue buttons in
**Bleach: Brave Souls** (Skip, Tap Screen, Quest Clear banner, Close, Next
Quest, Prepare for Quest, Start Quest) using OpenCV template matching, so you
can idle through story stages or repeat-farm a cleared stage without
babysitting every screen.

![status](https://img.shields.io/badge/status-personal--project-blue)

## What it does / doesn't do
- ✅ Detects and clicks known menu/dialogue buttons by matching them against
  reference images captured from the game.
- ❌ Does **not** play combat for you — it has no idea how to fight. Pair it
  with stages you can already auto-battle, or stages where you only need
  help clicking through the surrounding menus.

## Get it

**Option A — download the exe (Windows, no Python needed)**
Every push to `main` auto-builds `BleachAutoFarm.exe` via GitHub Actions.
Go to the repo's **Actions** tab → latest **Build Windows EXE** run →
download the `BleachAutoFarm-windows-exe` artifact, unzip it, and run
`BleachAutoFarm.exe`. Windows SmartScreen may warn about an unsigned exe
from an unknown publisher — click "More info" → "Run anyway" if you trust
the source (you built it yourself via your own repo's Actions run).

**Option B — run from source**
```bash
git clone https://github.com/<your-username>/bleach-autofarm.git
cd bleach-autofarm
pip install -r requirements.txt
python run_gui.py          # GUI
python run_cli.py          # headless CLI alternative
```

**Option C — build the exe yourself locally**
On Windows, inside the repo folder:
```bat
build.bat
```
This installs PyInstaller and produces `dist\BleachAutoFarm.exe`.

With the game running, click **Start**. The status dot goes green while
running. **Pause** freezes it in place, **Stop** ends the session. You can
also always fling your mouse into any screen corner to trigger pyautogui's
fail-safe and abort instantly.

## Updating the button templates
`templates/*.png` are the reference images it matches against, cropped
tightly around each button (no background). If you resize the game window
or the buttons stop matching, take a fresh screenshot, crop around just the
button, and overwrite the corresponding file. Thresholds live in
`bleach_autofarm/core.py` (`CLICK_PRIORITY`) if you need to loosen/tighten
a specific match.

## Project layout
```
bleach-autofarm/
├── bleach_autofarm/
│   ├── core.py     # screen capture + template matching + click loop (AutoFarmer class)
│   ├── gui.py       # Tkinter front end
│   └── cli.py       # headless front end
├── templates/        # cropped reference button images
├── run_gui.py
├── run_cli.py
├── build_exe.spec    # PyInstaller build config
├── build.bat          # local Windows build script
├── .github/workflows/build-exe.yml   # auto-builds the exe on push
└── requirements.txt
```

## ⚠️ A note on account risk
Automating input like this is very likely against Bleach: Brave Souls'
Terms of Service — most gacha games prohibit macros/bots and can flag or
restrict accounts that use them. This is a personal automation project, not
an endorsement of botting; use it on an account you're comfortable putting
at risk, and don't leave it running unattended for long stretches without
thinking through that tradeoff.

## License
MIT — see [LICENSE](LICENSE).
