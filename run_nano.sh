#! /bin/bash

LIMIT=0
CHUNK=0
MAX=0

while getopts "n:a:w:c:m:" arg; do
    case $arg in
	n)
	    LIMIT=$OPTARG
	    ;;
	a)
	    AFNAME=$OPTARG
	    ;;
	w)
	    WORKERS=$OPTARG
	    ;;
	c)
	    CHUNK=$OPTARG
	    ;;
	m)
	    MAX=$OPTARG
	    ;;
    esac
done

WDIR="nanocc_run_${NFILES}_${AFNAME}_${LIMIT}_${CHUNK}_${MAX}_${WORKERS}"

if [ ${LIMIT} == 0 ] ; then
    LIMIT=""
else
    LIMIT="--limit ${LIMIT}"
fi

if [ ${CHUNK} == 0 ] ; then
    CHUNK=""
else
    CHUNK="--chunk ${CHUNK}"
fi

if [ ${MAX} == 0 ] ; then
    MAX=""
else
    MAX="--max ${MAX}"
fi

if [ -e $WDIR ] ; then
    echo "Directory already exists. Exiting..."
    exit 1
fi
mkdir $WDIR
cd $WDIR
ln -s ../runner.py .
ln -s ../metadata .
sudo sysctl vm.drop_caches=3
#ulimit -n 4096
prmon -i 5 -- python runner.py --id test --json metadata/v2x17_${AFNAME}.json --year 2017 ${LIMIT} ${CHUNK} ${MAX} --executor futures -j $WORKERS > nanocc.out 2> nanocc.err
RC=$?
echo "Return code: ${RC}" >> nanocc.out
