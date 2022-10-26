## BASE IMAGE
FROM ubuntu:20.04 AS build-stage

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
    
## ADD CONDA ENV PATH TO LINUX PATH (make sure to put your env name in place of "venv")
ENV PATH /opt/conda/envs/venv/bin:$PATH
ENV CONDA_DEFAULT_ENV venv

## MAKE ALL BELOW RUN COMMANDS USE THE NEW CONDA ENVIRONMENT
SHELL ["conda", "run", "-n", "venv", "/bin/bash", "-c"]

## INSTALL PIP DEPENDENCIES
RUN pip install -r /tmp/environment_pip.txt

## COPY REST OF THE FILES
COPY . .

FROM python:3.8.15

COPY --from=build-stage /opt/conda/. /opt/conda/
COPY --from=build-stage /ai-driven-avatar/src/. ai-driven-avatar/src
COPY --from=build-stage /ai-driven-avatar/config/. ai-driven-avatar/config
COPY --from=build-stage /ai-driven-avatar/assets/. ai-driven-avatar/assets

ENV PATH /opt/conda/envs/venv/bin:$PATH

## ENV SETTINGS FOR PYGAME
ENV SDL_VIDEODRIVER 'dummy'

## ADD YOUR PROJECT'S ROOT DIRECTORY TO PYTHONPATH
ENV PYTHONPATH /ai-driven-avatar:$PYTHONPATH

WORKDIR /ai-driven-avatar

## FINALLY TIME TO EXECUTE!
ENTRYPOINT ["python", "src/opengym/__main__.py"]
CMD ["-a", "ppo", "-t", "10000"]