FROM bitnami/odoo:12.0.20210915-debian-10-r40

ARG BRANCH_NAME=new-requirements
ARG OPENG2P_CA_REPO=https://github.com/OpenG2P/openg2p-erp-community-addon
ARG OPENG2P_CA_BRANCH=master
ARG OPENG2P_ERP_REPO=https://github.com/OpenG2P/openg2p-erp
ARG OPENG2P_ERP_BRANCH=master


RUN install_packages wget unzip
RUN . /opt/bitnami/odoo/venv/bin/activate && \
    python3 -m pip install -r https://raw.githubusercontent.com/truthfool/openg2p-erp/$BRANCH_NAME/requirements.txt && \
    deactivate

RUN rm -rf /tmp/openg2p-erp* &&\
    curl -L -o /tmp/openg2p-erp-community-addon.zip $OPENG2P_CA_REPO/archive/$OPENG2P_CA_BRANCH.zip &&\
    curl -L -o /tmp/openg2p-erp.zip $OPENG2P_ERP_REPO/archive/$OPENG2P_ERP_BRANCH.zip &&\
    unzip /tmp/openg2p-erp-community-addon.zip -d /tmp &&\
    unzip /tmp/openg2p-erp.zip -d /tmp
