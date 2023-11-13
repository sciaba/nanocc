#!/bin/bash

prefix=$1
logdir=$1_$2
workers=$(echo $2 | cut -d. -f1) 
if [ ! -d "$logdir" ] ; then
    echo "Directory does not exist. Exiting..."
    exit 1
fi

rchar=$(grep -A 18 Max ${logdir}/prmon.json | awk '/rchar/ {sub(/,/, "", $2); print ($2 / 1024 ** 3)}')
wchar=$(grep -A 18 Max ${logdir}/prmon.json | awk '/wchar/ {sub(/,/, "", $2); print ($2 / 1024 ** 3)}')
rmbytes=$(grep -A 18 Max ${logdir}/prmon.json | awk '/read_bytes/ {sub(/,/, "", $2); print ($2 / 1024 ** 2)}')
rgbytes=$(grep -A 18 Max ${logdir}/prmon.json | awk '/read_bytes/ {sub(/,/, "", $2); print ($2 / 1024 ** 3)}')
wgbytes=$(grep -A 18 Max ${logdir}/prmon.json | awk '/write_bytes/ {sub(/,/, "", $2); print ($2 / 1024 ** 3)}')
utime=$(grep -A 18 Max ${logdir}/prmon.json | awk '/utime/ {sub(/,/, "", $2); print $2}')
stime=$(grep -A 18 Max ${logdir}/prmon.json | awk '/stime/ {sub(/,/, "", $2); print $2}')
wtime=$(grep -A 18 Max ${logdir}/prmon.json | awk '/wtime/ {sub(/,/, "", $2); print $2}')
rxmbytes=$(grep -A 18 Max ${logdir}/prmon.json | awk '/rx_bytes/ {sub(/,/, "", $2); print ($2 / 1024 ** 2)}')
rxgbytes=$(grep -A 18 Max ${logdir}/prmon.json | awk '/rx_bytes/ {sub(/,/, "", $2); print ($2 / 1024 ** 3)}')
totexetime=$(sed -n -E 's/.*processtime.* ([0-9.]*).*/\1/p' ${logdir}/nanocc.out)
d=$(sed -n -E 's/.*bytesread.* ([0-9.]*).*/\1/p' ${logdir}/nanocc.out)
entries=$(sed -n -E 's/.*entries.* ([0-9.]*).*/\1/p' ${logdir}/nanocc.out)
exetime=$(awk "BEGIN {print($totexetime / $workers)}")
rrate=$(awk "BEGIN {print($rmbytes / $wtime)}")
rxrate=$(awk "BEGIN {print($rxmbytes / $wtime)}")
cpueff=$(awk "BEGIN {print(100*($utime+$stime)/$wtime/$workers)}")
data=$(awk "BEGIN {print($d / 1024 ** 3)}")
data2=$(awk "BEGIN {print($d / 1024 ** 2)}")
#throughput=$(grep processtime ${logdir}/ttbar.out | awk '{print $7}')
datarate=$(awk "BEGIN {print($data2 / $exetime)}")
echo "Total read data from OS: $rchar GiB"
echo "Total written data to OS: $wchar GiB"
echo "Total read data from storage: $rgbytes GiB"
echo "Total written data to storage: $wgbytes GiB"
echo "Total network read data: $rxgbytes GiB"
echo "Wallclock time: $wtime sec"
echo "Read rate from storage: $rrate MiB/sec"
echo "Network read rate: $rxrate MiB/sec"
echo "CPU efficiency: $cpueff (%)"
echo "Execution time: $exetime sec"
#echo "Throughput per worker: $throughput kHz"
echo "Amount of data: $data GiB"
echo "Data rate: $datarate MiB/sec"
echo "Entries: $entries"
