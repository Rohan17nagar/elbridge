#!/bin/bash
set -e
set -o pipefail

# get data directory
echo "Enter a directory to store files (warning: expect to need several
gigabytes of room): "
read data_dir

if [ ! -d data_dir ]; then
  echo "Directory does not exist! Attempting to create it."
  mkdir -p data_dir
fi

cd "$data_dir"

echo "Downloading Census county data..."
wget "ftp2.census.gov/geo/tiger/TIGER2016/COUNTY/tl_2016_us_county.zip"
echo "Finished downloading county data."

mkdir wa-counties
unzip tl_2016_us_county.zip -d wa-counties

echo "Downloading Census block data (warning: takes a while)..."
wget "ftp2.census.gov/geo/tiger/TIGER2016/TABBLOCK/tl_2016_53_tabblock10.zip"
echo "Finished downoading block data."

mkdir wa-blocks
unzip tl_2016_53_tabblock10.zip -d wa-blocks

cd -

echo "Finished downloading Census data."

echo "To complete data download, request access to the Washington Voter
Registration Database at:"
echo "https://www.sos.wa.gov/elections/vrdb/extract-requests.aspx"

exit 0
