#!/bin/bash
CONDA_BASE=$(conda info --base) && source $CONDA_BASE/etc/profile.d/conda.sh
conda activate foo && Rscript -e "install.packages(c('PMA','lme4'),repos='https://cloud.r-project.org')"