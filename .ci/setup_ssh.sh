#!/usr/bin/env /bash

set -e

##########################################################
# The setup_ssh script does the following:
#
#  - Sets up key-based SSH login, and
#    installs the private keys, so
#    we can connect to servers.
#
#  - Configures git, and adds the
#    upstream repo as a remote
#
# (see https://docs.gitlab.com/ce/ci/ssh_keys/README.html)
#
# NOTE: It is assumed that non-docker
#       executors are already configured
#       (or don't need any configuration).
##########################################################

if [[ -f /.dockerenv ]]; then

 apt-get update -y                           || yum -y check-update                     || true;
 apt-get install -y openssh-client rsync git || yum install -y openssh-client rsync git || true;

 eval $(ssh-agent -s);
 mkdir -p $HOME/.ssh;

 echo "$SSH_PRIVATE_KEY_GIT"          > $HOME/.ssh/id_git;
 echo "$SSH_PRIVATE_KEY_FSL_DOWNLOAD" > $HOME/.ssh/id_fsl_download;

 if [[ "$CI_PROJECT_PATH" == "$UPSTREAM_PROJECT" ]]; then
   echo "$SSH_PRIVATE_KEY_DOC_DEPLOY"  > $HOME/.ssh/id_doc_deploy;
 fi;

 chmod go-rwx $HOME/.ssh/id_*;

 ssh-add $HOME/.ssh/id_git;
 ssh-add $HOME/.ssh/id_fsl_download;

 if [[ "$CI_PROJECT_PATH" == "$UPSTREAM_PROJECT" ]]; then
   ssh-add $HOME/.ssh/id_doc_deploy;
 fi

 ssh-keyscan ${UPSTREAM_URL##*@} >> $HOME/.ssh/known_hosts;
 ssh-keyscan ${DOC_HOST##*@}     >> $HOME/.ssh/known_hosts;
 ssh-keyscan ${FSL_HOST##*@}     >> $HOME/.ssh/known_hosts;

 touch $HOME/.ssh/config;

 echo "Host ${UPSTREAM_URL##*@}"                    >> $HOME/.ssh/config;
 echo "    User ${UPSTREAM_URL%@*}"                 >> $HOME/.ssh/config;
 echo "    IdentityFile $HOME/.ssh/id_git"          >> $HOME/.ssh/config;

 echo "Host docdeploy"                              >> $HOME/.ssh/config;
 echo "    HostName ${DOC_HOST##*@}"                >> $HOME/.ssh/config;
 echo "    User ${DOC_HOST%@*}"                     >> $HOME/.ssh/config;
 echo "    IdentityFile $HOME/.ssh/id_doc_deploy"   >> $HOME/.ssh/config;

 echo "Host fsldownload"                            >> $HOME/.ssh/config;
 echo "    HostName ${FSL_HOST##*@}"                >> $HOME/.ssh/config;
 echo "    User ${FSL_HOST%@*}"                     >> $HOME/.ssh/config;
 echo "    IdentityFile $HOME/.ssh/id_fsl_download" >> $HOME/.ssh/config;

 echo "Host *"                                      >> $HOME/.ssh/config;
 echo "    IdentitiesOnly yes"                      >> $HOME/.ssh/config;

 git config --global user.name  "Gitlab CI";
 git config --global user.email "gitlabci@localhost";

 if [[ `git remote -v` == *"upstream"* ]]; then
     git remote remove upstream;
 fi;
 git remote add upstream "$UPSTREAM_URL:$UPSTREAM_PROJECT";
fi
