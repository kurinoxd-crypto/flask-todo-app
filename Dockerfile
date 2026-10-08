FROM python:3.12.0b3-alpine3.18
COPY . /application
WORKDIR /application
COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt
EXPOSE 5000
CMD ["python", "app.py"]
