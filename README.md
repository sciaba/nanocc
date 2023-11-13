## Installation
Create and activate a dedicated conda environment with the needed dependencies:

```bash
conda create --name tmp_andrzej_analysis python=3.9.16
conda activate tmp_andrzej_analysis
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


### Test run
Use `--executor iterative` for single process to debug, `--executor futures` for local multiprocessing.

```bash
python runner.py --id test17 --json metadata/v2x17.json --year 2017 --limit 1 --chunk 5000 --max 2 --executor futures -j 5 
```

### Test scale out
Scale-out will be dependent on the cluster setup. If the cluster is sufficiently permissive the below might run right away, otherwise some editing of `runner.py` and `HighThroughputExecutor` when using `--executor parsl` will be necessary. Analogously for `--executor dask`

```bash
python runner.py --id test17 --json metadata/v2x17.json --year 2017 --limit 1 --chunk 5000 --max 2 --executor parsl
```

### Full scale
Removing test limiters...
```bash
python runner.py --id test17 --json metadata/v2x17.json --year 2017 --executor parsl
```
