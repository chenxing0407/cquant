FROM ubuntu:latest
ADD sources.list /etc/apt/
RUN mkdir /root/.pip
ADD pip.conf /root/.pip/

RUN apt update --fix-missing && apt install -y wget gcc make libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev && apt clean all

RUN wget https://www.python.org/ftp/python/3.6.3/Python-3.6.3.tar.xz && tar -xvf Python-3.6.3.tar.xz && cd Python-3.6.3 && ./configure --enable-optimizations && make build_all && make install && cd ../ && rm -rf Python-3.6.3  Python-3.6.3.tar.xz && find /usr/local/lib/python3.6/ -name "*pyc"  -delete

RUN pip3 install requests six && pip3 install aiohttp easyutils && pip3 install PyYAML PyMySQL SQLAlchemy pandas matplotlib  easyquotation easytrader && find /usr/local/lib/python3.6/ -name "*pyc"  -delete

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
