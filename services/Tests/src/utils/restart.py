import os
import json

from subprocess import Popen

cur_dir = os.path.dirname(os.path.abspath(__file__))


def restart_services():
    """
    Restart the service.
    """
    with open(f"{cur_dir}/errors.json", "r") as f:
        data = json.load(f)
        if data["errors"]["count"] < 4:
            return None

        if data["errors"]["items"] == set(data["error"]["items"]):
            return None

    Popen(f"python3 {cur_dir}/../../../../main.py stop", shell=True)
    Popen(f"python3 {cur_dir}/../../../../main.py start", shell=True)


if __name__ == '__main__':
    restart_services()
