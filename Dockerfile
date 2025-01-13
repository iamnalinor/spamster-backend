FROM python:3.12.1-alpine
WORKDIR /app
STOPSIGNAL SIGKILL
EXPOSE 8080

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /app

RUN chmod +x /app/etc/entrypoint*.sh
RUN dos2unix /app/etc/entrypoint*.sh

CMD ["/app/etc/entrypoint.sh"]