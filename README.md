## Acknowledgements
This code has been written by Andrzej Novak and the customisations in this repository are only meant to easily run it as an I/O benchmark.

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
where `<cores>` is the desired number of workers.

