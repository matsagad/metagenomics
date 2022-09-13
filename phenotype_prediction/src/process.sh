#!/usr/bin/bash
MIN_SEQ_LEN=29

FASTQ_PE_1_GZ=$1
FASTQ_PE_2_GZ=$2
FASTQ_PE_NAME=$(basename $FASTQ_PE_1_GZ)
GID="${FASTQ_PE_NAME%_pe_?.fastq.gz}"

PATH_TO_DATA=$(dirname $FASTQ_PE_1_GZ)
PATH_TO_CLEAN_DATA="$PATH_TO_DATA/clean"
PATH_TO_SKETCHES="$(dirname $PATH_TO_DATA)/sketches"

# Remove sequences containing N nucleotides and those shorter than required.
function clean_fastq {
  awk -v min_seq_len=$MIN_SEQ_LEN '
    BEGIN {FS = "\t" ; OFS = "\n"}
    {header = $0 ; getline seq ; getline qheader ; getline qseq ;
      if (length(seq) >= min_seq_len && seq !~ /^[ATCG]*$/)
        {print header, seq, qheader, qseq}
    }'
}

function unzip_gz {
  FASTQ_GZ_NAME=$1
  gunzip $1
  echo ${FASTQ_GZ_NAME%.gz}
}

FASTQ_PE_1=$(process_gz $FASTQ_PE_1_GZ)
FASTQ_PE_2=$(process_gz $FASTQ_PE_2_GZ)

FASTQ_CLEAN_INTERLEAVED="$PATH_TO_CLEAN_DATA/$GID.fastq"

seqfu ilv -1 $FASTQ_PE_1 -2 $FASTQ_PE_2 | clean_fastq >$FASTQ_CLEAN_INTERLEAVED
rm $FASTQ_PE_1 $FASTQ_PE_2

hulk <$FASTQ_CLEAN_INTERLEAVED sketch -o "$PATH_TO_SKETCHES/sample_$GID"
rm $FASTQ_CLEAN_INTERLEAVED
