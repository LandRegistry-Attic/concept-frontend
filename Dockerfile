FROM orchardup/python:2.7
RUN apt-get update -qq && apt-get install -yq ruby-sass
ADD requirements.txt /code/
WORKDIR /code
RUN pip install -r requirements.txt
ADD . /code
