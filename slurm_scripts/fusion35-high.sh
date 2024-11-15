#!/bin/bash

#SBATCH --job-name=job_fusion35-high
#SBATCH --output=/dss/dssfs02/lwp-dss-0001/pn39ci/pn39ci-dss-0000/MA_Git/slurm_error/fusion35-high.out
#SBATCH --error=/dss/dssfs02/lwp-dss-0001/pn39ci/pn39ci-dss-0000/MA_Git/slurm_error/fusion35-high.err
#SBATCH --get-user-env
#SBATCH --export=NONE
#SBATCH --time=240:00:00
#SBATCH --mem=950G
#SBATCH --partition=teramem_inter
#SBATCH --clusters=inter
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=katja.pelzer@tum.de
source /dss/dsshome1/00/ga27hek3/.conda_init

# Load necessary modules
module load slurm_setup # has to be loaded for every slurm job

# Activate the mamba environment
echo "Activating mamba environment..."
mamba activate snakemake
mamba activate pypsa-eur

# Set up the Gurobi license and environment variables
export GRB_LICENSE_FILE="/dss/dssfs02/lwp-dss-0001/pn39ci/pn39ci-dss-0000/MA_Git/gurobi_licenses/gurobi_koni.lic"
export GUROBI_HOME="/dss/dsshome1/0C/ge87say4/miniforge3/envs/pypsa-eur/lib/python3.12/site-packages/gurobi"
export PATH="${PATH}:${GUROBI_HOME}/bin"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${GUROBI_HOME}/lib"

# Navigate to the project directory
echo "Navigating to the project directory..."
cd /dss/dsshome1/00/ga27hek3/pypsa-eur-current/ || { echo "Failed to navigate to project directory. Exiting."; exit 1; }

# Unlock Snakemake if necessary
snakemake --unlock
#snakemake -call purge



# -------------------------------------------------------------------------------------------------------------------------------
# Scenarios 2025/30/35/40, Base costs, 0 CO2 in 2050
# -------------------------------------------------------------------------------------------------------------------------------
echo "Running Snakemake..."
snakemake -call all --configfile /dss/dssfs02/lwp-dss-0001/pn39ci/pn39ci-dss-0000/MA_Git/config/config.fusion35-high.yaml
if [ $? -ne 0 ]; then
    echo "Snakemake execution failed. Exiting."
    exit 1
fi

echo "Job completed successfully."
echo "Job completed successfully."