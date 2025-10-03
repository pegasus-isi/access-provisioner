FROM debian:12

RUN apt update -y && \
    apt upgrade -y && \
    apt install -y \
         python3-dateutil \
         python3-pip \
         python3-venv \
    && \
    apt clean -y

RUN echo "deb [trusted=yes] https://research.cs.wisc.edu/htcondor/repo/debian/24.x bookworm main" >/etc/apt/sources.list.d/htcondor.list && \
    apt update -y && \
    apt install -y condor

RUN python3 -m venv /venv && \
    . /venv/bin/activate && \
    pip3 install \
          python-dateutil \
          htcondor \
          openstacksdk

COPY app /app

RUN chmod 755 /app/runme.sh

ENTRYPOINT ["/app/runme.sh"]

