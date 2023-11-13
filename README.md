## Acknowledgements
This code has been written by Andrzej Novak and the customisations in this repository are only meant to easily run it as an I/O benchmark.

## Prerequisites
Install PrMon as explained here:

https://github.com/HSF/prmon

## Installation
Create and activate a dedicated conda environment with the needed dependencies:

```bash
conda create --name cms_coffea_analysis python=3.9.16
conda activate cms_coffea_analysis
conda install -c conda-forge xrootd
pip install -r requirements.txt
# get analysis code and install as package
git clone git@github.com:andrzejnovak/boostedhiggs.git
cd boostedhiggs
pip install -e . 
cd ..
```

Create a VOMS proxy to get access to the data:

```bash
# voms-proxy-init -voms cms:/cms/Role=production -valid 192:00
```
## Test scale out
Assuming you have read access to the relevant EOS dataset, you can test that everyting runs fine by doing
```bash
python runner.py --id test17 --json metadata/v2x17_cern-xrootd.json --year 2017 --limit 1 --chunk 5000 --max 2 --executor futures -j 5 
```
## Use at a different site
The file `metadata/v2x17_cern-xrootd.json` contains the list of files to be read. If you want to use the script at another site, you need to copy them to the desired storage element and location and create a new JSON file for the new file list.

## Use for benchmarking
The script `run_nano.sh` can be used to execute the workload while recording some relevant performance metrics, collected by PrMon.
The simplest way to do that is by doing

```
./run_nano.sh -a cern-xrootd -w <workers>
```
where `<workers>` is the desired number of workers.
The script should be studied and modified if needed; for example the original version clears the OS page cache before the execution, as to avoid data to be read from memory rather than from disk.

## Collecting statistics
The script `metrics.sh` parses the output of the desired run and prints some metrics in a human readable way. The script `metrics_csv.sh` does the same thing but needs at least two runs with the same parameters to estimate the errors on the metrics.

For help write to <Andrea.Sciaba@cern.ch>.


