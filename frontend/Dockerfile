# base image on required python build
FROM python:3.10.8

# expose port 3000 to outside of container
EXPOSE 3000

# set working dir within image
WORKDIR /frontend

# copy current dir contents into image dir
ADD /frontend /frontend

# pip install requirements
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# run web app
CMD ["flask", "run"]