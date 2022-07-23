from setuptools import setup

install_requires = ["pynvml", "rich", "sh", "omegaconf"]

setup(
    name="submas",
    version="1.0",
    description="Job submitter",
    author="Yoichiro Hisadome",
    author_email="hisadome0406@gmail.com",
    entry_points={
        "console_scripts": ["submas=submas:main"],
    },
    install_requires=install_requires,
    packages=["submas"],
)
