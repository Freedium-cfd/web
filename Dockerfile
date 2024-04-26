FROM debian:bullseye-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3 python3-pip curl && \
    apt-get clean

COPY ./requirements.txt ./
COPY ./requirements-fast.txt ./

COPY ./server ./server
COPY ./core ./core
COPY ./rl_string_helper ./rl_string_helper
COPY ./database-lib ./database-lib

COPY ./other/sqlite_zstd-0.1.dev1+g5aaeb60-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl ./

RUN pip install --no-cache-dir wheel

RUN pip3 install --no-cache-dir ./rl_string_helper
RUN pip3 install --no-cache-dir ./database-lib
RUN pip3 install --no-cache-dir ./core

RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir -r requirements-fast.txt

RUN pip3 install --no-cache-dir sqlite_zstd-0.1.dev1+g5aaeb60-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl

EXPOSE 7080

CMD ["python3", "-m", "server", "server"]