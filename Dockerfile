FROM orchardup/python:2.7
ADD requirements.txt /code/
WORKDIR /code
RUN pip install -r requirements.txt
ADD . /code
