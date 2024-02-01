This project contains some example data files useful that may be used
as an initial setup for the [Orekit library](https://www.orekit.org/).

In order to use these files, simply download the
[latest archive](https://gitlab.orekit.org/orekit/orekit-data/-/archive/master/orekit-data-master.zip)
and unzip it anywhere you want. Rename the `orekit-data-master` folder to
`orekit-data`, note the path of this folder and add the following lines at
the start of your program:

```java
File orekitData = new File("/path/to/the/folder/orekit-data");
DataProvidersManager manager = DataContext.getDefault().getDataProvidersManager();
manager.addProvider(new DirectoryCrawler(orekitData));
```

This zip file contains:

* JPL DE 441 ephemerides from 1990 to 2149,
* IERS Earth orientation parameters from 1973 to June 2023
  with predicted data up to late 2023 (both IAU-1980 and IAU-2000),
* configuration data for ITRF versions used in regular IERS files,
* leap seconds history from 1972 to end 2023,
* Marshall Solar Activity Future Estimation from 1999 to June 2023,
* CSSI Space Weather Data with observed data from 1957 to June 2023
  with predicted data up to 22 years in the future
* the Eigen 6S gravity field
* the FES 2004 ocean tides model.

The provided archive is just a convenience, it is intended as a starting
point for Orekit setup. Users are responsible to update the files in
the unzipped folder to suit their needs as new data is published by IERS,
NASA... This is why we suggest to rename `orekit-data-master`
into `orekit-data` to show that the live data folder is decorrelated
from the initial master folder.

There is *NO* guarantee that this convenience archive will be updated
or even provided in the future.
