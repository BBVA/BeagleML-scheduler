FROM python:3.5.4@sha256:47e3dc72fcd066d926f955ff2339d7cde8e3c6d2010fb26a8832ec847fc2dfd2

ENV PATH="/opt/scheduler/exec:${PATH}"

WORKDIR /tmp

# Librdkafka v0.11.0
RUN git clone https://github.com/edenhill/librdkafka.git && \
    cd /tmp/librdkafka/ && \
    git checkout v0.11.0 && \
    ./configure && \
    make && \
    make install && \
    ldconfig

# Upgrade curl to > 7.40 + libcurl
RUN wget http://curl.haxx.se/download/curl-7.50.3.tar.gz && \
    tar -xvf curl-7.50.3.tar.gz && \
    cd curl-7.50.3/ && \
    ./configure && \
    make && \
    make install && \
    sed -i '1i/usr/lib' /etc/ld.so.conf.d/libc.conf && \
    ldconfig

# Requirements to install SCIPY
# https://talk.plesk.com/threads/problem-with-apt-ubuntu-16-04.341306/
# https://askubuntu.com/questions/623578/installing-blas-and-lapack-packages
RUN chmod 1777 /tmp && \
    apt-get update && \
    apt-get install -y libblas-dev liblapack-dev gfortran && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir /root/.kube

COPY . /opt
WORKDIR /opt

RUN pip install -r requirements.txt
RUN python setup.py install --user

EXPOSE 5000
