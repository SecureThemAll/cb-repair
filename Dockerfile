FROM ubuntu:20.04

ENV TZ=Europe
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Installing dependencies
RUN apt update \
  && apt -y upgrade \
  && apt install -y -q git build-essential libc6-dev libc6-dev-i386 curl gcc-multilib g++-multilib clang \
  python2.7 python-dev python3-pip python3-dev gdb cmake ssh apport

# Setup & Enable Password-less SSH Logon
RUN service ssh start && mkdir -p /var/run/sshd/ && mkdir /root/.ssh && chmod 700 /root/.ssh

RUN git clone https://github.com/SecureThemAll/cb-repair
WORKDIR /cb-repair

# Init benchmark
RUN ./init.sh; exit 0

#RUN python3 "./src/init.py" && ./src/cb_repair.py init_polls -v && service ssh restart
RUN service ssh start

#ENTRYPOINT ["./src/cb_repair.py"]
#CMD ["catalog", "-v"]
