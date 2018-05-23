# Or bionic
FROM ubuntu:latest
LABEL author="Bumsik Kim <k.bumsik@gmail.com>"

WORKDIR /app
CMD ["/bin/bash"]

RUN apt-get update && \
    apt-get install -y python3-all python3-pip fakeroot debmake debhelper fakeroot wget tar && \
    apt-get autoremove -y && \
    ln /usr/bin/python3 /usr/bin/python && \
    ln /usr/bin/pip3 /usr/bin/pip && \
    rm -rf /var/cache/apt/archives/*.deb && \
    useradd -c Builder -m -U builder

USER builder
