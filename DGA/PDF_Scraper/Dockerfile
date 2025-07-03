# Stage 1: Build Stage
FROM python:3.11.4 AS build

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Create the directory for application
RUN mkdir -p /app/data
RUN mkdir -p /app/logs
RUN mkdir -p /app/models

    
# Install the required packages
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu


# install uWSGI
RUN pip install uwsgi

# Stage 2: Runtime Stage
FROM python:3.11-slim AS runtime

# # Install build-essential tools required for compiling uWSGI
# # RUN apt-get update && apt-get install -y build-essential
# # Install necessary dependencies
# # RUN apt-get update && apt-get install -y libxml2 libxml2-dev libssl-dev
# # RUN apt-get update && apt-get install -y libgomp1

# Install required dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    gettext-base

# # Set the working directory in the container
WORKDIR /app

# # Copy only the necessary files from the build stage
COPY --from=build /app /app
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /usr/local/bin/uwsgi /usr/local/bin/uwsgi
# # COPY --from=build /usr/lib/x86_64-linux-gnu/libxml2.so.2 /usr/lib/x86_64-linux-gnu/libxml2.so.2
# # COPY --from=build /usr/lib/x86_64-linux-gnu/libicuuc.so.72 /usr/lib/x86_64-linux-gnu/libicuuc.so.72
# # COPY --from=build /usr/lib/x86_64-linux-gnu/libicudata.so.72 /usr/lib/x86_64-linux-gnu/libicudata.so.72

# # Define the volume
VOLUME /app/data
VOLUME /app/logs
VOLUME /app/models
VOLUME /app/src


# setting up environment variable for hostname
# ENV HOSTNAME=localhost

# Expose the port uWSGI will listen on
EXPOSE 5101

# Ensure uWSGI is available in the final image
# RUN pip install uwsgi

# Run uWSGI using the configuration file
CMD ["uwsgi", "/app/src/deploy.ini"]