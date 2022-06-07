# image_jdk/Dockerfile
---
FROM roboxes/centos8
MAINTAINER rocky "zhenhua.zhou@partner.sam.com"

RUN mkdir -p /iosp
ADD openjdk1.8.0_171/ /iosp/openjdk1.8.0_171/
ADD rotatelogs  /usr/sbin/rotatelogs
RUN chmod 755 /usr/sbin/rotatelogs

RUN yum install -y apr-util && \
    yum clean all && \
    rm -rf /var/cache/yum/*

ENV JAVA_HOME /iosp/openjdk1.8.0_171
ENV PATH $PATH:$JAVA_HOME/bin
ENV JRE_HOME $JAVA_HOME/jre
ENV CLASSPATH $JAVA_HOME/lib/:$JRE_HOME/lib/



# image_tomcat/Dockerfile
---
FROM scheckout-jdk8u171:v1
MAINTAINER rocky "zhenhua.zhou@partner.sam.com"

RUN mkdir -p /iosp/comp
ADD tomcat-8.5.72/ /iosp/tomcat-8.5.72/
ADD privacy-api-cn/ /iosp/comp/privacy-api-cn/


ADD docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

#DEPLOY CODE
ADD privacy-api.war /iosp/comp/privacy-api-cn/configuration/deploy/privacy-api.war
ADD config-prd.tar.gz /iosp/comp/privacy-api-cn/resources/config-prd.tar.gz


ENV CATALINA_HOME /iosp/tomcat-8.5.72
ENV CATALINA_BASE /iosp/comp/privacy-api-cn

ENTRYPOINT ["/docker-entrypoint.sh"]
