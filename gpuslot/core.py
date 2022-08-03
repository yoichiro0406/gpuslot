import asyncio
import os
import time
from collections import deque
from typing import Deque, Dict, Set

import pynvml
import rich
import sh
from loguru import logger
from rich import box, spinner
from rich.live import Live
from rich.table import Table

from .status import *
from .tmux import get_tmux_sessions
from .utils import fire_and_forget


class GpuHostedJob:
    def __init__(self, job_id: str, cmd: str):
        self.job_id = job_id
        self.cmd = cmd
        self.state = PENDING
        self.gpu_idx = ""
        self.errlog = "/tmp/gpuslot.err"
        with open(self.errlog, "w") as _:
            pass

    def update_state(self):
        sessions = get_tmux_sessions()
        is_running = self.session_name in sessions
        if self.state == RUNNING and not is_running:
            self.state = DONE
            logger.info(f"Job Id: {self.job_id} DONE")

    def submit(self, gpu_idx) -> asyncio.subprocess.Process:
        python_cmd = f"env CUDA_VISIBLE_DEVICES={gpu_idx} {self.cmd} 2>| {self.errlog}"
        cmd = f'tmux new-session -s {self.session_name} -d "{python_cmd}"'
        coro = asyncio.create_subprocess_shell(cmd)
        self.state = RUNNING
        self.gpu_idx = gpu_idx
        logger.info(f"Job Id: {self.job_id} SUBMITTED")
        self.cast_err()
        return coro

    @fire_and_forget
    def cast_err(self):
        is_initial = True
        for line in sh.tail("-f", self.errlog, f"--pid={os.getgid()}", _iter=True):
            if is_initial:
                logger.warning(f"Job Id: {self.job_id} DIED")
                rich.print(f"[bold red]Job Id: {self.job_id} DIED")
                is_initial = False
            print(line, end="")

    @property
    def session_name(self):
        return f"gpuslot-{self.job_id}"

    @property
    def is_running(self):
        return self.state == RUNNING


def _initialize_jobs(jobs: Dict[str, str]) -> deque:
    job_que = deque()
    for job_id, cmd in jobs.items():
        job = GpuHostedJob(job_id, cmd)
        job_que.append(job)
    return job_que


def _gather_using_gpu_indices(jobs: Deque[GpuHostedJob]) -> Set[int]:
    own_using_gpus = set()
    for job in jobs:
        if job.is_running:
            own_using_gpus.add(job.gpu_idx)
    return own_using_gpus


def _find_available_gpu_indices() -> Set[int]:
    available_gpu_indices = set()
    num_gpus = pynvml.nvmlDeviceGetCount()

    for gpu_idx in range(num_gpus):
        handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_idx)
        nv_processes = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
        if len(nv_processes) == 0:
            available_gpu_indices.add(gpu_idx)

    return available_gpu_indices


def _check_exist_running_job(job_que: Deque[GpuHostedJob]) -> bool:
    exist_running_job = False
    for job in job_que:
        exist_running_job = exist_running_job or job.is_running
    return exist_running_job


def _generate_status_table(jobs: Deque[GpuHostedJob]) -> Table:
    palette = {RUNNING: "red", DONE: "green", PENDING: "grey30"}

    table = Table("", "Job Id", "Status", "GPU", box=box.HORIZONTALS, show_edge=False)
    for job in jobs:
        state = job.state
        job_id = job.job_id
        color = palette[state]
        progress_icon = spinner.Spinner("arrow3", style="red") if job.is_running else ""
        table.add_row(progress_icon, job_id, f"[{color}]{state}", f"{job.gpu_idx}")
    return table


async def wait_and_submit(
    jobs: Dict[str, str],
    num_alloc_gpus: int = 1,
    interval: float = 1.0,
) -> None:
    job_que = _initialize_jobs(jobs)
    submitted_que = deque()

    with Live(_generate_status_table(job_que), refresh_per_second=20) as live:
        while job_que or _check_exist_running_job(submitted_que):
            available_gpu_indices = _find_available_gpu_indices()
            own_using_gpu_indices = _gather_using_gpu_indices(submitted_que)
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
            live.update(_generate_status_table(submitted_que + job_que))
    logger.info("Completed all jobs")
