# Run the backup of data to Elm
Tools to run a back up of a list of specified files to Elm as tar files, using the elm-archive tool on Sherlock.  
This is expected to be run infrequently as it is slow and elm is slow  
To set this up, a variety of steps were needed like authorizing globus and setting up a min0 account. You know it is working when you can run the elm-archive command. These steps are specified in the following links:  
> [getting-started](https://docs.elm.stanford.edu/getting-started/)  
> [elm-archive](https://docs.elm.stanford.edu/user-guide/sherlock/)  

Once this is set up you will be ready to use these tools. Specifically, to use this you will need to modify the following:  

> `globals.sh`: This file specifies the global parameters that will be used in the scripts. You will need to specify the conda environment, the Elm bucket name this will go to, and the partition on Sherlock that the jobs will run on. The conda environment must be able to import pandas, numpy, glob, os, sys, and subprocess.
> `backup_path_list.csv`: This file specifies the paths to be backed up, whether to backup the children of that path separately, and the job requirements if they are not default. The CSV has the following structure:
>> | `path` | `tar_children_separately` | `job_requirements` |  
>> The first column (`path`) specifies the paths to be backed up.  
>> The second column (`tar_children_separately`) of each row is whether to backup that path or to backup the children of that path individually. There is no functionality to go a second level down.  
>> The third column (`job_requirements`) specifies the job requirements if they are not default. For instance, when backing up the video data, it is recommended to add '-n 8 -t 2-0' to ask for 8 cores and 2 days of time.  
>> Note that it does not work on specific files, only folders.  

With these files set up, you can then run the `supervisor_backup_Elm.sh` script to start the backup process. This script will run the `backup_Elm.py` script, which is responsible for reading the paths from the CSV file and creating tar files of the specified directories. You can supply inputs to the script as follows:
> `backup_folder`: The folder where the tar files will be stored.  
> `csv_path`: The path to the `backup_path_list.csv` file.  
> `row`: The specific row in the CSV file that you want to process. This is 0-indexed, meaning the first row is row 0. If you have set tar_children_separately to 1 for a row, then you can jump in at a specific element in that folder by using a decimal value. For example, if you want to start at the 3rd child of the 3rd element in the CSV file, you would use `2.2`   