FROM mcr.microsoft.com/playwright/python:v1.52.0-noble

WORKDIR /usr/src/app

# Dependencies for Playwright headed chromium. xvfb is used for more_com crawler to emulate user scrolling
RUN apt-get update && apt-get install -y \
    xvfb \
    libgtk-3-0 \
    libx11-xcb1 \
    libnss3 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libasound2t64 \
    libxss1 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create a directory for persistent data
RUN mkdir /data

COPY . .

CMD bash -c "xvfb-run -a -s '-screen 0 1920x1080x24' python ./main.py"