import asyncio
from collections import deque
from typing import Dict, Set

import pynvml
from loguru import logger

from .status import *
from .tmux import get_tmux_sessions


class GpuHostedTask:
    def __init__(self, job_id: str, cmd: str):
        self.job_id = job_id
        self.cmd = cmd
        self.state = PENDING
        self.gpu_idx = ""

    def update_state(self):
        sessions = get_tmux_sessions()
        is_running = self.session_name in sessions
        if self.state == RUNNING and not is_running:
            self.state = DONE
            logger.info(f"Job Id: {self.job_id} DONE")

    def submit(self, gpu_idx) -> asyncio.subprocess.Process:
        python_cmd = f"env CUDA_VISIBLE_DEVICES={gpu_idx} {self.cmd}"
        cmd = f"tmux new-session -s {self.session_name} -d {python_cmd}"
        coro = asyncio.create_subprocess_shell(cmd)
        self.state = RUNNING
        self.gpu_idx = gpu_idx
        logger.info(f"Job Id: {self.job_id} SUBMITTED")
        return coro

    @property
    def session_name(self):
        return f"submas-{self.job_id}"

    @property
    def is_running(self):
        return self.state == RUNNING


def initialize_jobs(jobs: Dict[str, str]) -> deque:
    job_que = deque()
    for job_id, cmd in jobs.items():
        job = GpuHostedTask(job_id, cmd)
        job_que.append(job)
    return job_que


def gather_using_gpu_indices(jobs: GpuHostedTask) -> Set[int]:
    own_using_gpus = set()
    for job in jobs:
        if job.is_running:
            own_using_gpus.add(job.gpu_idx)
    return own_using_gpus


def find_available_gpu_indices() -> Set[int]:
    available_gpu_indices = set()
    num_gpus = pynvml.nvmlDeviceGetCount()

    for gpu_idx in range(num_gpus):
        handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_idx)
        nv_processes = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
        if len(nv_processes) == 0:
            available_gpu_indices.add(gpu_idx)

    return available_gpu_indices


def check_exist_running_job(job_que: deque) -> bool:
    exist_running_job = False
    for job in job_que:
        exist_running_job = exist_running_job or job.is_running
    return exist_running_job
