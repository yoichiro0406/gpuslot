# submas
Job submitter for shared lab gpu server

![demo.gif](demo.gif)

## Setup
```sh
pip install -e .
```

## Run
- run
```sh
cd examples
submas run --cfg job_list.yaml -n 3
```

- kill
```sh
submas kill-all
```
