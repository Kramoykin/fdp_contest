FROM python:3.12

ADD ./requirements.txt /

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install uvicorn python-multipart

ADD ./app /app

WORKDIR /app

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--loop", "asyncio"]