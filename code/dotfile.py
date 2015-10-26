# coding=utf-8

import sys
from osgeo import ogr, gdal
from shapely.wkb import loads
from shapely.geometry import *
from random import uniform
import sqlite3

# Import the module that converts spatial data between formats

sys.path.append("filepath")
from globalmaptiles import GlobalMercator

# Main function that reads the shapefile, obtains the population counts,
# creates a point object for each person by race, and exports to a SQL database.

def main(input_filename, output_filename):
    
    # Create a GlobalMercator object for later conversions
    
    merc = GlobalMercator()

    # Open the shapefile
    
    ds = ogr.Open(input_filename)
    
    if ds is None:
        print "Open failed.\n"
        sys.exit( 1 )

    # Obtain the first (and only) layer in the shapefile
    
    lyr = ds.GetLayerByIndex(0)

    lyr.ResetReading()

    # Obtain the field definitions in the shapefile layer

    feat_defn = lyr.GetLayerDefn()
    field_defns = [feat_defn.GetFieldDefn(i) for i in range(feat_defn.GetFieldCount())]

    # Obtain the index of the field for the count for whites, blacks, Asians, 
    # Others, and Hispanics.
    
    for i, defn in enumerate(field_defns):
        if defn.GetName() == "V001": # pop total
            pop_field = i
            
        if defn.GetName() == "V002": # brancos
            white_field = i
            
        if defn.GetName() == "V003": # negros
            black_field = i
            
        if defn.GetName() == "V004": # asiaticos
            asian_field = i
            
        if defn.GetName() == "V005": # indios
            hispanic_field = i
            
        if defn.GetName() == "V006": # outros
            other_field = i
            
        if defn.GetName() == "CD_GEOCODI": # codigo da UF são os dois primeiros caracteres de CD_GEOCODI
            statefips_field = i

    # Set-up the output file
    
    conn = sqlite3.connect( output_filename )
    cc = conn.cursor()
    cc.execute( "create table if not exists people_by_race (statefips text, x text, y text, quadkey text, race_type text)" )

    # Obtain the number of features (Census Blocks) in the layer
    
    n_features = len(lyr)

    # Iterate through every feature (Census Block Ploygon) in the layer,
    # obtain the population counts, and create a point for each person within
    # that feature.

    for j, feat in enumerate( lyr ):
        
        # Print a progress read-out for every 1000 features and export to hard disk
        
        if j % 1000 == 0:
            conn.commit()
            print "%s/%s (%0.2f%%)"%(j+1,n_features,100*((j+1)/float(n_features)))
            
        # Obtain total population, racial counts, and state fips code of the individual census block
        try:
            pop = int(feat.GetField(pop_field))
        except: pop = 0
        try:
            white = int(feat.GetField(white_field))
        except: white = 0
        try:
            black = int(feat.GetField(black_field))
        except: black = 0
        try:
            asian = int(feat.GetField(asian_field))
        except: asian = 0
        try:
            hispanic = int(feat.GetField(hispanic_field))
        except: hispanic = 0
        try:
            other = int(feat.GetField(other_field))
        except: other = 0

        statefips = feat.GetField(statefips_field)[0:2]

        # Obtain the OGR polygon object from the feature

        geom = feat.GetGeometryRef()
        
        if geom is None:
            continue
        
        # Convert the OGR Polygon into a Shapely Polygon
        
        poly = loads(geom.ExportToWkb())
        
        if poly is None:
            continue        
            
        # Obtain the "boundary box" of extreme points of the polygon

        bbox = poly.bounds
        
        if not bbox:
            continue
     
        leftmost,bottommost,rightmost,topmost = bbox
        
        # Generate a point object within the census block for every person by race
        for race in ["white", "black", "asian", "hispanic", "other"]:
            for i in range(eval(race)):
                # Choose a random longitude and latitude within the boundary box
                # and within the orginial ploygon of the census block
                    
                while True:
                        
                    samplepoint = Point(uniform(leftmost, rightmost),uniform(bottommost, topmost))
                        
                    if samplepoint is None:
                        break
                    
                    if poly.contains(samplepoint):
                        break
        
                # Convert the longitude and latitude coordinates to meters and
                # a tile reference
        
                x, y = merc.LatLonToMeters(samplepoint.y,samplepoint.x)
                tx,ty = merc.MetersToTile(x, y, 21)
                    
                # Create a unique quadkey for each point object
                    
                quadkey = merc.QuadTree(tx, ty, 21)
                    
                # Create categorical variable for the race category
                       
                race_type = race[0]
        
                # Export data to the database file
        
                cc.execute( "insert into people_by_race values (?,?,?,?,?)", (statefips, x, y, quadkey,race_type) )

    conn.commit()

# Execution code...

if __name__=='__main__':
    
    for state in [str(x) for x in range(1,28)]: #pra todos os estados da republica q
        print "state:%s"%state
        main("../maps/merged/"+ state +".shp", "../data/gen/people_race_allstates.db")
    """

    for state in ['01','02','04','05','06','08','09','10','11','12','13','15',
        '16','17','18','19','20','21','22','23','24','25','26','27','28','29','30',
        '31','32','33','34','35','36','37','38','39','40','41','42','44','45','46',
        '47','48','49','50','51','53','54','55','56']:
    """    
        #print "state:%s"%state
        
        #main( ".../maps/statefile_"+state+".shp", ".../Map Data/people_by_race5.db")
    #main("../maps/merged/01.shp", "../data/gen/people_by_race5.db")
