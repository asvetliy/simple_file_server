FROM python:3.9-slim

RUN groupadd pygroup && useradd -m -g pygroup -s /bin/bash pyuser
RUN mkdir -p /home/pyuser/app

COPY . /home/pyuser/app
WORKDIR /home/pyuser/app/app
RUN apt-get update && apt-get install -y gcc git gettext
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r /home/pyuser/app/app/requirements.txt
RUN chown -R pyuser:pygroup /home/pyuser

USER pyuser

RUN mkdir /home/pyuser/app_data
RUN mkdir /home/pyuser/app_data/public
RUN mkdir /home/pyuser/app_data/media
RUN python /home/pyuser/app/app/manage.py collectstatic --clear --noinput
RUN python /home/pyuser/app/app/manage.py compilemessages -l en
RUN python /home/pyuser/app/app/manage.py compilemessages -l ru

CMD ["gunicorn", "app.wsgi"]