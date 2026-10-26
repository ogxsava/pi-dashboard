"""System stats and a small internet speed test, using only the standard library."""
import os
import shutil
import socket
import statistics
import time
import urllib.request

DOWNLOAD_URL = "https://speed.cloudflare.com/__down?bytes=10000000"  # 10 MB test file
LATENCY_HOST = ("1.1.1.1", 443)


def cpu_temp_c():
    """CPU temperature in Celsius, or None where the Pi sensor file does not exist."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read()) / 1000, 1)
    except OSError:
        return None


def load_avg():
    """1, 5 and 15 minute load averages, or None on Windows."""
    try:
        return [round(x, 2) for x in os.getloadavg()]
    except (AttributeError, OSError):
        return None


def memory():
    """Memory used / total in MB, read from /proc/meminfo (Linux only)."""
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                key, value = line.split(":")
                info[key] = int(value.split()[0]) // 1024  # kB -> MB
        total, available = info["MemTotal"], info["MemAvailable"]
        return {"used_mb": total - available, "total_mb": total}
    except (OSError, KeyError):
        return None


def disk():
    total, used, _ = shutil.disk_usage("/")
    return {"used_gb": round(used / 1e9, 1), "total_gb": round(total / 1e9, 1)}


def uptime_s():
    try:
        with open("/proc/uptime") as f:
            return int(float(f.read().split()[0]))
    except OSError:
        return None


def status():
    return {
        "hostname": socket.gethostname(),
        "cpu_temp_c": cpu_temp_c(),
        "load": load_avg(),
        "memory": memory(),
        "disk": disk(),
        "uptime_s": uptime_s(),
    }


def latency_ms(samples=5):
    """Median time to open a TCP connection to LATENCY_HOST."""
    times = []
    for _ in range(samples):
        start = time.perf_counter()
        with socket.create_connection(LATENCY_HOST, timeout=5):
            pass
        times.append((time.perf_counter() - start) * 1000)
    return round(statistics.median(times), 1)


def download_mbps(max_seconds=15):
    """Download the test file and return the speed in megabits per second.
    On a very slow connection it stops after max_seconds and uses what was received so far."""
    start = time.perf_counter()
    request = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "pi-dashboard/1.0"})  # server rejects the default one
    received = 0
    with urllib.request.urlopen(request, timeout=10) as response:
        while time.perf_counter() - start < max_seconds:
            chunk = response.read(65536)
            if not chunk:
                break
            received += len(chunk)
    return round(received * 8 / 1e6 / (time.perf_counter() - start), 1)


def speed_test():
    """Returns {'download_mbps': ..., 'latency_ms': ...}; failed parts are None."""
    result = {"download_mbps": None, "latency_ms": None}
    for key, fn in (("latency_ms", latency_ms), ("download_mbps", download_mbps)):
        try:
            result[key] = fn()
        except OSError as error:  # no network, blocked, timeout, ...
            print(f"speed test: {key} failed: {error}")
    return result
