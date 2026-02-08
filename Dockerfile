FROM mambaorg/micromamba:1.5.10

WORKDIR /app

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /app/environment.yml
RUN micromamba create -y -n app -f /app/environment.yml \
  && micromamba clean --all --yes

ENV MAMBA_DOCKERFILE_ACTIVATE=1
SHELL ["/bin/bash", "-lc"]

COPY --chown=$MAMBA_USER:$MAMBA_USER . /app
CMD ["micromamba", "run", "-n", "app", "python", "-m", "scripts.run_cli"]
