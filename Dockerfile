FROM python:3.12.3-slim

WORKDIR /app

COPY ./requirements.txt ./
COPY ./requirements-fast.txt ./

COPY ./server ./server
COPY ./core ./core
COPY ./rl_string_helper ./rl_string_helper
COPY ./database-lib ./database-lib

RUN pip install --no-cache-dir wheel

RUN pip3 install --no-cache-dir ./rl_string_helper
RUN pip3 install --no-cache-dir ./database-lib
RUN pip3 install --no-cache-dir ./core

RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir -r requirements-fast.txt

EXPOSE 7080

CMD ["python3", "-m", "server", "server"]