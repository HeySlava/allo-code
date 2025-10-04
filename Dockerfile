FROM python:3.11-slim-bullseye

WORKDIR /opt

ENV PATH=/venv/bin:$PATH

COPY ./setup.py ./setup.cfg ./
COPY ./allo.py ./allo.py

RUN :\
    && python -m venv /venv \
    && pip install --no-cache-dir pip -U wheel setuptools . \
    && :

CMD ["allo-code"]
