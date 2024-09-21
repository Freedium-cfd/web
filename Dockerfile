FROM python:3.12.3
# -slim

ENV DEBIAN_FRONTEND=noninteractive

RUN pip install poetry && poetry config virtualenvs.create false

WORKDIR /app

RUN pip install --no-cache-dir wheel Cython

COPY ./rl_string_helper ./rl_string_helper
RUN pip3 install --no-cache-dir ./rl_string_helper

COPY ./database-lib ./database-lib
RUN pip3 install --no-cache-dir ./database-lib

COPY ./medium-parser ./medium-parser
RUN pip3 install --no-cache-dir ./medium-parser

COPY ./web ./web

WORKDIR /app/web

RUN poetry install

# EXPOSE 7080

CMD ["python3", "-m", "server", "server"]
