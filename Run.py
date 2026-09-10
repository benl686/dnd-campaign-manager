import os, sys, socket, threading, webbrowser, time
from streamlit.web import cli as stcli

PORT = 8501
URL = f"http://localhost:{PORT}"

def port_in_use(port):
    """Return True if something is already listening on the given port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0

def open_browser():
    """Wait briefly for Streamlit to start, then open the browser."""
    time.sleep(2)
    webbrowser.open_new(URL)

if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(__file__)

    os.chdir(base_dir)

    if port_in_use(PORT):
        # App is already running — just open the browser.
        webbrowser.open_new(URL)
        sys.exit(0)

    threading.Thread(target=open_browser, daemon=True).start()

    sys.argv = [
        "streamlit",
        "run",
        "Home.py",
        f"--server.port={PORT}",
        "--server.headless=true",   # prevent Streamlit from opening its own tab
    ]
    stcli.main()