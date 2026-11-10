# Internet Speed Test

A Python terminal script that measures download and upload speeds over multiple runs and displays min/max/average speeds, idle ping, progress bars, and connection ratings.

## Requirements

- Python 3.9 or newer
- An internet connection for live measurements

## Quick start

```bash
# Clone your repository after uploading these files to GitHub, then enter its directory.
python -m venv .venv
```

Activate the virtual environment:

- macOS/Linux: `source .venv/bin/activate`
- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Windows Command Prompt: `.venv\Scripts\activate.bat`

Then install and run:

```bash
python -m pip install -r requirements.txt
python internet_speed_test_v1.0.0.py
```

The script performs three sequential download/upload measurements by default. Live tests can take some time and use a substantial amount of data. A failed connection or unavailable test server results in an error message and a nonzero exit code.

## Customize

Edit the constants near the top of `internet_speed_test_v1.0.0.py`:

- `NUM_TESTS`: number of measurements (must be at least 1)
- `EXCELLENT_*`, `GOOD_*`, `NEUTRAL_*`, `BAD_*`: rating thresholds in Mbps
- `DOWNLOAD_BAR_SCALE_MBPS` and `UPLOAD_BAR_SCALE_MBPS`: full-width bar values

Overall ratings require **both** average download and average upload speeds to meet the corresponding thresholds. Individual ratings use only their respective direction. The output omits ANSI colors in non-interactive terminals, when `NO_COLOR` is set, or when `TERM=dumb`.

## Run tests

No live connection is required for the automated tests:

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the same tests on pushes and pull requests.

## Upload to GitHub

Create an empty repository on GitHub, then either upload the **contents** of this folder using **Add file → Upload files**, including the `.github` folder, or use Git:

```bash
cd internet-speed-test
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Replace `YOUR_USERNAME` and `YOUR_REPOSITORY` with your own values. You may need to configure your Git name/email and authenticate with GitHub before pushing.

## Dependency

Uses [`speedtest-cli`](https://pypi.org/project/speedtest-cli/) (`import speedtest`). This project is not affiliated with Ookla. No license is supplied; choose a license before inviting reuse or contributions.
