#!/usr/bin/env python3
import subprocess, sys, os, platform, shutil

ENV_FILE = ".env"
SESSION_BASENAME = "instagram_session"  # custom session filename you control

def read_env_username():
    if not os.path.exists(ENV_FILE):
        return None
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("INSTA_USERNAME="):
                return line.split("=", 1)[1].strip()
    return None

def default_session_path(username: str) -> str:
    sysname = platform.system()
    if sysname == "Windows":
        base = os.getenv("APPDATA") or os.path.expanduser("~\\AppData\\Roaming")
        return os.path.join(base, "Instaloader", f"session-{username}")
    elif sysname == "Darwin":  # macOS
        base = os.path.expanduser("~/Library/Application Support/Instaloader")
        return os.path.join(base, f"session-{username}")
    else:  # Linux
        base = os.path.expanduser("~/.config/instaloader")
        return os.path.join(base, f"session-{username}")

def session_exists(username: str) -> bool:
    # check both default location and custom file in CWD
    return os.path.exists(default_session_path(username)) or os.path.exists(SESSION_BASENAME)

def ensure_dep(dep: str):
    """Check a module is importable, try to install if missing."""
    try:
        __import__(dep)
    except ImportError:
        print(f"Installing {dep} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

def create_session_with_browser(username: str, browser: str = "chrome") -> bool:
    """
    Use browser cookies (no password prompt). Requires browser-cookie3.
    Saves session to ./instagram_session (SESSION_BASENAME).
    """
    ensure_dep("browser_cookie3")
    cmd = [
        sys.executable, "-m", "instaloader",
        "-b", browser,
        "--sessionfile", SESSION_BASENAME,
        ":stories"  # harmless target to force auth; you can use any public profile
    ]
    print("🔐 Creating Instagram session from browser cookies …")
    print("   Make sure you are logged into Instagram in your browser.")
    print("   Command:", " ".join(cmd))
    try:
        # interactive I/O allowed (no capture), so errors show up
        ret = subprocess.run(cmd, check=False)
        ok = (ret.returncode == 0) and os.path.exists(SESSION_BASENAME)
        return ok
    except Exception as e:
        print("Browser-cookie session failed:", e)
        return False

def create_session_with_password(username: str, password: str) -> bool:
    """
    Fallback: pass password flag once to create session (less safe).
    Saves session to default location unless you also add --sessionfile.
    """
    cmd = [
        sys.executable, "-m", "instaloader",
        "-l", username,
        "-p", password,
        "--sessionfile", SESSION_BASENAME
    ]
    print("🔐 Creating Instagram session with username/password (fallback) …")
    print("   Command:", " ".join(cmd[:-1]), "<hidden>")
    try:
        ret = subprocess.run(cmd, check=False)
        ok = (ret.returncode == 0) and os.path.exists(SESSION_BASENAME)
        return ok
    except Exception as e:
        print("Password session failed:", e)
        return False

def main():
    print("🚀 Instagram Session Setup Tool")
    print("=" * 50)
    username = read_env_username()
    if not username:
        print("❌ No INSTA_USERNAME found in .env. Add: INSTA_USERNAME=your_username")
        return

    print(f"📋 Username: {username}")
    if session_exists(username):
        print("✅ Session already exists.")
        print("   You can now load it in Python, e.g.:")
        print('   L.load_session_from_file("{}", filename="{}")'.format(username, SESSION_BASENAME))
        return

    # Make sure instaloader is installed
    ensure_dep("instaloader")

    # 1) Try browser cookies first (best UX on Windows)
    #    Change 'chrome' to 'edge' or 'firefox' if needed.
    if create_session_with_browser(username, browser="chrome"):
        print("✅ Session created via browser cookies.")
    else:
        print("⚠️ Browser-cookie login failed. Trying password fallback …")
        pw = os.getenv("INSTA_PASSWORD")
        if not pw:
            print("❌ Set INSTA_PASSWORD in .env or environment to use the password fallback.")
            return
        if create_session_with_password(username, pw):
            print("✅ Session created via password.")
        else:
            print("❌ Could not create a session.")

    # Show where sessions are
    print("\n📁 Default session (Instaloader):", default_session_path(username))
    print("📄 Custom session file (this tool):", os.path.abspath(SESSION_BASENAME))
    print("\n🎯 In your downloader, load it like:")
    print('    L.load_session_from_file("{}", filename="{}")'.format(username, SESSION_BASENAME))

if __name__ == "__main__":
    main()
