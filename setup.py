from setuptools import setup

setup(
    name="submas",
    version="1.0",
    description="Job submitter",
    author="Yoichiro Hisadome",
    author_email="hisadome0406@gmail.com",
    entry_points={
        "console_scripts": ["submas=submas:main"],
    },
    install_requires=["pynvml", "rich", "sh", "omegaconf", "loguru", "click"],
    packages=["submas"],
)
