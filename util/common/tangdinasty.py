"""
Python wrapper for `td`
"""
from os import path
import os
import subprocess
import database

def run(script, file_loc, stdout=False):
    env = os.environ.copy()
    dsh_path = path.join(database.get_tang_root(), "td", "bin", "td_commands_prompt.exe")
    if not path.exists(dsh_path):
        dsh_path = path.join(database.get_tang_root(), "td", "bin", "td")
    if stdout:
        return subprocess.run([dsh_path,script], env=env, cwd=file_loc)
    else:
        return subprocess.run([dsh_path,script], env=env, cwd=file_loc, stdout=subprocess.DEVNULL)

