import argparse
import asyncio
import os
import sys
import time
from collections import deque
from typing import Dict

import pynvml
from loguru import logger
from omegaconf import OmegaConf
from rich import box, spinner
from rich.live import Live
from rich.table import Table

from .core import (
    check_exist_running_job,
    find_available_gpu_indices,
    gather_using_gpu_indices,
    initialize_jobs,
)
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


async def run(
    jobs: Dict[str, str],
    num_alloc_gpus: int = 1,
    interval: float = 0.5,
    log_path: str = "main.log",
) -> None:
    logger.add(log_path)
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
                gpu_idx = available_gpu_indices.pop()
                job = job_que.pop()
                coro = job.submit(gpu_idx)
                submitted_que.append(job)
                await coro

            for job in submitted_que:
                job.update_state()

            time.sleep(interval)
            live.update(generate_status_table(submitted_que + job_que))
    logger.info("Completed all jobs")


def setup_custom_resolver():
    def yaml_datetime():
        if not hasattr(yaml_datetime, "exp_datetime"):
            exp_datetime = time.strftime("%Y_%m%d_%H%M")
            yaml_datetime.exp_datetime = exp_datetime
        return yaml_datetime.exp_datetime

    OmegaConf.register_new_resolver("open", lambda path: OmegaConf.load(path))
    OmegaConf.register_new_resolver("datetime", yaml_datetime)
    OmegaConf.register_new_resolver("join", lambda a, b: os.path.join(a, b))


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str)
    args, _ = parser.parse_known_args()
    return args


def main():
    logger.configure(handlers=[])
    pynvml.nvmlInit()
    args = get_args()
    setup_custom_resolver()
    cfg = OmegaConf.load(args.cfg)
    asyncio.run(run(**cfg))
