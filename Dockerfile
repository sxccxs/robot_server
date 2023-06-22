FROM python:3.11.3

WORKDIR /
RUN set -xe
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    build-essential

RUN curl -sSL https://install.python-poetry.org | python3 - --git https://github.com/python-poetry/poetry.git@master
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-dev

COPY ./common ./common
COPY ./server ./server
COPY ./main.py ./
COPY ./logging_config.toml ./

RUN mkdir ./logs

EXPOSE 9999

CMD ["poetry", "run", "python", "./main.py"]