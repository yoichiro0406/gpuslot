import re
import subprocess
from typing import Set


def get_tmux_sessions() -> Set[str]:
    pattern = re.compile("(\w.*): .*")
    try:
        sessions = subprocess.check_output(
            "tmux ls", shell=True, text=True
        ).splitlines()
    except subprocess.CalledProcessError:
        return set()
    names = set()
    for session in sessions:
        re_res = pattern.match(session)
        if re_res:
            name, *_ = re_res.groups()
            names.add(name)
    return names


def kill_session(name) -> None:
    subprocess.call(f"tmux kill-session -t {name}", shell=True)


if __name__ == "__main__":
    names = get_tmux_sessions()
    print(names)
