FROM ubuntu
# System wide deps
RUN apt-get update; apt-get install --yes python3 \
                                          python3-dev \
                                          python3-pip \
                                          supervisor \
                                          iputils-ping \
                                          make

WORKDIR "/agent"
RUN mkdir logs

# Application deps
ADD requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
ADD supervisor/agent_mock/supervisord.conf.ini supervisord.conf.ini

ADD lorawan lorawan
ADD conformance_testing conformance_testing
ADD parameters parameters
ADD utils.py utils.py
ADD message_queueing.py message_queueing.py
ADD user_interface user_interface
ADD testing_tool_conf.json testing_tool_conf.json
RUN python3 -m pip install lorawan/user_side_mock/messenger/

# Define environment variables
ENV PYTHONPATH /agent/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

