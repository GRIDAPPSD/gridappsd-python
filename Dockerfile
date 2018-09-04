FROM python:3.5-jessie

#RUN pip --upgrade pip

WORKDIR /usr/src/gridappsd-python

COPY requirements.txt ./
##RUN pip3 install -U pip setuptools wheel
##RUN pip3 install ruamel.yaml
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install .

CMD ["python", "/usr/src/gridappsd-python/register_app.py"]