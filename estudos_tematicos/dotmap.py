import csv
import os
from PIL import Image, ImageDraw
from math import pow
import geopandas as gpd
import pandas as pd

import argparse

# Constantes
A = 1000.0

zoom_levels = [*range(4, 20, 2)]  # Níveis de zoom de 6 a 18


race_colors = {
    "Brancos": "#ff7f9b",
    "Pretos": "#071119",
    "Amarelas": "#dda625",
    "Pardas": "#cfc2ad",
    "Indígenas": "#1775e1",
}


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


# Função que converte cores em hexadecimal para RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


# Processamento principal
def create_tile(gpkg_path):
    proj = GlobalMercator()
    # zoom_levels = [int(line.strip()) for line in open("zoomlevel.txt")]
    # verifica se o arquivo existe
    print("Starting up...")
    if not os.path.exists(gpkg_path):
        print(f"Arquivo {gpkg_path} não encontrado.")
        return
    for level in zoom_levels:
        print(f"Processando o nível {level}...")
        gdf = gpd.read_file(gpkg_path)

        quadkey = ""
        image = None
        tms_tile = None
        # ultimo id do gdf
        last_id = gdf.index[-1]

        for _idx, row in gdf.iterrows():
            px, py = row["geometry"].x / A, row["geometry"].y / A
            new_quadkey = row["quadkey"][:level]
            race_type = row["raca_cor"]
            eol = ""
            if _idx % 1000 == 0 and quadkey != "":
                eol = "\n" if _idx == last_id else ""
                # imprime o texto "Linhas processadas: {linhas}" substindo a linha atual no console pelo novo texto
                print(f"\rLinhas processadas: {_idx}", end=eol)

            if new_quadkey != quadkey:  # Novo tile
                if image:
                    # Salva a imagem anterior
                    gtile = proj.GoogleTile(int(tms_tile[0]), int(tms_tile[1]), level)
                    path = f"tiles/{level}/{int(gtile[0])}/{int(gtile[1])}.png"
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    image.save(path)
                    if eol == "":
                        print()
                    print(f"Tile salvo em: {path}")

                quadkey = new_quadkey
                google_tile = proj.QuadKeyToTileXY(new_quadkey)
                tms_tile = proj.GoogleTile(google_tile[0], google_tile[1], level)
                if eol == "":
                    print()
                print(f"Salvando tile: Nível {level}, {tms_tile}")

                image = Image.new("RGBA", (512, 512), (255, 255, 255, 255))
                draw = ImageDraw.Draw(image)

            # Define a cor do ponto ['parda' 'indigena' 'branca' 'amarela' 'preta']
            if race_type not in race_colors.keys():
                continue

            color = (*hex_to_rgb(race_colors[race_type]), transparent(level))
            # if race_type == "Brancos":  # Brancos
            #     color = (115, 178, 255, transparent(level))
            # elif race_type == "Pretos":  # Pretos
            #     color = (255, 0, 0, transparent(level))
            # elif race_type == "Amarelas":  # Asiáticos
            #     color = (255, 170, 0, transparent(level))
            # elif race_type == "Pardas":  # Pardos
            #     color = (159, 212, 0, transparent(level))
            # elif race_type == "Indígenas":  # Indígenas
            #     color = (153, 102, 51, transparent(level))
            # else:
            #     continue

            # Desenha o ponto na imagem
            if image:
                draw.point((px * 512, py * 512), fill=color)

        # Salva o último tile
        if image:
            gtile = proj.GoogleTile(int(tms_tile[0]), int(tms_tile[1]), level)
            path = f"tiles/{level}/{int(gtile[0])}/{int(gtile[1])}.png"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            image.save(path)
            if eol == "":
                print()
            print(f"Último tile salvo em: {path}")


def main():
    parser = argparse.ArgumentParser(description="Processa dados geográficos.")
    # Adicionar um argumento para o caminho do arquivo GPKG, obrigatório que pode ser --gpkg-path ou -g
    parser.add_argument(
        "--gpkg-path",
        "-g",
        type=str,
        required=True,
        help="Caminho para o arquivo GPKG a ser processado.",
    )
    args = parser.parse_args()
    create_tile(args.gpkg_path)


if __name__ == "__main__":
    main()
