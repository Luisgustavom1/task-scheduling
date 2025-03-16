FROM wrenchproject/wrench:unstable
USER root

RUN apt-get update && apt-get install -y curl zip python3-venv

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install build uvicorn

# Install WRENCH API v0.4
RUN wget https://github.com/wrench-project/wrench-python-api/archive/refs/tags/v0.4.zip; unzip v0.4.zip; cd wrench-python-api-0.4; python3 -m build; pip install ./dist/wrench-*.whl

COPY . .

RUN chmod +x ./start.bash

CMD bash ./start.bash