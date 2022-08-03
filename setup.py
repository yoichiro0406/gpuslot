from setuptools import setup


def read_readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="gpuslot",
    version="1.1",
    description="Job submitter for gpus",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Yoichiro Hisadome",
    author_email="hisadome0406@gmail.com",
    entry_points={
        "console_scripts": ["gpuslot=gpuslot:main"],
    },
    url="https://github.com/yoichiro0406/gpuslot",
    install_requires=["pynvml", "rich", "omegaconf", "loguru", "click", "sh"],
    license="MIT",
    packages=["gpuslot"],
)
