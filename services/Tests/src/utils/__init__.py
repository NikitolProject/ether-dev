import os

from subprocess import Popen


def restart_services() -> None:
    """
    Restart all services.
    """
    Popen(["python3", f"{os.path.dirname(os.path.abspath(__file__))}/restart.py"])
