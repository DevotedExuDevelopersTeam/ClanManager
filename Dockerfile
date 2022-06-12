FROM python:3.10-bullseye

RUN apt-get update -y
RUN apt-get install -y libgl1-mesa-dev
RUN pip install -U poetry

WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN poetry install

COPY . .

ENTRYPOINT ["poetry", "run", "python"]
CMD ["bot.py"]
