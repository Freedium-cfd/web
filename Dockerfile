FROM python:3.12.3-slim

WORKDIR /app

RUN pip install --no-cache-dir wheel

COPY ./rl_string_helper ./rl_string_helper
RUN pip3 install --no-cache-dir ./rl_string_helper

COPY ./database-lib ./database-lib
RUN pip3 install --no-cache-dir ./database-lib

COPY ./core ./core
RUN pip3 install --no-cache-dir ./core

# COPY ./server ./server

COPY ./requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY ./requirements-fast.txt ./
RUN pip3 install --no-cache-dir -r requirements-fast.txt

EXPOSE 7080

CMD ["python3", "-m", "server", "server"]