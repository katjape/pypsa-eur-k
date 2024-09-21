#!/bin/bash

#SBATCH --job-name=job_b_eu_10e-6_38_katja_serial
#SBATCH --output=/dss/dssfs02/lwp-dss-0001/pn39ci/pn39ci-dss-0000/MA_Git/slurm_error/b_eu_10e-6_38_katja_serial.out
#SBATCH --error=/dss/dssfs02/lwp-dss-0001/pn39ci/pn39ci-dss-0000/MA_Git/slurm_error/b_eu_10e-6_38_katja_serial.err
#SBATCH --get-user-env
#SBATCH --export=NONE
#SBATCH --time=480:00:00
#SBATCH --mem=55G
#SBATCH --partition=serial_long
#SBATCH --clusters=serial
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=katja.pelzer@tum.de

source /dss/dsshome1/05/ge87say3/.conda_init

# Load necessary modules
module load slurm_setup # has to be loaded for every slurm job

# Activate the mamba environment
echo "Activating mamba environment..."
mamba activate snakemake
mamba activate pypsa-eur

# Set up the Gurobi license and environment variables
export GRB_LICENSE_FILE="/dss/dssfs02/lwp-dss-0001/pn39ci/pn39ci-dss-0000/MA_Git/gurobi_licenses/gurobi_katja.lic"
export GUROBI_HOME="/dss/dsshome1/05/ge87say3/gurobi_install/gurobi1103/linux64"
export PATH="${PATH}:${GUROBI_HOME}/bin"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${GUROBI_HOME}/lib"

# Navigate to the project directory
echo "Navigating to the project directory..."
cd /dss/dsshome1/05/ge87say3/pypsa-eur-k-1/ || { echo "Failed to navigate to project directory. Exiting."; exit 1; }

# Unlock Snakemake if necessary
snakemake --unlock
snakemake --rerun-incomplete



# -------------------------------------------------------------------------------------------------------------------------------
# Job KA1 -  Reference scenario w/o fusion, 10e-6, All countries, 0 CO2, Base costs
# -------------------------------------------------------------------------------------------------------------------------------
echo "Running Snakemake..."
snakemake -call all --configfile /dss/dssfs02/lwp-dss-0001/pn39ci/pn39ci-dss-0000/MA_Git/config/base/config.b_eu_10e-6_38_ref.yaml
if [ $? -ne 0 ]; then
    echo "Snakemake execution failed. Exiting."
    exit 1
fi

echo "Job completed successfully."