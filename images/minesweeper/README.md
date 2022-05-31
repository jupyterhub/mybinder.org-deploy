# minesweeper docker image

docker image with basic dependencies for admin tasks on a kubernetes cluster
(ps, python, python-psutil, python-kubernetes)

## How to update requirements.txt

Because `pip-compile` resolves `requirements.txt` with the current Python for
the current platform, it should be run on the same Python version and platform
as our Dockerfile.

```shell
# run from images/minesweeper
# update requirements.txt based on requirements.in
docker run --rm \
    --env=CUSTOM_COMPILE_COMMAND="see README.md" \
    --volume=$PWD:/io \
    --workdir=/io \
    --user=root \
    python:3.9-slim-bullseye \
    sh -c 'pip install pip-tools==6.* && pip-compile --upgrade'
```
