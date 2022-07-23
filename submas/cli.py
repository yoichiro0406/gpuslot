import argparse
import asyncio
import time
from collections import deque
from typing import Dict

import pynvml
from omegaconf import OmegaConf
from rich import box, spinner
from rich.live import Live
from rich.table import Table

from .core import find_available_gpu_indices, gather_using_gpu_indices, initialize_jobs
from .status import *


def generate_status_table(jobs: deque) -> Table:
    palette = {RUNNING: "red", DONE: "green", PENDING: "grey30"}

    table = Table("", "Job Id", "Status", "GPU", box=box.HORIZONTALS, show_edge=False)
    for job in jobs:
        state = job.state
        job_id = job.job_id
        color = palette[state]
        progress_icon = spinner.Spinner("arrow3", style="red") if job.is_running else ""
        table.add_row(progress_icon, job_id, f"[{color}]{state}", f"{job.gpu_idx}")
    return table


def check_exist_running_job(job_que: deque) -> bool:
    exist_running_job = False
    for job in job_que:
        exist_running_job = exist_running_job or job.is_running
    return exist_running_job


async def run(
    jobs: Dict[str, str], num_alloc_gpus: int = 1, interval: float = 0.5
) -> None:
    job_que = initialize_jobs(jobs)
    submitted_que = deque()

    with Live(generate_status_table(job_que), refresh_per_second=20) as live:
        while job_que or check_exist_running_job(submitted_que):
            available_gpu_indices = find_available_gpu_indices()
            own_using_gpu_indices = gather_using_gpu_indices(submitted_que)
            available_gpu_indices -= own_using_gpu_indices

            is_allowed = len(own_using_gpu_indices) < num_alloc_gpus
            is_any_gpu_available = len(available_gpu_indices)

            if is_allowed and is_any_gpu_available and job_que:
                gpu_idx = available_gpu_indices.pop()  # HACK
                # gpu_idx = 0
                job = job_que.pop()
                coro = job.submit(gpu_idx)
                submitted_que.append(job)
                await coro

            for job in submitted_que:
                job.update_state()

            time.sleep(interval)
            live.update(generate_status_table(submitted_que + job_que))


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str)
    args, _ = parser.parse_known_args()
    return args


def main():
    pynvml.nvmlInit()
    args = get_args()
    cfg = OmegaConf.load(args.cfg)
    asyncio.run(run(**cfg))
