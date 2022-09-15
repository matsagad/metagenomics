#!/usr/bin/bash
MIN_SEQ_LEN=29
NUM_PROCESSORS=8
SKETCH_SIZE=512

FASTQ_PE_1_GZ=$1
FASTQ_PE_2_GZ=$2
FASTQ_PE_NAME=$(basename $FASTQ_PE_1_GZ)
GID="${FASTQ_PE_NAME%_pe_?.fastq.gz}"

PATH_TO_DATA=$(dirname $FASTQ_PE_1_GZ)
PATH_TO_SKETCHES="$(dirname $PATH_TO_DATA)/sketches"

# Remove sequences shorter than required.
function clean_fastq {
  awk -v min_seq_len=$MIN_SEQ_LEN '
    BEGIN {FS = "\t" ; OFS = "\n"}
    {header = $0 ; getline seq ; getline qheader ; getline qseq ;
      if (length(seq) >= min_seq_len)
        {print header, seq, qheader, qseq}
    }'
}

function unzip_gz {
  FASTQ_GZ_NAME=$1
  gunzip $1
  echo ${FASTQ_GZ_NAME%.gz}
}

FASTQ_PE_1=$(unzip_gz $FASTQ_PE_1_GZ)
FASTQ_PE_2=$(unzip_gz $FASTQ_PE_2_GZ)

FASTQ_INTERLEAVED="$PATH_TO_DATA/$GID.fastq"

seqfu ilv -1 $FASTQ_PE_1 -2 $FASTQ_PE_2 | clean_fastq >$FASTQ_INTERLEAVED &&
  rm $FASTQ_PE_1 $FASTQ_PE_2

cat $FASTQ_INTERLEAVED | hulk sketch -p=$NUM_PROCESSORS -s=$SKETCH_SIZE -o "$PATH_TO_SKETCHES/sample_$GID" &&
  rm $FASTQ_INTERLEAVED
