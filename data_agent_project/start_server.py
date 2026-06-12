import os
import subprocess
import sys
import time
from pathlib import Path

LLAMA_SERVER = r"C:\Users\flow\AppData\Local\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe"
MODEL_PATH = Path(__file__).parent / "models" / "Qwen3-4B-Q4_K_M.gguf"
HOST = "0.0.0.0"
PORT = 8080


def start_server():
    if not Path(LLAMA_SERVER).exists():
        print(f"llama-server not found at: {LLAMA_SERVER}")
        sys.exit(1)

    if not MODEL_PATH.exists():
        print(f"Model not found at: {MODEL_PATH}")
        print("Please download the model first.")
        sys.exit(1)

    cmd = [
        LLAMA_SERVER,
        "-m", str(MODEL_PATH),
        "--host", HOST,
        "--port", str(PORT),
        "-ngl", "99",
        "--ctx-size", "4096",
    ]

    print(f"Starting llama-server...")
    print(f"  Model: {MODEL_PATH.name}")
    print(f"  Address: http://{HOST}:{PORT}")
    print(f"  GPU layers: 99 (full offload)")
    print()

    proc = subprocess.Popen(cmd)

    print("Waiting for server to start...")
    time.sleep(5)

    import urllib.request
    try:
        resp = urllib.request.urlopen(f"http://localhost:{PORT}/health")
        print(f"Server health: {resp.read().decode()}")
        print("\nServer is ready!")
    except Exception as e:
        print(f"Server may still be loading: {e}")

    return proc


if __name__ == "__main__":
    proc = start_server()
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        proc.terminate()
