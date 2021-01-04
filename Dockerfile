FROM python:3.8.7-slim-buster

# set workdir to myapp
WORKDIR /myapp
# copy stuff
COPY . .
# install application
RUN pip install .

# overwrite python entryoint from base image
ENTRYPOINT [ "strava_collect" ]
