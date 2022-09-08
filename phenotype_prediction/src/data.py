from genericpath import isfile
import gzip
import os.path
import re
import shutil
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
        Interleave two paired-end fastq files (based on interleave-fastq by Erik Garrison and Sébastien Boisvert).
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
        Note: manual interleaving is too slow.
    """
    print(f"Fetching paired-end fastq files...")
    gid_links = get_links_to_data_set_gids()

    for gid_link in gid_links:
        gid = gid_link.split("/")[-1]

        if os.path.isfile(f"sketches/sample_{gid}.json"):
            print(
                f"Found existing sketch; skipping sample {gid}.")
            continue

        print(
            f"Downloading {gid} paired-end fastq files...")
        pes = [gzip.GzipFile(fileobj=request.urlopen(
            f"{gid_link}_pe_{i}.fastq.gz")) for i in range(1, 3)]

        print(
            f"Interleaving and histosketching {gid} samples...")
        cmd = ["hulk", "sketch", "-o", f"sketches/{gid}"]
        process = subprocess.Popen(
            cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        process.stdin.write(
            interleave_fastq(pes[0], pes[1]))
        process.communicate()[0]

        process.wait()
        process.stdin.close()
        print(f"Completed {gid} sample histosketching.")


def generate_sketches_seqfu():
    """
        Generate sketches of available whole genome shotgun sequencing data.
        Note: uses seqfu for faster interleaving but very memory intensive to unzip files.
    """
    print(f"Fetching paired-end fastq files...")
    gid_links = get_links_to_data_set_gids()

    for gid_link in gid_links:
        gid = gid_link.split("/")[-1]

        if os.path.isfile(f"sketches/sample_{gid}.json"):
            print(
                f"Found existing sketch; skipping sample {gid}.")
            continue

        print(
            f"Downloading {gid} paired-end fastq files...")
        for i in range(1, 3):
            file_name = f"data/{gid}_pe_{i}.fastq"
            if os.path.isfile(file_name):
                continue

            if not os.path.isfile(f"{file_name}.gz"):
                request.urlretrieve(f"{gid_link}_pe_{i}.fastq.gz", f"{file_name}.gz")

            with gzip.open(f"{file_name}.gz", "rb") as compressed:
                with open(file_name, "wb") as uncompressed:
                    shutil.copyfileobj(compressed, uncompressed)
            
            os.remove(f"{file_name}.gz")

        print(
            f"Interleaving and histosketching {gid} samples...")
        cmd = f"seqfu ilv -1 data/{gid}_pe_1.fastq data/{gid}_pe_2.fastq | hulk sketch -o sketches/{gid}".split()
        process = subprocess.Popen(
            cmd, shell=True)
        process.wait()

        for i in range(1, 3):
            os.remove(f"data/{gid}_pe_{i}.fastq")
        print(f"Completed {gid} sample histosketching.")


def main():
    generate_sketches_seqfu()


if __name__ == "__main__":
    main()
