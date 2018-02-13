FROM centos:centos7
MAINTAINER Sergio Traldi <sergio.traldi@pd.infn.it>

RUN  yum localinstall -y http://repos.mesosphere.com/el/7/noarch/RPMS/mesosphere-el-repo-7-1.noarch.rpm
RUN  yum install -y mesos openssh wget python libnss3 curl gzip
RUN wget --no-cookies --no-check-certificate --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie" "http://download.oracle.com/otn-pub/java/jdk/8u161-b12/2f38c3b165be4555a1fa6e98c45e0808/jdk-8u161-linux-x64.tar.gz" -O /opt/jdk-8u161-linux-x64.tar.gz
RUN tar -zxf /opt/jdk-8u161-linux-x64.tar.gz -C /opt
RUN ln -sf /opt/jdk1.8.0_161 /opt/jdk
RUN rm -rf /opt/jdk-8u161-linux-x64.tar.gz
RUN echo "net.ipv6.conf.all.disable_ipv6 = 1" >> /etc/sysctl.conf
RUN echo "net.ipv6.conf.default.disable_ipv6 = 1" >> /etc/sysctl.conf
RUN chmod 777 /opt/
RUN wget http://www.eu.apache.org/dist/hadoop/common/hadoop-2.6.5/hadoop-2.6.5.tar.gz -O /opt/hadoop-2.6.5.tar.gz
RUN tar -zxf /opt/hadoop-2.6.5.tar.gz -C /opt
RUN ln -sf /opt/hadoop-2.6.5 /opt/hadoop
RUN rm -rf /opt/hadoop-2.6.5.tar.gz
RUN wget https://archive.apache.org/dist/spark/spark-2.1.0/spark-2.1.0-bin-hadoop2.6.tgz -O /opt/spark-2.1.0-bin-hadoop2.6.tgz
RUN tar -zxf /opt/spark-2.1.0-bin-hadoop2.6.tgz -C /opt
RUN ln -sf /opt/spark-2.1.0-bin-hadoop2.6 /opt/spark
RUN rm -rf /opt/spark-2.1.0-bin-hadoop2.6.tgz

COPY spark-conf/* /opt/spark/conf/
COPY scripts /scripts

ENV SPARKHOME /opt/spark

ENTRYPOINT ["/scripts/run.sh"]
