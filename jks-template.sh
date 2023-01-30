#!/bin/bash
[ -n "${Jira_Url}" ] || exit 1
[ "${BUILD_USER_ID}"  != "ppmoney" ] || exit 1
#推送发布预告
[ "${start_notice}" == "yes" ] && sh /usr/local/scripts/publish_notice.sh SEND_DD_PREPARE ${Jira_Url} ${BUILD_USER}
#发布系统
#sh -x /data/scripts/jidai/jd-app.sh $JOB_NAME ${branch}


# jenkins job名字，项目名
jenkins_name="${JOB_NAME}"
project_name="jd-app"

# 项目版本，若无，则传入时间戳
if [ "${Rollback}" == "yes" ];then
project_version=${Rollback_tag}
else
#project_version=`date +%Y%m%d%H%M`
project_version="${branch}"
fi

# 传送至发布机的类型，文件/文件夹
#copy_option=file|dir
copy_option=file
 
# 发布机推送至服务器的类型
#option=war|jar|dir
option=war


# 发布jar/war需要定义以下变量
project_local_updatepath="/data/jenkins/workspace/${jenkins_name}/${project_name}/target"

# 本地jenkins构建jar/war文件的路径
the_local_filename="$(ls ${project_local_updatepath}/*.war)"

# 本地jenkins构建jar/war文件被重命名后的名字，默认$project_name
the_modified_filename="$project_local_updatepath/${project_name}.war"


# 应用服务器，若有多个，用":"隔开
#remote_server=az-prd-jd-web01.haomoney.local:az-prd-jd-web04.haomoney.local:az-prd-jd-web06.haomoney.local:az-prd-jd-web07.haomoney.local

# app/tomcat 目录
remote_project_path=/data/web/tomcat7_jd_app01

# 发布war时，tomcat webapps软链接名字，默认project_name；发布jar也无需注释
soft_link_name=$project_name

# copy 文件参数（可选）
# 源文件（绝对路径），目的文件（绝对路径）
#the_src_file=/data/update/jd-app/config/logback.xml
#the_dest_file=/data/web/tomcat7_jd_app01/webapps/jd-app/WEB-INF/classes/logback.xml


# 修改文件参数（可选）
#the_file_path=$remote_project_path/webapps/$project_name/WEB-INF/classes/application.properties
#the_regexp_line="spring.profiles.active=.*"
#the_new_line="spring.profiles.active=inte"


# 检查状态码参数（可选）
# 5个参数需一同定义，端口，等待端口开启超时时间，检测的url，检测超时时间，检测状态码
the_port=8080
port_timeout=300
the_check_url="http://127.0.0.1:8080/jd-app/"
timeout=300
status_code="200,302"

if [ "${Rollback}" != "yes" ];then
###################################
# 传送dir/jar/war至发布机
ansible-playbook /data/scripts/prd-copy-$copy_option.yaml \
-e "jenkins_name=$jenkins_name" \
-e "project_name=$project_name" \
-e "project_version=$project_version" \
-e "the_local_filename=$the_local_filename" \
-e "the_modified_filename=$the_modified_filename" \
-e "option=$option"
fi

# ssh发布机，远程执行playbook，发布至服务器
# 默认情况下，会以jdadmin进行ssh连接，并执行任务，若需改为root，则增加参数 -u root
ssh -p 22 jdadmin@40.73.116.55 \
ansible-playbook /data/scripts/prd-deploy-$option.yaml \
-e "remote_server=$remote_server" \
-e "project_name=$project_name" \
-e "project_version=$project_version" \
-e "remote_project_path=$remote_project_path" \
-e "soft_link_name=$soft_link_name" \
-e "the_port=$the_port" \
-e "port_timeout=$port_timeout" \
-e "the_check_url=$the_check_url" \
-e "timeout=$timeout" \
-e "status_code=$status_code" \
-e "Rollback=$Rollback"

#20181012:由于接了配置中心，取消这个替换操作
#-e "the_src_file=$the_src_file"  \
#-e "the_dest_file=$the_dest_file" \

#推送完成通知
if [ "$?" -eq "0" ];then
	[ "${finish_notice}" == "yes" ] && sh /usr/local/scripts/publish_notice.sh SEND_DD_FINISHED ${Jira_Url} ${BUILD_USER} || echo "finish_notice=${finish_notice}"
else
	exit 1
fi


#获取应用服务器的tag列表存到本地：
set +x
ssh -p 22 jdadmin@40.73.116.55 "ssh jdadmin@`echo $remote_server|awk -F: '{print $1}'` ls -t /data/update/${project_name}"|xargs|tr ' ' ','|sed 's/^/tag=&/g' >/data/scripts/server_tag_list/${JOB_NAME}.txt
set -x
