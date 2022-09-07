import gzip
import re
import sys
import subprocess
from urllib import request
from bs4 import BeautifulSoup, SoupStrainer

SUCCESS = 200
PAIRED_END_SUFFIX = "_pe_1.fastq.gz"
DATASET_LINK = "https://diabimmune.broadinstitute.org/diabimmune/data/17/"


def get_links_to_data_set_gids() -> list[str]:
    """
        Retrieve GID links of available whole genome shotgun sequencing data.
    """
    response = request.urlopen(DATASET_LINK)
    if response.status != SUCCESS:
        print(
            f"Could not retrieve data sets from {DATASET_LINK}.", file=sys.stderr)
        return
    page = response.read()

    # Retrieve shotgun GID links
    pattern = re.compile(r"\_pe\_1\.fastq\.gz$")

    return [link["href"].removesuffix(PAIRED_END_SUFFIX) for link in BeautifulSoup(page, "html.parser", parse_only=SoupStrainer("a"))
            if link.has_attr("href") and pattern.search(link["href"])]


def interleave_fastq(f1, f2) -> bytearray:
    """
        Interleaves two paired-end fastq files (based on interleave-fastq by Erik Garrison and Sébastien Boisvert).
    """
    buff = bytearray()

    while True:
        line = f1.readline()
        if line.strip() == "":
            break
        buff.extend(line.strip())

        for _ in range(3):
            buff.extend(f1.readline().strip())
        for _ in range(4):
            buff.extend(f2.readline().strip())

    f1.close()
    f2.close()

    return buff


def generate_sketches() -> None:
    """
        Generate sketches of available whole genome shotgun sequencing data.
    """
    gid_links = get_links_to_data_set_gids()

    for gid_link in gid_links:
        gid = gid_link.split("/")[-1]
        pes = [gzip.GzipFile(fileobj=request.urlopen(
            f"{gid_link}_pe_{i}.fastq.gz").read()) for i in range(1, 3)]

        # Histosketch the interleaved fastq file
        cmd = ["hulk", "sketch", "-o", f"sketches/{gid}"]
        process = subprocess.Popen(
            cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        process.stdin.write(
            interleave_fastq(pes[0], pes[1]))
        process.communicate()[0]
        process.wait()
        process.stdin.close()
