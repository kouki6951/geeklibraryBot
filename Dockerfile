FROM shomaigu/flask-base:latest

RUN apt-get update
RUN apt-get -y install python3 python3-pip curl wget
RUN pip3 install --upgrade pip setuptools

# エリア選択時にビルドが停止してしまうのを回避
ENV DEBIAN_FRONTEND=noninteractive
RUN echo Asia/Tokyo > /etc/timezone
RUN apt-get install -y awscli
RUN mkdir -p /usr/src/app/templates
RUN mkdir -p /var/www/

ADD ./requirements.txt /usr/src/app/
ADD ./app.py /usr/src/app/
ADD ./wsgi.py /usr/src/app/
ADD ./templates /usr/src/app/templates
ADD ./uwsgi.ini /usr/src/app/
RUN pip3 install --no-cache-dir -r /usr/src/app/requirements.txt

# AWS認証情報ファイルコピー
RUN mkdir -p /root/.aws
RUN mkdir -p /root/.ssh
ADD ./.aws /root/.aws
ADD ./.ssh /root/.ssh

WORKDIR /usr/src/app/

CMD ["python3", "/usr/src/app/app.py"]
CMD ["uwsgi", "--ini", "/usr/src/app/uwsgi.ini"]

