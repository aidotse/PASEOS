FROM ubuntu:22.10
ARG CONDA_PYTHON_VERSION=3
ARG USERNAME=user
ARG HOME=/home/user
ARG CONDA_DIR=$HOME/conda
ARG USERID=1000


# Create the user
RUN useradd --create-home -s /bin/bash --no-user-group -u $USERID $USERNAME 

# Instal basic utilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends git wget unzip bzip2 sudo build-essential ca-certificates && \
    apt-get install ffmpeg libsm6 libxext6  -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

## Install miniconda
ENV PATH $CONDA_DIR/bin:$PATH
RUN wget --quiet https://repo.continuum.io/miniconda/Miniconda$CONDA_PYTHON_VERSION-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    echo 'export PATH=$CONDA_DIR/bin:$PATH' > /etc/profile.d/conda.sh && \
    /bin/bash /tmp/miniconda.sh -b -p $CONDA_DIR && \
    rm -rf /tmp/*


RUN chown $USERNAME $HOME -R && \
    adduser $USERNAME sudo && \
    echo "$USERNAME ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER $USERNAME
WORKDIR /home/$USERNAME/paseos

# copy all files.
COPY . $HOME/paseos
    
#Install environment
RUN conda env create -f environment.yml

# For interactive shell
SHELL ["/bin/bash", "-c"]

RUN echo ". activate base" >> $HOME/.bashrc  && \ 
    chmod u+x $HOME/.bashrc && \ 
    $HOME/.bashrc

#
ENV PATH $HOME/conda/envs/env/bin:$PATH
