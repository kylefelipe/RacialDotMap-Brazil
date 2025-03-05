# %% [markdown]
# # Documentação
#
# Baixa setores de 2010 : https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/26565-malhas-de-setores-censitarios-divisoes-intramunicipais.html?edicao=26589&t=downloads
#
#
# Mala de setores Sensitários: https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/26565-malhas-de-setores-censitarios-divisoes-intramunicipais.html

# %%
# Importing libraries

import pandas as pd
import geopandas as gpd
from os import path, makedirs, remove
from glob import glob
from shapely.geometry import Point, MultiPoint
import numpy as np
from globalmaptiles import GlobalMercator
from tqdm import tqdm

# %%
# Defining the paths
base_path = "/home/kylefelipe/mapa_repo/estudos_tematicos/COR_RACA/CSVS"
rand_folder = "/home/kylefelipe/mapa_repo/estudos_tematicos/COR_RACA/pontos_aleatorios"
makedirs(rand_folder, exist_ok=True)

csv_pessoa_base = path.join(base_path, "Pessoa03_{sigla_uf}.csv")

csv_files = glob(path.join(base_path, "*.csv"))
states = [
    # "AC",
    "AL",
    # "AM",
    # "AP",
    # "BA", #! Verificar pois é muito grande, ordenar
    # "CE",
    # "DF",
    "ES",
    # "GO",
    # "MA",
    # "MG", #! Verificar pois é muito grande, ordenar
    # "MS",
    "MT",
    # "PA",
    # "PB",
    "PE", #! Verificar pois deu DtypeWarning em várias colunas
    # "PI",
    "PR",
    # "RJ", #! Verificar pois é muito grande, ordenar
    # "RN",
    "RO",
    # "RR",
    # "RS",
    # "SC",
    # "SE",
    "SP",
    # "TO",
    # "SP",
]


# %%
# Lendo o arquivo csv de pessoas
pessoa_fields = {
    "V001": "pop_field",
    "V002": "white_field",
    "V003": "black_field",
    "V004": "asian_field",
    "V005": "pardos_field",
    "V006": "indigena_field",
    "Cod_setor": "statefips_field",
}

int_fields = {
    "V001": "pop_field",
    "V002": "white_field",
    "V003": "black_field",
    "V004": "asian_field",
    "V005": "pardos_field",
    "V006": "indigena_field",
}
race_fields = {
    "white_field": "Brancos",
    "black_field": "Pretos",
    "asian_field": "Asiáticos",
    "pardos_field": "Pardos",
    "indigena_field": "Indígenas",
}
merc = GlobalMercator()


# Função para gerar N pontos aleatórios dentro de uma geometria
def generate_random_points(geometry, num_points):
    minx, miny, maxx, maxy = geometry.bounds
    points = []
    while len(points) < num_points:
        random_x = np.random.uniform(minx, maxx, num_points)
        random_y = np.random.uniform(miny, maxy, num_points)
        candidate_points = MultiPoint([Point(x, y) for x, y in zip(random_x, random_y)])
        # Filtra apenas os pontos dentro da geometria
        points_within = [p for p in candidate_points.geoms if geometry.contains(p)]
        points.extend(points_within)
    return points[:num_points]


