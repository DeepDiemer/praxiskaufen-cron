"""Taktgeber: startet per SSH einen Lauf auf einem entfernten Server (Render-Cronjob).

Alles Umgebungsspezifische kommt aus Umgebungsvariablen, nichts davon steht im Repository:
  SSH_TARGET       benutzer@host
  SSH_KNOWN_HOSTS  Zeile(n) im known_hosts-Format (fester Server-Fingerabdruck)
  SSH_PRIVATE_KEY  privater Schlüssel (Secret). Auf dem Server darf er nur den Lauf starten (command=…,restrict).
"""
import os
import subprocess
import sys
import tempfile


def main():
    key = os.environ.get("SSH_PRIVATE_KEY", "").replace("\\n", "\n").strip()
    target = os.environ.get("SSH_TARGET", "").strip()
    known = os.environ.get("SSH_KNOWN_HOSTS", "").replace("\\n", "\n").strip()
    if "PRIVATE KEY" not in key or "@" not in target or not known:
        print("Konfiguration fehlt (SSH_PRIVATE_KEY, SSH_TARGET, SSH_KNOWN_HOSTS)", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory() as d:
        kp, kh = os.path.join(d, "id"), os.path.join(d, "known_hosts")
        with open(os.open(kp, os.O_WRONLY | os.O_CREAT, 0o600), "w") as f:
            f.write(key + "\n")
        with open(kh, "w") as f:
            f.write(known + "\n")
        cmd = ["ssh", "-i", kp, "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes", "-o", "UserKnownHostsFile=" + kh,
               "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=30", target]
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=10 * 60)
        out = (r.stdout or "").strip().splitlines()
        print("\n".join([l for l in out if "Pseudo-terminal" not in l][-5:]) or "Lauf gestartet")
        return r.returncode


if __name__ == "__main__":
    sys.exit(main())
