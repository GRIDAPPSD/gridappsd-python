# Use latest slim Python image. Note that it's built on Debian Stretch.
FROM python:3.7-slim

ENV GRIDAPPSD_PORT="61613"
ENV GRIDAPPSD_URI="tcp://gridappsd:${GRIDAPPSD_PORT}"
ENV GRIDAPPSD_USER=""
ENV GRIDAPPSD_PASSWORD=""

RUN pip install --upgrade pip

WORKDIR /usr/src/gridappsd-python

COPY requirements.txt ./
##RUN pip3 install -U pip setuptools wheel
##RUN pip3 install ruamel.yaml
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install .

CMD ["python", "/usr/src/gridappsd-python/register_app.py"]
