## BASE IMAGE
FROM ubuntu:20.04

## SET WORKING DIRECTORY
WORKDIR /ai-driven-avatar

RUN apt-get update -y \
    && apt-get install -y wget \
    && apt-get clean
    
## CONDA INSTALLATION --> use the latest Anaconda version for linux from their official website.
RUN rm -rf /opt/conda && \
    wget --quiet https://repo.anaconda.com/archive/Anaconda3-2022.10-Linux-x86_64.sh -O ~/anaconda.sh && \
    /bin/bash ~/anaconda.sh -b -p /opt/conda && \
    rm ~/anaconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    find /opt/conda/ -follow -type f -name '*.a' -delete && \
    find /opt/conda/ -follow -type f -name '*.js.map' -delete && \
    /opt/conda/bin/conda clean -afy
    
## ADD CONDA PATH TO LINUX PATH 
ENV PATH /opt/conda/bin:$PATH

## COPY ENV REQUIREMENTS FILES
COPY ./environment.yml /tmp/environment.yml
COPY ./environment_pip.txt /tmp/environment_pip.txt

## CREATE CONDA ENVIRONMENT USING YML FILE
RUN conda update conda \
    && conda env create -f /tmp/environment.yml
    
## ADD CONDA ENV PATH TO LINUX PATH 
ENV PATH /opt/conda/envs/venv/bin:$PATH
ENV CONDA_DEFAULT_ENV venv
# make sure to put your env name in place of "venv"

## MAKE ALL BELOW RUN COMMANDS USE THE NEW CONDA ENVIRONMENT
SHELL ["conda", "run", "-n", "venv", "/bin/bash", "-c"]

## INSTALL PIP DEPENDENCIES
RUN pip install -r /tmp/environment_pip.txt

## ENV SETTINGS FOR PYGAME
ENV SDL_VIDEODRIVER 'dummy'

## COPY REST OF THE FILES
COPY . .

## ADD YOUR PROJECT'S ROOT DIRECTORY TO PYTHONPATH
ENV PYTHONPATH /ai-driven-avatar:$PYTHONPATH

## FINALLY TIME TO EXECUTE!
ENTRYPOINT ["python", "src/opengym/__main__.py"]
CMD ["-a", "ppo", "-t", "10000"]