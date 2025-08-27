FROM mcr.microsoft.com/playwright/python:v1.52.0-noble

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create a directory for persistent data
RUN mkdir /data

COPY . .

CMD [ "python", "./main.py" ]
