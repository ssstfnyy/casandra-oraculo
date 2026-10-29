FROM ubuntu:24.04

ARG DUSER=casandra
ARG DGROUP=staff
ARG CASANDRA_LIBS=casandra_libs

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Santiago
ENV PIP_ROOT_USER_ACTION=ignore

ENV TF_CPP_MIN_LOG_LEVEL=3
ENV TF_ENABLE_ONEDNN_OPTS=0

RUN apt update && \
    apt upgrade --yes

RUN apt install --yes --no-install-recommends software-properties-common adduser sudo

RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install --yes --no-install-recommends python3.11 python3-pip

RUN pip3 install --break-system-packages \
    joblib pandas tensorflow scikit-learn tqdm openpyxl matplotlib

RUN apt autoremove -y && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN adduser --gecos "" --disabled-password --ingroup $DGROUP $DUSER \
    && adduser $DUSER sudo \
    && echo "$DUSER ALL=(ALL) NOPASSWD: ALL" >/etc/sudoers.d/$DUSER \
    && chmod 0440 /etc/sudoers.d/$DUSER

EXPOSE 10800
USER ${DUSER}
WORKDIR /home/${DUSER}

COPY --chown=$DUSER:staff broker.py ./
COPY --chown=$DUSER:staff $CASANDRA_LIBS/*.py ./$CASANDRA_LIBS/
# NUEVO (version02): se incluye el modelo entrenado en la imagen, para que el
# servicio de predicción funcione sin montar volúmenes.
COPY --chown=$DUSER:staff $CASANDRA_LIBS/training_model/ ./$CASANDRA_LIBS/training_model/

VOLUME ./$CASANDRA_LIBS/training_data
VOLUME ./$CASANDRA_LIBS/training_model


ENTRYPOINT ["python3","broker.py"]
