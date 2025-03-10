FROM wrenchproject/wrench:unstable
USER root

RUN apt-get update && apt-get install -y curl

# Install WRENCH API v0.4
RUN apt-get -y install zip
RUN python3 -m pip install build
RUN wget https://github.com/wrench-project/wrench-python-api/archive/refs/tags/v0.4.zip; unzip v0.4.zip; cd wrench-python-api-0.4; python3 -m build; python3 -m pip install ./dist/wrench-*.whl

# Install Node.js and nodemon
RUN python3 -m pip install uvicorn

COPY . .

RUN chmod +x ./start.bash

CMD ["./start.bash"] 