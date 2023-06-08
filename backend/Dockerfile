FROM python:3.9

WORKDIR /app

RUN pip install gunicorn==20.1.0

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

<<<<<<< HEAD
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]
=======
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]
>>>>>>> 0e04d57c313ea62c98b1a6361642b07b1dd7576d
