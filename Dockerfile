FROM public.ecr.aws/lambda/python:3.10-x86_64
WORKDIR /tmp
# installing the browser
RUN yum update -y && yum install -y wget unzip
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm && \
yum -y localinstall google-chrome-stable_current_x86_64.rpm && \
rm -rf google-chrome-stable_current_x86_64.rpm
# installing the chromedriver
RUN chromever=$(google-chrome-stable --version | awk -F " " '{print $3}') && \
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${chromever%.*} -O chromedriverver && \
wget https://chromedriver.storage.googleapis.com/$(cat chromedriverver)/chromedriver_linux64.zip && \
unzip chromedriver_linux64.zip && \
mv chromedriver /usr/bin/chromedriver && \
chmod +x /usr/bin/chromedriver && \
rm -rf chromedriver_linux64.zip
# installing requirements
COPY app/requirements.txt  .
COPY app/clientes.json ./mnt/
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# copy the app code
COPY app/app.py ${LAMBDA_TASK_ROOT}

CMD ["app.lambda_handler"]

# CMD ["usr/bin/sh"]