import subprocess
import sys

proc = subprocess.Popen(
    ["docker", "logs", "-f", "clan-manager"], stderr=subprocess.PIPE, text=True
)
for line in iter(proc.stderr.readline, ""):
    print(line, end="", file=sys.stderr)
    if "bot is ready!" in line.lower():
        proc.kill()
        sys.exit(0)

sys.exit(1)