#!/bin/sh

# Copyright 2002-2023 CS GROUP
# Licensed to CS GROUP (CS) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# CS licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# this script updates the following files in the orekit-data directory
#  UTC-TAI.history
#  Earth-Orientation-Parameters/IAU-1980/finals.all
#  Earth-Orientation-Parameters/IAU-2000/finals2000A.all
#  MSAFE/mmm####f10_prd.txt (where mmm is a month abbreviation and #### a year)
#  CSSI-Space-Weather-Data/SpaceWeather-All-v1.2.txt

# base URLS
usno_ser7_url=https://maia.usno.navy.mil/ser7
iers_rapid_url=https://datacenter.iers.org/data
msafe_url=https://www.nasa.gov/sites/default/files/atoms/files
cssi_url=ftp://ftp.agi.com/pub/DynamicEarthData

# fetch a file from an URL
fetch_URL()
{ echo "fetching file $1" 1>&2
  local name=$(echo "$1" | sed 's,.*/,,')
  if [ -f "$name" ] ; then
    mv "$name" "$name.old"
  fi

  if curl "$1" | tr -d '\015' > "$name" && test -s "$name" ; then
    if [ -f "$name.old" ] ; then
        # remove old file
        rm "$name.old"
    fi
    echo "$1 fetched" 1>&2
    return 0
  else
    if [ -f "$name.old" ] ; then
        # recover old file
        mv "$name.old" "$name"
    fi
    echo "$1 not fetched!" 1>&2
    return 1
  fi

}

# find the MSAFE base name (month/year) following an existing base name
next_MSAFE()
{
    local pattern='\([a-z][a-z][a-z]\)\([0-9][0-9][0-9][0-9]\)f10'
    local month=$(echo "$1" | sed "s,$pattern,\1,")
    local year=$(echo  "$1" | sed "s,$pattern,\2,")
    case $month in
      'jan') month='feb' ;;
      'feb') month='mar' ;;
      'mar') month='apr' ;;
      'apr') month='may' ;;
      'may') month='jun' ;;
      'jun') month='jul' ;;
      'jul') month='aug' ;;
      'aug') month='sep' ;;
      'sep') month='oct' ;;
      'oct') month='nov' ;;
      'nov') month='dec' ;;
      'dec') month='jan' ; year=$(($year + 1));;
      *) echo "wrong pattern $1" 1>&2 ; exit 1;;
    esac
    echo ${month}${year}f10
}

# find the first MSAFE file that is missing in current directory
first_missing_MSAFE()
{
  local msafe=mar1999f10
  while test -f "$msafe".txt || test -f "$msafe"_prd.txt ; do
      msafe=$(next_MSAFE $msafe)
  done
  echo $msafe
}

# update (overwriting) leap seconds file
fetch_URL $usno_ser7_url/tai-utc.dat

# update (overwriting) Earth Orientation Parameters
(cd Earth-Orientation-Parameters/IAU-2000 && fetch_URL $iers_rapid_url/9/finals2000A.all)
(cd Earth-Orientation-Parameters/IAU-1980 && fetch_URL $iers_rapid_url/7/finals.all)

# update (adding files) Marshall Solar Activity Future Estimation
msafe_base=$(cd MSAFE ; first_missing_MSAFE)
while [ ! -z "$msafe_base" ] ; do
    msafe_file=${msafe_base}_prd.txt
    if $(cd MSAFE ; fetch_URL ${msafe_url}/${msafe_file}) ; then
      case $(head -1 MSAFE/${msafe_file} | tr ' ' '_') in
          __TABLE_3_*) echo 1>&2 "${msafe_file} retrieved"
                       msafe_base=$(next_MSAFE $msafe_base)
                       ;;
          *)           echo 1>&2 "${msafe_file} not published yet"
                       rm MSAFE/${msafe_file}
                       msafe_base=""
                       ;;
      esac
    else
      msafe_base=""
    fi
done

# update (overwriting) CSSI space weather data
(cd CSSI-Space-Weather-Data && fetch_URL $cssi_url/SpaceWeather-All-v1.2.txt)
