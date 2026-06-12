import getpass
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.auth import hash_password


password = getpass.getpass("Password: ")
confirm = getpass.getpass("Confirm password: ")
if password != confirm:
    raise SystemExit("Passwords do not match")

print(hash_password(password))
