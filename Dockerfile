FROM jenkins/jenkins:lts

USER root
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install semgrep bandit

USER jenkins
