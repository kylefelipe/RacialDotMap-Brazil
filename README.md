# Brazil Racial Dotmap

Python and Processing code for creating (1) a dataset for every person in Brazil, coded by race, and (2) map tiles from the data. The end result can be seen at http://patadata.org/maparacial

# Methodology/how-to

## Step 0. Map+data joins
The preliminary ## Step (using no code) was to join racial data from the 2010 IBGE Census (available at tables Pessoa03UF.csv, where UF is a two-letter code used for each different state, at ftp://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_do_Universo/Agregados_por_Setores_Censitarios) to the corresponding state map (all of which are available at ftp://geoftp.ibge.gov.br/malhas_digitais/censo_2010/). This was done using free tool QGIS through table joining (a simples process described here http://www.qgistutorials.com/en/docs/performing_table_joins.html). A different shapefile, this time with racial data joined, was generated for each one of Brazil's 27 states (including the Federal District, DF).

## Step 1. Generating the database file
First, install osgeo, shapely and sqlite3 libraries for python.
Python script dotfile.py calls for each different state shapefile, in which it reads census sector by census sector, and for each person/point within it generates random geographic coordinates (within such sector) thus positioning the person/point in space. The output of this script is a huge (~12gb) database (.db) file containing one line per person, as well as their race, latitude, longitude and other info needed to make the map readable. This could take a few hours.

## Step 2. Converting to csv
Before you mess with it, you need that .db file converted to csv. This can be done using the bash file included called 'tocsv/simplecsv.sh'. Just be sure to adapt the pathnames accordingly. This will output a slightly smaller csv file with the same data in the previous .db file. This shouldn't take more than 30 minutes.

## Step 3. Sorting the file
Now you need to sort the entire csv file by quadkey, the info in the fourth column of the file. This is so Processing knows how to generate coherent map tiles later. Basically run the following bash command on it (included in 'sort/simplesort.sh'):

'sort -t, -k4 filename.csv > sorted.csv'

This could take a couple of hours.

## Step 4. Generating map tiles
Just run Processing file 'dotmap.pde' and map tiles will start being generated. You can track its progress with the accompanying 'index.html' file that previews the map as it is generated. Be sure to see what zoomlevels you want (4 to 15, 4 being the smallest zoom) by editing the 'zoomlevels.txt' file. #er zoomlevels may take dozens of hours to generate, so be warned. I used Processing 3, but older versions should work just fine.

# License

This code is based on the work of Brandon Martin-Anderson from the MIT Media Lab, which released its code (that generated maps with no color-coding) to the public domain, and on the work of the University of Virginia's Cooper Center which, though doesn't make it clear which license is used, does state its maps are "made available for free for research, teaching, scholarship, publications (including books and articles distributed in print or digitally), and other uses to promote the public good." We have chosen to license our code, with the small improvements and adaptations to this project, as CC-BY-SA.