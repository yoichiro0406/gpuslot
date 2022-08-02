import asyncio
import os
import time

import click
import pynvml
from loguru import logger
from omegaconf import OmegaConf

from .core import wait_and_submit
from .status import *
from .tmux import get_tmux_sessions, kill_session


def setup_custom_resolver():
    def yaml_datetime():
        if not hasattr(yaml_datetime, "exp_datetime"):
            exp_datetime = time.strftime("%Y_%m%d_%H%M")
            yaml_datetime.exp_datetime = exp_datetime
        return yaml_datetime.exp_datetime

    OmegaConf.register_new_resolver("open", lambda path: OmegaConf.load(path))
    OmegaConf.register_new_resolver("datetime", yaml_datetime)
    OmegaConf.register_new_resolver("join", lambda a, b: os.path.join(a, b))


@click.group()
def main():
    pass


@main.command()
@click.option("--cfg")
@click.option("-n", "--num-gpus", type=int)
@click.option("--log_path", default="gpuslot.log")
def run(cfg, num_gpus, log_path):
    logger.configure(handlers=[{"sink": log_path}])
    pynvml.nvmlInit()
    setup_custom_resolver()
    cfg = OmegaConf.load(cfg)
    asyncio.run(wait_and_submit(cfg.jobs, num_gpus))


@main.command()
@click.option("--log_path", default="gpuslot.log")
def kill_all(log_path):
    logger.add(log_path)
    sessions = get_tmux_sessions()
    for session in sessions:
        if session.startswith("gpuslot-"):
            kill_session(session)
            logger.info(f"{session} killed")
