# Gerrymandering

### How to run this

1. Pull this repo:

```
git clone git@github.com:rohan/gerrymander.git
cd gerrymander/
```

2. Next, create a data directory (you'll need a lot of room).

3. Using the [Census TIGER database](https://census.gov/geo/maps-data/data/tiger-line.html), download the following files:
- [2016 Washington county map](ftp://ftp2.census.gov/geo/tiger/TIGER2016/COUNTY/tl_2016_us_county.zip)
- [2016 Washington block map](ftp://ftp2.census.gov/geo/tiger/TIGER2016/TABBLOCK/tl_2016_53_tabblock10.zip)
- The most recent voter registration database for Washington. You'll need to request permission on the [Washington Secretary of State website](https://www.sos.wa.gov/elections/vrdb/extract-requests.aspx).

4. Create folders in your data directory for each file, e.g., `your_data_directory/wa-counties`.

5. Unzip each file into your data directory, as follows: `unzip filename.zip -d your_data_directory/folder_for_file`.

6. Create a config file by copying the existing file: ~
