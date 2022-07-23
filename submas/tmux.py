import re
import subprocess
from typing import List


def get_tmux_sessions() -> List[str]:
    pattern = re.compile("(\w.*): .*")
    sessions = subprocess.check_output("tmux ls", shell=True, text=True).splitlines()
    names = set()
    for session in sessions:
        re_res = pattern.match(session)
        if re_res:
            name, *_ = re_res.groups()
            names.add(name)
    return names


if __name__ == "__main__":
    names = get_tmux_sessions()
    print(names)
