# Use an official Python runtime as a parent image
FROM ubuntu:16.04

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app

RUN mkdir -p /app/softwares
RUN mkdir -p /app/softwares/openmpi
RUN mkdir -p /app/softwares/java
RUN mkdir -p /app/softwares/bazel

RUN apt-get clean
RUN apt-get update

RUN apt-get install -qy git
RUN apt-get install -qy locales
RUN apt-get install -qy vim
RUN apt-get install -qy tmux
RUN apt-get install -qy wget
RUN apt-get install -y g++
RUN apt-get install -qy software-properties-common python-software-properties
RUN apt-get install -y python-dev python-pip
RUN apt-get install -qy zip
RUN apt-get install -qy unzip

RUN apt-get -qy autoremove

RUN \
  echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
  add-apt-repository -y ppa:webupd8team/java && \
  apt-get update && \
  apt-get install -y oracle-java8-installer && \
  rm -rf /var/lib/apt/lists/* && \
  rm -rf /var/cache/oracle-jdk8-installer

#http://mirrors.kernel.org/ubuntu/pool/main/z/zlib/zlib1g_1.2.8.dfsg-1ubuntu1_amd64.deb
#http://mirrors.kernel.org/ubuntu/pool/main/z/zlib/zlib1g-dev_1.2.8.dfsg-1ubuntu1_amd64.deb

# Define commonly used JAVA_HOME variable

ENV JAVA_HOME /usr/lib/jvm/java-8-oracle

#RUN apt-get install pkg-config zip g++ zlib1g-dev unzip python

RUN wget https://github.com/bazelbuild/bazel/releases/download/0.8.1/bazel-0.8.1-installer-linux-x86_64.sh -P /app/softwares/bazel
RUN cd /app/softwares/bazel/
RUN chmod +x /app/softwares/bazel/bazel-0.8.1-installer-linux-x86_64.sh
RUN ./softwares/bazel/bazel-0.8.1-installer-linux-x86_64.sh --user
#RUN echo export PATH="$PATH:$HOME/bin"" > ./profile.bash

ENV BAZEL_HOME ~/bin/bazel

#RUN wget https://github.com/bazelbuild/bazel/releases/download/0.8.1/bazel_0.8.1-linux-x86_64.deb -P /app/softwares/bazel/
#sha256sum -c tools/bazel_0.8.1-linux-x86_64.deb.sha256
#  - sudo dpkg -i bazel_0.8.1-linux-x86_64.deb
#  - echo "Installing C++ and Python"
#  - sudo apt-get install g++
#  - sudo apt-get install  python-dev python-pip

#CMD ["ls", "/app/softwares"]

#CMD ["ls", "/app/softwares/java"]

RUN mkdir -p /app/bashes

COPY bashes /app/bashes

RUN /bin/bash -c "source /app/bashes/profile.bash"

RUN wget https://www.open-mpi.org/software/ompi/v3.0/downloads/openmpi-3.0.0.tar.gz -P /app/softwares/openmpi/
RUN tar -xzvf /app/softwares/openmpi/openmpi-3.0.0.tar.gz -C /app/softwares/openmpi
RUN mkdir -p /app/build
WORKDIR /app/softwares/openmpi/openmpi-3.0.0 
RUN ./configure --prefix=/app/build --enable-mpi-java 
RUN make -j 8 
RUN make install
RUN export BUILD=/app/build
RUN export OMPI_300=/app/softwares/openmpi/openmpi-3.0.0
RUN export PATH=$BUILD/bin:$PATH
RUN export LD_LIBRARY_PATH=$BUILD/lib:$LD_LIBRARY_PATH
RUN useradd -ms /bin/bash twister2
RUN usermod -aG sudo twister2
RUN echo "root:root" | chpasswd
RUN su - twister2
RUN mkdir -p /app/sandbox/github
WORKDIR /app/twister2
#RUN "source /app/bashes/profile.bash"
#RUN "source /app/bashes/ompi.bash"

# YOUR TWISTER2 Working Directory
RUN mkdir -p /app/sandbox/github/local
COPY twister2 /app/sandbox/github/local/
