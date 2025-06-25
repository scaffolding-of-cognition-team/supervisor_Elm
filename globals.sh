#!/bin/bash
# Specify global parameters that will be used in the scripts

# What is the name of the conda environment that will be used for the python. It must be able to import pandas, numpy, glob, os, sys, and subprocess
CONDA_ENV=infant_fMRI

# What is the name of the bucket where the ELM data is stored
ELM_BUCKET=cte

# What is the name of the partition on Sherlock that the jobs will run on
PARTITION=cte