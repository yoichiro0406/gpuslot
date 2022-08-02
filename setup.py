from setuptools import setup

setup(
    name="gpuslot",
    version="1.0",
    description="Job submitter for gpus",
    author="Yoichiro Hisadome",
    author_email="hisadome0406@gmail.com",
    entry_points={
        "console_scripts": ["gpuslot=gpuslot:main"],
    },
    url="https://github.com/yoichiro0406/gpuslot",
    install_requires=["pynvml", "rich", "omegaconf", "loguru", "click"],
    packages=["gpuslot"],
)
