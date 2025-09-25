import os, sys, subprocess, pathlib

def main():
    py = sys.executable
    cmd = [
        py, "-m", "nuitka", "--onefile", "--standalone",
        "--enable-plugin=pyqt6",
        "--include-package=forexsmartbot",
        "--output-dir=dist",
        "app.py"
    ]
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)

if __name__ == "__main__":
    main()
