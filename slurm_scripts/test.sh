#!/bin/bash
#SBATCH --job-name=test_job       # Job name
#SBATCH --partition=teramem_inter # Partition (queue)
#SBATCH --nodes=1                 # Number of nodes
#SBATCH --ntasks=1                # Number of tasks
#SBATCH --cpus-per-task=1         # Number of CPU cores per task
#SBATCH --mem=5G                  # Memory (RAM) requested
#SBATCH --time=00:00:10           # Time limit 10 seconds (HH:MM:SS)
#SBATCH --output=test_job_%j.out  # Output file name (%j expands to jobID)
#SBATCH --error=test_job_%j.err   # Error file name (%j expands to jobID)

# Load required modules (optional, depending on environment)
# module load ...

# Commands to run
echo "Running a test job on Teramem cluster"
sleep 5  # Simulates a simple task
echo "Job finished successfully!"

