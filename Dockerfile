FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install
RUN playwright install-deps 

# Create a directory for persistent data
RUN mkdir /data

COPY . .

CMD [ "python", "./main.py" ]