#####
csv_pessoa_bar = tqdm(
    csv_files,
    desc="Processando arquivos CSV",
    unit="arquivo",
    leave=True,
    ncols=20,
)
for csv_pessoa in csv_pessoa_bar:
    filename = path.basename(csv_pessoa)
    sigla_uf = filename.split("_")[1].split(".")[0]
    csv_pessoa_bar.write(f"{sigla_uf}")
    if not sigla_uf.upper() in states:
        continue
    output_file = path.join(rand_folder, f"{sigla_uf.lower()}_pontos_pessoas.gpkg")
    if path.exists(output_file):
        # Remove o arquivo
        tqdm.write(f"Removendo {output_file}")
        remove(output_file)

    pessoa_df = pd.read_csv(csv_pessoa, sep=";", encoding="latin1")
    pessoa_df["CD_GEOCODI"] = pessoa_df["Cod_setor"].astype(str)
    pessoa_df = pessoa_df.rename(columns=pessoa_fields)
    # Remover colunas que não são de interesse
    cols_to_remove = [
        col
        for col in pessoa_df.columns
        if col not in [*pessoa_fields.values(), "CD_GEOCODI"]
    ]
    pessoa_df = pessoa_df.drop(columns=cols_to_remove)

    pessoa_cols = pessoa_df.columns
    # Lendo setores sensitários
    setor_sensitario_path = path.join(
        "/home/kylefelipe/mapa_repo/estudos_tematicos/SETORES_CENSITARIOS/gpkg",
        f"{sigla_uf.lower()}_setores_censitarios.gpkg",
    )
    setor_sensitario_gdf = gpd.read_file(setor_sensitario_path)
    joined_gdf = setor_sensitario_gdf.merge(pessoa_df, on="CD_GEOCODI", how="left")
    joined_gdf = joined_gdf.infer_objects(copy=False)
    joined_gdf["statefips_field"] = joined_gdf["statefips_field"].astype(str).str[:2]

    col_bar = tqdm(
        int_fields.values(),
        desc="  Processando colunas",
        unit="coluna",
        ncols=20,
        leave=False,
    )

    for col in col_bar:
        col_bar.set_postfix_str(f" coluna: {col}")
        # Verifica se a coluna é do tipo texto
        if joined_gdf[col].dtype == "object":
            # Substitui X por None
            if joined_gdf[col].str.contains("X").any():
                joined_gdf[col] = joined_gdf[col].replace("X", None)

        # Muda o tipo da coluna para inteiro
        joined_gdf[col] = joined_gdf[col].apply(
            lambda x: int(x) if pd.notnull(x) else None
        )

    crs = joined_gdf.crs

    # Barra de progresso para setores
    setor_bar = tqdm(
        joined_gdf.iterrows(),
        desc="Processando setores",
        unit="setor",
        total=joined_gdf.shape[0],
        # leave=F,
    )
    for idx, row in setor_bar:
        setor_bar.set_postfix_str(f"setor: {row['CD_GEOCODI']}")
        # tqdm.write(f"Trabalhando no setor {row['CD_GEOCODI']}")
        # gerando os pontos aleatórios para as raças
        for race, race_label in race_fields.items():
            qt_pessoas = row[race]
            if pd.isnull(qt_pessoas) or qt_pessoas == 0:
                continue
            qt_pessoas = int(qt_pessoas)

            # Gera pontos aleatórios para a raça atual
            points = generate_random_points(row.geometry, qt_pessoas)

            # Cria o GeoDataFrame para os pontos
            points_gdf = gpd.GeoDataFrame(
                {
                    "geometry": points,
                    "race_type": [race_label] * len(points),
                },
                crs=crs,
            )

            # Adiciona atributos da linha ao GeoDataFrame
            for col in pessoa_cols:
                points_gdf[col] = row[col]

            # Calcula quadkey e outros atributos
            points_gdf["tile_x"], points_gdf["tile_y"], points_gdf["quadkey"] = zip(
                *[
                    (
                        *merc.MetersToTile(*merc.LatLonToMeters(p.y, p.x), 21),
                        merc.QuadTree(
                            *merc.MetersToTile(*merc.LatLonToMeters(p.y, p.x), 21), 21
                        ),
                    )
                    for p in points
                ]
            )

            # Exporta os dados para o arquivo GPKG
            mode = "a" if path.exists(output_file) else "w"
            points_gdf.to_file(output_file, driver="GPKG", mode=mode)
        setor_bar.set_postfix_str("")
    # Ordena os pontos pelo quadkey
    print("Ordenando pontos")
    points_gdf = gpd.read_file(output_file)
    points_gdf = points_gdf.sort_values(by="quadkey")
    points_gdf.to_file(output_file, driver="GPKG", mode="w")
    # >>>>>>>>>>>
    # break

#     for idx, row in joined_gdf.iterrows():
#         print(f"Trabalhando no setor {row['CD_GEOCODI']}")
#         bbox = row.geometry.bounds
#         leftmost, bottommost, rightmost, topmost = bbox
#         for race in race_fields.keys():
#             qt_pessoas = int(row[race])
#             print(f"Qt {race} {qt_pessoas}")
#             # Cria um ponto aleatório dentro da geometria para cada pessoa
#             for i in range(qt_pessoas):
#                 while True:
#                     x = np.random.uniform(leftmost, rightmost)
#                     y = np.random.uniform(bottommost, topmost)
#                     point = Point(x, y)
#                     # verifica se o ponto cai dentro da geometria
#                     if row.geometry.contains(point):
#                         break

#                 # adiciona os atributos da linha ao ponto
#                 point_gdf = gpd.GeoDataFrame([point], columns=["geometry"])
#                 mx, my = merc.LatLonToMeters(y, x)
#                 tx, ty = merc.MetersToTile(mx, my, 21)
#                 quadkey = merc.QuadTree(tx, ty, 21)
#                 race_type = race_fields[race]
#                 point_gdf["race_type"] = race_fields[race]
#                 for col in pessoa_cols:
#                     point_gdf[col] = row[col]
#                 mode = "a" if path.exists(output_file) else "w"
#                 # set crs
#                 point_gdf.crs = crs
#                 # exporta o geodataframe para um arquivo gpkg
#                 point_gdf.to_file(output_file, driver="GPKG", mode=mode)
#     # ordena o arquivo por quadkey
#     points_gdf = gpd.read_file(output_file)
#     points_gdf = points_gdf.sort_values(by="quadkey")
#     # substitui o arquivo original pelo arquivo ordenado
#     points_gdf.to_file(output_file, driver="GPKG", mode="w")
