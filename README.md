# Pi Dashboard

A small web dashboard for a Raspberry Pi (or any Linux machine). It shows:

- live system stats: CPU temperature, load, memory, disk, uptime
- a graph of internet download speed and latency, measured automatically every 30 minutes and stored in SQLite

Plain Python, Flask and Chart.js. The only dependency is Flask.

## How it works

| File | Job |
|---|---|
| `monitor.py` | reads system stats from `/sys` and `/proc`, and runs the speed test (a 10 MB download from Cloudflare plus the median TCP connect time to 1.1.1.1) |
| `db.py` | stores speed test results in `dashboard.db` |
| `app.py` | Flask server with a background thread that runs a speed test every N minutes |
| `templates/index.html` | the page: stat cards and a Chart.js line chart, refreshed in the browser |

API: `GET /api/status`, `GET /api/speedtests`, `POST /api/speedtests/run`.

## Run it

```bash
python3 -m venv --system-site-packages ~/dashboard-venv
source ~/dashboard-venv/bin/activate
pip install -r requirements.txt
python app.py --port 8000 --interval 30
```

Open `http://<pi-address>:8000` from any device on the same network.

On Windows or macOS it also runs, but the Pi-specific cards (temperature, load, memory, uptime) show "n/a".

## Start automatically on boot (systemd)

1. Edit `pi-dashboard.service`: set `User=` to your username and fix the paths.
2. Install and start it:

```bash
sudo cp pi-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pi-dashboard
sudo systemctl status pi-dashboard
```

## Notes and limits

- The speed test measures one 10 MB download, so it is a rough indicator, not a precise benchmark.
- There is no login. The server listens on all interfaces, so only run it on a network you trust.
- Results are stored in `dashboard.db` next to the app (ignored by git).
