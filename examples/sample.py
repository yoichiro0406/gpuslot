import argparse
import time

import torch


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_sleep", type=int)
    args, _ = parser.parse_known_args()
    return args


def sample_run(num_sleep: int, device: str):
    sample_tensor = torch.rand(1000, 1000)
    sample_tensor.to(device)
    res = sample_tensor @ sample_tensor
    time.sleep(num_sleep)


if __name__ == "__main__":
    args = get_args()
    sample_run(args.num_sleep, "cuda:0")
