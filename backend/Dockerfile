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
>>>>>>> 319d91559032a2cba16da701d156d4085b873667
