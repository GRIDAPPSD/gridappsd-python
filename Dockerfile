# Use latest slim Python image. Note that it's built on Debian Stretch.
FROM python:slim

ENV GRIDAPPSD_URI="tcp://gridappsd:61613"
ENV GRIDAPPSD_USER="system"
ENV GRIDAPPSD_PASS="manager"

#RUN pip --upgrade pip

WORKDIR /usr/src/gridappsd-python

COPY requirements.txt ./
##RUN pip3 install -U pip setuptools wheel
##RUN pip3 install ruamel.yaml
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install .

CMD ["python", "/usr/src/gridappsd-python/register_app.py"]
