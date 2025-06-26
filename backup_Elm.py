## Run the backup of data to Elm
# Back up all the specified files to Elm as tar files
# This is expected to be run infrequently as it is slow and elm is slow
# To set this up, a variety of steps were needed like authorizing globus and setting up a min0 account. You know it is working when you can run the elm-archive command. These steps are specified in the following links:
#   https://docs.elm.stanford.edu/getting-started/
#   https://docs.elm.stanford.edu/user-guide/sherlock/
#
# At the heart of this function is the elm-archive tool on Sherlock, which is used to create tar files and upload them to the S3 bucket.
# Note that it does not work on specific files, only folders.
#
# You may have to edit this script to adjust the elm bucket or sherlock partition you are using.
# 
# The function takes as an input the folder to put this in. By default it will be called backup-QX-YYYY where QX is the quarter and YYYY is the year. It is not a precise date since the back up is not expected to be run frequently.
# 
# The second input (although usually unnecessary) is the path to the CSV. Defaults to 'backup_path_list.csv'
#
# The CSV has the following structure:
# | path | tar_children_separately | job_requirements |
# The first column ('path') specifies the paths to be backed up.
# The second column ('tar_children_separately') of each row is whether to backup that path or to backup the children of that path individually. There is no functionality to go a second level down.
# The third column ('job_requirements) specifies the job requirements if they are not default. For instance, when backing up the video data, it is recommended to add '-n 8 -t 2-0' to ask for 8 cores and 2 days of time.
# It then creates a tar file for each path, and uploads it to the specified S3 bucket with an equivalent path
#
# The third input is what row to start from in the csv. In case the code crashes/time runs out, you can specify a row to start from in order tor resume. It will redo from that row onwards. You can say 3.4 and it will resume at the 4th element of row 5 (assuming tar_children_separately == 1).

import pandas as pd
import os
import numpy as np
import sys
import glob
import subprocess

# Get the inputd
if len(sys.argv) > 1:
    backup_folder = sys.argv[1]
else:
    backup_folder = 'backup-Q%d-%d' % (np.ceil((pd.Timestamp.now().month + 1) / 3), pd.Timestamp.now().year)

# Specify the csv to load in
if len(sys.argv) > 2:
    csv_path = sys.argv[2]
else:
    csv_path = "backup_path_list.csv"

# Take the row number of the CSV to start on, if supplied
if len(sys.argv) > 3:
    row = sys.argv[3]
    # Check if it has a decimal, and if so split
    if '.' in row:
        initial_row = int(row.split('.')[0])
        path_counter = int(row.split('.')[1])
    else:
        initial_row = int(row)
        path_counter = 0
else:
    initial_row = 0
    path_counter = 0

# Load in the globals.sh file to get the ELM_BUCKET and PARTITION variables
# This is expected to be in the same directory as this script
globals_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'globals.sh')
if os.path.exists(globals_path):
    with open(globals_path, 'r') as f:
        for line in f:
            if line.startswith('ELM_BUCKET'):

                # Bucket name for elm
                ELM_BUCKET = line.split('=')[1].strip().strip('"')
            elif line.startswith('PARTITION'):

                # What is the partition on Sherlock to run this on?
                PARTITION = line.split('=')[1].strip().strip('"')
else:
    print("globals.sh file not found. Quitting.")
    sys.exit(1)

# Load the CSV
backup_paths_df = pd.read_csv(csv_path, keep_default_na=False, na_values=['nan', 'None'])

# Loop through the paths
row = initial_row
while row < len(backup_paths_df):
    # Pull out the info
    paths = backup_paths_df.iloc[row]['path']
    tar_children_separately = backup_paths_df.iloc[row]['tar_children_separately']
    job_requirements = backup_paths_df.iloc[row]['job_requirements']

    # Work with the job requirements variable to make it comaptible
    if job_requirements == 'nan' or job_requirements == 'None':
        job_requirements = ''
    else:
        # Check there are spaces on either side
        if not job_requirements.endswith(' '):
            job_requirements += ' '

        if not job_requirements.startswith(' '):
            job_requirements = ' ' + job_requirements


    # In a big print statement, print the info
    print('####################################\n####################################\n')
    print("Backing up path: %s, tar_children_separately: %s, job_requirements: %s\n" % (paths, tar_children_separately, job_requirements))
    print('####################################\n####################################\n')

    # Get all the paths separately if specified
    if tar_children_separately:
        paths = glob.glob(os.path.join(paths, '*'))
    else:
        # Make it a list
        paths = [paths]

    # Is this the row you provided and is path counter not zero? Else, set path_counter to zero
    if initial_row == row and path_counter != 0:
        print("Resuming from row %d, path %d/%d" % (row, path_counter + 1, len(paths)))
    else:
        path_counter = 0

    # Loop through the paths and back them up
    while path_counter < len(paths):
        # Get the current path and output file
        curr_path = paths[path_counter]
        output_file = '%s/%s%s' % (ELM_BUCKET, backup_folder, curr_path)

        # Check if the path exists
        if not os.path.exists(curr_path):
            print("Path %s does not exist. Skipping." % curr_path)
            path_counter += 1
            continue
        
        # Check if the path is a file
        if os.path.isfile(curr_path):
            print("Path %s is a file, not a directory. Skipping." % curr_path)
            path_counter += 1
            continue
        
        # Check if the path is an empty directory
        if len(os.listdir(curr_path)) == 0:
            print("Path %s is an empty directory. Skipping." % curr_path)
            path_counter += 1
            continue

        # Set up the elm command
        elm_archive_command = "elm_archive transfer --label %s-%d.%d -p %s%s%s %s" % (backup_folder, row, path_counter, PARTITION, job_requirements, curr_path, output_file)
        print("Running command:\n%s" % elm_archive_command)

        # Run the command
        # Note: This command is expected to be run on the Sherlock cluster, so it may not work on other systems
        # Continue if there is an error
        try:
            subprocess.run(elm_archive_command, shell=True, check=True)
            print("\nFinished backing up path: %s\n" % curr_path)
        except subprocess.CalledProcessError as e:
            print("Error running command: %s\n%s" % (elm_archive_command, e))
            print("Skipping path %s" % curr_path)

        path_counter += 1

    # Increment the row
    row += 1
    print("\nFinished row %d/%d" % (row, len(backup_paths_df)))
