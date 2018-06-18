# Or bionic
FROM ubuntu:bionic
LABEL author="Bumsik Kim <k.bumsik@gmail.com>"

WORKDIR /app
CMD ["/bin/bash"]

RUN apt-get update && \
    apt-get install -y python3-all python3-pip python3-wheel fakeroot debmake debhelper fakeroot wget tar && \
    apt-get autoremove -y && \
    ln /usr/bin/python3 /usr/bin/python && \
    ln /usr/bin/pip3 /usr/bin/pip && \
    rm -rf /var/cache/apt/archives/*.deb && \
    pip install virtualenv && \
    pip install --upgrade pip setuptools

# Get Miniconda and make it the main Python interpreter
RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    bash ~/miniconda.sh -b -p ~/miniconda && \
    rm ~/miniconda.sh
