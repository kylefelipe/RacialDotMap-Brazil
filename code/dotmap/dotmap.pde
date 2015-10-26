BufferedReader reader;
double ll, bb, rr, tt;

float A = 1000.0;

GlobalMercator proj = new GlobalMercator();

class PersonPoint {
  double x, y;
  String quadnode;

  PersonPoint(String row) {
    String[] fields = split(row, ",");
    this.x = Double.parseDouble(fields[1])/A;
    this.y = Double.parseDouble(fields[2])/A;
    this.quadnode = fields[3];
  }

  void draw(PGraphics pg) {
    pg.point((float)this.x, (float)this.y);
  }
}

ArrayList people;

float pointWeight(int level) {
  if (level < 9 || level > 14) {
    return 0.01;
  }
  else {
    return 0.02;
  }
}

float transparent(int level) {
  if (level < 6) {
    return 153;
  }
  else if (level < 8) {
    return 179;
  }
  else if (level < 10) {
    return 204;
  }
  else if (level < 12) { 
    return 230;
  }
  else {
    return 255;
  }
}

void setup(){
  
  size(512, 512, JAVA2D);
  smooth(8);

  String[] zoomlevels = loadStrings("zoomlevel.txt");  // a text file with lines 4, 5, 6 ...etc. specifing zoomlevel

  for (int i = 0; i < zoomlevels.length; i++) {

    int level = int(zoomlevels[i]);

    println("Starting up...");
    reader = createReader("sorted.csv");  // the datafile (converted to .csv) sorted by quadkey
    try {
      String line;
      String quadkey = "";
      PGraphics pg = null; // processing image to be filled by dots
      PVector tms_tile = null;
      
      int rown = 0; // row counter
      
      line = reader.readLine();
      
      while (true) {
        line = reader.readLine();
        
        if (line == null || line.length() == 0) {
          println("file done");
          break;
        }
        
        rown += 1;
        
        if (rown % 100000 == 0) {
          println(rown);
        }
        String[] fields = split(line, ",");
        float px = float(fields[1])/A;
        float py = float(fields[2])/A;
        String newQuadkey = fields[3].substring(0,level);
        String race_type = fields[4].substring(0, 1);

        if (!newQuadkey.equals(quadkey)) { // if next quadkey is diff from previous -> new tile is initialized
          
          //finish up the last tile
          if (pg != null) {
            pg.endDraw();
            PVector gtile = proj.GoogleTile((int)tms_tile.x, (int)tms_tile.y, level);
            println("tiles_black/"+level+"/"+int(gtile.x)+"/"+int(gtile.y)+".png saved.");
            pg.save("tiles_black/"+level+"/"+int(gtile.x)+"/"+int(gtile.y)+".png");
            println("Last tile done.");
          }

          quadkey = newQuadkey;
          
          PVector google_tile = proj.QuadKeyToTileXY( newQuadkey );
          tms_tile = proj.GoogleTile( (int)google_tile.x, (int)google_tile.y, level );

          println("Level: "+ level +" "+ tms_tile.x +" "+ tms_tile.y );

          pg = createGraphics(512, 512, JAVA2D);
          pg.beginDraw();
          pg.smooth(8);

          PVector[] bounds = proj.TileBounds( (int)tms_tile.x, (int)tms_tile.y, level );

          float tile_ll = bounds[0].x/A;
          float tile_bb = bounds[0].y/A;
          float tile_rr = bounds[1].x/A;
          float tile_tt = bounds[1].y/A;

          double xscale = width/(tile_rr-tile_ll);
          double yscale = width/(tile_tt-tile_bb);
          float scale = min((float)xscale, (float)yscale);

          pg.scale(scale,-scale);
          
          pg.translate(-(float)tile_ll, -(float)tile_tt);

          pg.strokeWeight(pointWeight(level));
          
          pg.background(255);
        }
        
        /*if (pg != null) { // pure black map code, comment if generating coloured map
          pg.stroke(0, 0, 0, transparent(level));
          pg.point(px, py);
        }
        */
        
        if (race_type.equals("w") && pg != null) { // brancos
          pg.stroke(115, 178, 255, transparent(level)); // blue
          pg.point(px, py);
        }
          
        if (race_type.equals("b") && pg != null) { // pretos
          pg.stroke(255, 0, 0, transparent(level)); // red
          pg.point(px, py);
        }
        
        if (race_type.equals("a") && pg != null) { // asiaticos
          pg.stroke(255, 170, 0, transparent(level)); // yellow
          pg.point(px, py);
        }
          
        if (race_type.equals("h") && pg != null) { // pardos
          pg.stroke(159, 212, 0, transparent(level)); // green
          pg.point(px, py);
        }
          
        if (race_type.equals("o") && pg != null) { // indigenas
          pg.stroke(#996633, transparent(level)); // grey
          pg.point(px, py);
        }

      }

      if (pg != null) { // if tile has at least 1 dot
        pg.endDraw();
        PVector gtile = proj.GoogleTile((int)tms_tile.x, (int)tms_tile.y, level);
        pg.save("tiles_black/"+level+"/"+int(gtile.x)+"/"+int(gtile.y)+".png");
        println("One tile done.");
      }
    } 
    catch (IOException e) {
      e.printStackTrace();
    }
  }
}

void draw() {
}
