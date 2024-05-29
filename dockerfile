FROM python:3.12

ADD ./requirements.txt /

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install uvicorn python-multipart

ADD ./app /app

WORKDIR /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--loop", "asyncio"]