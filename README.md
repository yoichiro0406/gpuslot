# gpuslot
[![PyPI version](https://badge.fury.io/py/gpuslot.svg)](https://badge.fury.io/py/gpuslot)
[![license](https://img.shields.io/github/license/yoichiro0406/gpuslot.svg?maxAge=86400)](LICENSE)

Job submitter for shared lab gpu server

![demo.gif](demo.gif)

## Install
```sh
pip install gpuslot
```

## Run
- run
```sh
cd examples
gpuslot run --cfg job_list.yaml -n 3
```

- kill
```sh
gpuslot kill-all
```
