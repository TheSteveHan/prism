FROM python:3.8.16
RUN  apt-get update
RUN  apt-get install -y libxmlsec1-dev 
RUN  apt-get install -y libev-dev 
RUN wget -O /usr/local/bin/dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.2.2/dumb-init_1.2.2_amd64
RUN chmod +x /usr/local/bin/dumb-init
RUN pip install pipenv
WORKDIR /app
COPY Pipfile* ./
RUN pipenv install --deploy --system
ADD . /app/
ENV DEBUG=False
ENTRYPOINT ["/usr/local/bin/dumb-init", "--", "./docker_entrypoint.sh"]
