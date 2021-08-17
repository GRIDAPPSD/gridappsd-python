# Docker Environment for Applications

The Dockerfile in the gridappsd-python repository is the base for the
gridappsd/application-base-python:main container.  It is meant to extended for applications
to utilize.  An example of this is used in the
[gridappsd-sample-app](https://github.com/GRIDAPPSD/gridappsd-sample-app).

## Application Creation

Create a new directory to hold your application.  Please create a document structure as
in the gridappsd-sample-app above.

The following Dockerfile is the preferred way of allowing your application to self-register
with the gridappsd server.  Please follow the gridappsd-sample-app directory structure.

````
# Dockerfile from gridappsd-sample-app

# Use the base application container to allow the application to be controlled
# from the gridappsd container.
FROM gridappsd/app-container-base:main

# Add the TIMESTAMP variable to capture the build information from
# the travis docker build command and add them to the image.
ARG TIMESTAMP
RUN echo $TIMESTAMP > /dockerbuildversion.txt

# Pick a spot to put our application code
# (note gridappsd-python is located at /usr/src/gridappsd-python)
# and is already installed in the app-container-base environment.
WORKDIR /usr/src/gridappsd-sample

# Add dependencies to the requirements.txt file before
# uncommenting the next two lines
# COPY requirements.txt ./
# RUN RUN pip install --no-cache-dir -r requirements.txt

# Copy all of the source over to the container.
COPY . .

# Use a symbolic link to the sample app rather than having to
# mount it at run time (note can still be overriden in docker-compose file)
RUN ln -s /usr/src/gridappsd-sample/sample_app.config /appconfig
````
