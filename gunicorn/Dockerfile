FROM python:3.11

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

# RUN pip install gunicorn
# RUN apt-get update
# RUN apt-get install gunicorn -y

EXPOSE 80

CMD ["gunicorn", "-b", "0.0.0.0:80", "app:app"]
# CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]