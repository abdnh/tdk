"""
Pronounce a Turkish word using mpv
Usage:
    python prontr.py foo
"""

import os
import shutil
import subprocess
import sys
import tempfile
import urllib

from tdk import TDK


def play(word: str) -> None:
    tdkobj = TDK(word)

    for link in tdkobj.audio_links:

        req = tdkobj._get_request(link)
        with urllib.request.urlopen(req) as res:
            with tempfile.NamedTemporaryFile("wb", suffix=".wav", delete=False) as file:
                file.write(res.read())
                path = file.name
            subprocess.run(
                [
                    shutil.which("mpv"),
                    "--idle=no",
                    "--no-terminal",
                    "--force-window=no",
                    "--audio-display=no",
                    "--keep-open=no",
                    path,
                ],
                check=True,
            )
            os.remove(path)


play(sys.argv[1])
