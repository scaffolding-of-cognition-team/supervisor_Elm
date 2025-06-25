#!/bin/sh
# Make a supervisor for sbatching the backup_Elm.py script
# This script will run for 7 days
#
# To run this, you will need a conda environment with the standard python libraries like pandas and numpy.
#
#SBATCH --job-name backup_Elm
#SBATCH --output logs/backup_Elm-%j.out
#SBATCH --time 7-0

# Get the conda information from the globals.sh file
source ./globals.sh

# Set up the conda environment
CONDA_BASE=$(conda info --base)
source $CONDA_BASE/etc/profile.d/conda.sh
conda activate $CONDA_ENV

echo "Starting backup_Elm supervisor script"

# Get the inputs to the function
backup_folder=$1
csv_path=$2
row=$3

# Run the backup script
python ./backup_Elm.py ${backup_folder} ${csv_path} ${row}

# Check the exit status of the script
if [ $? -ne 0 ]; then
    echo "backup_Elm.py script failed. Exiting supervisor script."
    exit 1
else
    echo "backup_Elm.py script completed successfully."
fi
