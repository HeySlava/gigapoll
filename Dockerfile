FROM python:3.11-slim-bullseye

WORKDIR /opt

ENV PATH=/venv/bin:$PATH

COPY ./setup.py ./setup.cfg ./
COPY ./gigapoll ./gigapoll

RUN :\
    && python -m venv /venv \
    && pip install --no-cache-dir pip -U wheel setuptools . \
    && :

WORKDIR /opt/gigapoll
CMD ["gigapoll"]
