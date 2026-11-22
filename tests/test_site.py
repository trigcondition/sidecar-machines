"""Headless check of the listing page's preview player (site/app.js). Skipped locally when no Chrome/Chromium works;
when the CI environment variable is set (GitHub Actions) a missing or hanging browser FAILS the test.

Builds a tiny site in a temp directory (the real site files, an index.json with a preview set made of generated
silent MP3 streams), loads it in headless Chromium, runs tests/site/sitetest.js inside the page and reads the result
from the dumped DOM. Needs no packages.
"""
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
import functools
import http.server
import html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mp3gen  # noqa: E402


def find_browser():
    for name in ("google-chrome", "google-chrome-stable", "chrome", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p:
            return p
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return mac if os.path.exists(mac) else None


IN_CI = bool(os.environ.get("CI"))
TIMEOUT = 60 if IN_CI else 20   # seconds; a hung browser is a skip locally, a failure in CI


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def build_site(tmp):
    """Fill `tmp` with the real site files, a harness page (test.html) and an index.json with a preview set."""
    shutil.copytree(os.path.join(ROOT, "site"), tmp, dirs_exist_ok=True)
    # the harness page is the real index.html plus the test script (same CSP: scripts from 'self')
    with open(os.path.join(tmp, "index.html")) as f:
        page = f.read().replace('<script src="app.js"></script>',
                                '<script src="app.js"></script>\n<script src="sitetest.js"></script>')
    with open(os.path.join(tmp, "test.html"), "w") as f:
        f.write(page)
    shutil.copy(os.path.join(HERE, "site", "sitetest.js"), tmp)
    vdir = os.path.join(tmp, "machines", "test.sine", "1.0.0")
    os.makedirs(os.path.join(vdir, "preview"))
    for n in ("01 Kick.mp3", "Pad #2 (long).mp3"):
        with open(os.path.join(vdir, "preview", n), "wb") as f:
            f.write(mp3gen.make_mp3(frames=400))
    base = dict(kind="machine", version="1.0.0", compatible_from="1.0.0", short="SINE", author="alice",
                licence="MIT", board="pi5", api=2, sha256="0" * 64, description="A sine.", size=10,
                readme="machines/test.sine/1.0.0/README.md")
    e1 = dict(base, id="test.sine", name="Sine", file="machines/test.sine/1.0.0/x.rmp",
              demo="https://example.org/demo.mp3",
              previews=[{"name": n[:-4], "file": "machines/test.sine/1.0.0/preview/" + n, "bytes": 400 * 417}
                        for n in ("01 Kick.mp3", "Pad #2 (long).mp3")]
              + [{"name": "dot", "file": "machines/./x.mp3", "bytes": 1}])   # refused by the player: not counted
    e1b = dict(e1, board="pi4", file="machines/test.sine/1.0.0/x4.rmp", sha256="4" * 64, size=2048, short="SINQ")
    e1["sha256"] = "5" * 64
    e2 = dict(base, id="test.plain", name="Plain", file="machines/test.plain/1.0.0/x.rmp",
              description="<b>bold</b> & plain")
    e3 = dict(base, id="test.only4", name="Only4", board="pi4", file="machines/test.only4/1.0.0/x.rmp")
    with open(os.path.join(tmp, "index.json"), "w") as f:
        json.dump({"schema": 1, "entries": [e3, e2, e1b, e1],
                   "latest": {"test.sine": {"pi4": "1.0.0", "pi5": "1.0.0"}, "test.plain": {"pi5": "1.0.0"},
                              "test.only4": {"pi4": "1.0.0"}}}, f)


class SiteTest(unittest.TestCase):
    def no_browser(self, why):
        if IN_CI:
            self.fail(why + " (CI is set: the player test may not be skipped)")
        self.skipTest(why)

    def test_preview_player(self):
        if not find_browser():
            self.no_browser("no Chrome or Chromium found")
        tmp = tempfile.mkdtemp()
        try:
            build_site(tmp)
            handler = functools.partial(Quiet, directory=tmp)
            srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=srv.serve_forever, daemon=True)
            thread.start()
            prof = tempfile.mkdtemp()
            try:
                r = subprocess.run(
                    [find_browser(), "--headless=new", "--disable-gpu", "--no-sandbox", "--user-data-dir=" + prof,
                     "--autoplay-policy=no-user-gesture-required", "--virtual-time-budget=20000", "--dump-dom",
                     "http://127.0.0.1:%d/test.html" % srv.server_address[1]],
                    capture_output=True, timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                self.no_browser("the browser did not finish in %d s (some sandboxes block headless Chromium)" % TIMEOUT)
            finally:
                srv.shutdown()
                srv.server_close()
                thread.join()
                shutil.rmtree(prof, ignore_errors=True)
            dom = r.stdout.decode("utf-8", "replace")
            m = re.search(r'<pre id="result">(.*?)</pre>', dom, re.S)
            self.assertTrue(m, "no result in the page: " + dom[-600:] + r.stderr.decode()[-600:])
            res = json.loads(html.unescape(m.group(1)))
            self.assertTrue(res["ok"], "\n".join(res["log"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
