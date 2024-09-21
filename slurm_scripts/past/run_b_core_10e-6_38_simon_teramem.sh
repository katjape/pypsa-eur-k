#!/bin/bash

#SBATCH --job-name=job_b_core_10xe-6_38_simon_teramem
#SBATCH --output=/dss/dssfs02/lwp-dss-0001/pn39ci/pn39ci-dss-0000/MA_Git/slurm_error/b_core_10xe-6_38_simon_teramem.out
#SBATCH --error=/dss/dssfs02/lwp-dss-0001/pn39ci/pn39ci-dss-0000/MA_Git/slurm_error/b_core_10xe-6_38_simon_teramem.err
#SBATCH --get-user-env
#SBATCH --export=NONE
#SBATCH --time=230:00:00
#SBATCH --mem=900000M
#SBATCH --partition=teramem_inter
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=katja.pelzer@tum.de
# SBATCH --account=go73lez2


source /dss/dsshome1/01/go73lez2/.conda_init

# Load necessary modules
module load slurm_setup # has to be loaded for every slurm job

# Activate the mamba environment
echo "Activating mamba environment..."
mamba activate snakemake
mamba activate pypsa-eur

# Set up the Gurobi license and environment variables
export GRB_LICENSE_FILE="/dss/dssfs02/lwp-dss-0001/pn39ci/pn39ci-dss-0000/MA_Git/gurobi_licenses/gurobi_simon.lic"
export GUROBI_HOME="/dss/dsshome1/01/go73lez2/miniforge3/envs/pypsa-eur"
export PATH="${PATH}:${GUROBI_HOME}/bin"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${GUROBI_HOME}/lib"

# Navigate to the project directory
echo "Navigating to the project directory..."
cd /dss/dsshome1/01/go73lez2/MA_Git/pypsa-eur-k/ || { echo "Failed to navigate to project directory. Exiting."; exit 1; }

# Unlock Snakemake if necessary
snakemake --unlock
# snakemake --rerun-incomplete

# Run Snakemake with the specified config file
echo "Running Snakemake..."
snakemake -call all --configfile /dss/dssfs02/lwp-dss-0001/pn39ci/pn39ci-dss-0000/MA_Git/config/base/config.b_core_10e-6_38.yaml
if [ $? -ne 0 ]; then
    echo "Snakemake execution failed. Exiting."
    exit 1
fi

echo "Job completed successfully."


