FROM python:3.10
RUN wget -O /usr/local/bin/dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.2.2/dumb-init_1.2.2_amd64
RUN chmod +x /usr/local/bin/dumb-init
RUN pip install pipenv
RUN pip install typing_extensions
RUN apt-get update
RUN apt-get install -y libev-dev
WORKDIR /app
COPY Pipfile* ./
RUN pipenv install --deploy --system
RUN pipenv --clear
ADD . /app/
ENTRYPOINT ["/usr/local/bin/dumb-init", "--", "./run_prod_server.sh"]
