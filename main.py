import asyncio
import uvicorn
import os
import sys
import subprocess
import shutil
import re

from app.api import app
from app.fetcher import live_fetcher

# ==================================================
# ENV DETECTION
# ==================================================
def is_colab():
    try:
        import google.colab
        return True
    except ImportError:
        return False

# ==================================================
# CLOUDFLARE TUNNEL (COLAB ONLY)
# ==================================================
def install_cloudflared():
    if shutil.which("cloudflared"):
        print("✅ cloudflared already installed")
        return

    print("⏳ Installing cloudflared...")
    subprocess.run([
        "curl", "-fsSL",
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
        "-o", "cloudflared"
    ], check=True)

    subprocess.run(["chmod", "+x", "cloudflared"], check=True)
    print("✅ cloudflared installed")

def start_cloudflare_tunnel(port: int):
    print(f"🌍 Starting Cloudflare tunnel on port {port}...")

    proc = subprocess.Popen(
        ["./cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    public_url = None
    for line in iter(proc.stdout.readline, ""):
        if "trycloudflare.com" in line and not public_url:
            match = re.search(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", line)
            if match:
                public_url = match.group(0)
                print(f"\n✅ Public URL: {public_url}\n")
                break

    return proc, public_url

# ==================================================
# MAIN APP
# ==================================================
async def main():
    asyncio.create_task(live_fetcher())

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config)

    if is_colab():
        install_cloudflared()
        tunnel_proc, public_url = start_cloudflare_tunnel(8000)
        print("🔌 API available at:")
        print(public_url)
        print(public_url + "/live/options")
        print(public_url + "/ws/options")

    await server.serve()

# ==================================================
if __name__ == "__main__":
    asyncio.run(main())
