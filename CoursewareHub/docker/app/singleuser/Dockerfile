FROM niicloudoperation/notebook:latest

USER root

# disable extention / kernels
RUN jupyter wrapper-kernelspec remove -f bash && \
    jupyter nbextension disable --py lc_run_through --sys-prefix

# timezone
RUN ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata

USER $NB_USER
