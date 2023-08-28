FROM python:3.9.2-slim-buster
RUN mkdir /app && chmod 777 /app
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
COPY . .
RUN apt -qq update && apt upgrade -y
RUN pip3 install telethon 
RUN pip3 install requests 
CMD [ "python3", "Bot 4.py" ]
