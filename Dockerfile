FROM public.ecr.aws/lambda/python:3.10

# installing the browser and the webdriver
RUN yum install -y wget unzip
RUN cd /tmp/ &&  \
wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm && \
yum localinstall -y google-chrome-stable_current_x86_64.rpm
RUN chromever=$(google-chrome-stable --version | awk -F " " '{print $3}') && \
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${chromever%.*} -O chromedriverver && \
wget https://chromedriver.storage.googleapis.com/$(cat chromedriverver)/chromedriver_linux64.zip && \
unzip chromedriver_linux64.zip && \
mv chromedriver /usr/bin/chromedriver
# installing requirements
# COPY app/requirements.txt  .
# RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# #copy the app code
# COPY ./app/app.py {$LAMBDA_TASK_ROOT}

# CMD ["app.lambda_handler"]

CMD ["usr/bin/sh"]