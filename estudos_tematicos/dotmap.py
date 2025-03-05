import csv
import os
from PIL import Image, ImageDraw
from math import pow
import geopandas as gpd
import pandas as pd

# Constantes
A = 1000.0

zoom_levels = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]


# Classe para manipular projeções (GlobalMercator em Java)
class GlobalMercator:
    def QuadKeyToTileXY(self, quadkey):
        tile_x, tile_y = 0, 0
        level = len(quadkey)
        for i in range(level):
            bit = level - i - 1
            mask = 1 << bit
            if quadkey[i] == "1":
                tile_x |= mask
            elif quadkey[i] == "2":
                tile_y |= mask
            elif quadkey[i] == "3":
                tile_x |= mask
                tile_y |= mask
        return (tile_x, tile_y)

    def GoogleTile(self, tile_x, tile_y, zoom):
        return tile_x, (int(pow(2, zoom)) - 1 - tile_y)

    def TileBounds(self, tile_x, tile_y, zoom):
        n = 256 * pow(2, zoom)
        tile_ll = tile_x * n / pow(2, zoom)
        tile_bb = tile_y * n / pow(2, zoom)
        tile_rr = (tile_x + 1) * n / pow(2, zoom)
        tile_tt = (tile_y + 1) * n / pow(2, zoom)
        return [(tile_ll, tile_bb), (tile_rr, tile_tt)]


# Funções auxiliares
def point_weight(level):
    if level < 9 or level > 14:
        return 0.01
    else:
        return 0.02


def transparent(level):
    if level < 6:
        return 153
    elif level < 8:
        return 179
    elif level < 10:
        return 204
    elif level < 12:
        return 230
    else:
        return 255


# Classe para processar dados
class PersonPoint:
    def __init__(self, row):
        self.x = float(row["geometry"]) / A
        self.y = float(row["geometry"]) / A
        self.quadnode = row[3]


# Processamento principal
def main():
    proj = GlobalMercator()
    # zoom_levels = [int(line.strip()) for line in open("zoomlevel.txt")]

    for level in zoom_levels:
        print("Starting up...")
        gdf = gpd.read_file(
            "/home/kylefelipe/mapa_repo/estudos_tematicos/acre_pessoas_simples_quadkey.gpkg",
            # rows=10,
        )
        # with open("sorted.csv", newline="") as csvfile: # remover
        #     reader = csv.reader(csvfile) # remover
        #     next(reader)  # Ignora o cabeçalho, se houver remover

        quadkey = ""
        image = None
        tms_tile = None

        for _idx, row in gdf.iterrows():
            px, py = row["geometry"].x / A, row["geometry"].y / A
            new_quadkey = row["quadkey"][:level]
            race_type = row["raca"]

            if new_quadkey != quadkey:  # Novo tile
                if image:
                    # Salva a imagem anterior
                    gtile = proj.GoogleTile(int(tms_tile[0]), int(tms_tile[1]), level)
                    path = f"tiles/{level}/{int(gtile[0])}/{int(gtile[1])}.png"
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    image.save(path)
                    print(f"Tile salvo em: {path}")

                quadkey = new_quadkey
                google_tile = proj.QuadKeyToTileXY(new_quadkey)
                tms_tile = proj.GoogleTile(google_tile[0], google_tile[1], level)
                print(f"Novo tile: Nível {level}, {tms_tile}")

                image = Image.new("RGBA", (512, 512), (255, 255, 255, 255))
                draw = ImageDraw.Draw(image)

            # Define a cor do ponto ['parda' 'indigena' 'branca' 'amarela' 'preta']

            if race_type == "branca":  # Brancos
                color = (115, 178, 255, transparent(level))
            elif race_type == "preta":  # Pretos
                color = (255, 0, 0, transparent(level))
            elif race_type == "amarela":  # Asiáticos
                color = (255, 170, 0, transparent(level))
            elif race_type == "parda":  # Pardos
                color = (159, 212, 0, transparent(level))
            elif race_type == "indigena":  # Indígenas
                color = (153, 102, 51, transparent(level))
            else:
                continue

            # Desenha o ponto na imagem
            if image:
                draw.point((px * 512, py * 512), fill=color)

        # Salva o último tile
        if image:
            gtile = proj.GoogleTile(int(tms_tile[0]), int(tms_tile[1]), level)
            path = f"tiles/{level}/{int(gtile[0])}/{int(gtile[1])}.png"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            image.save(path)
            print(f"Último tile salvo em: {path}")


if __name__ == "__main__":
    main()
