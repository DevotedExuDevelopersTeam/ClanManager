FROM python:3.10-bullseye

ENV VIRTUAL_ENV=/app/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN sudo apt-get update
RUN sudo apt-get install -y libgl1-mesa-dev

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python"]
CMD ["bot.py"]
