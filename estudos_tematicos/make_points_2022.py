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
base_path = "/home/kylefelipe/mapa_repo/estudos_tematicos/COR_RACA/2022"
csv_folder = path.join(base_path, "CSVS")
rand_folder = path.join(base_path, "pontos_aleatorios")
makedirs(rand_folder, exist_ok=True)

agregado_file = next(iter(glob(path.join(csv_folder, "*.csv"))))
states = [
    "AC",
    "AL",
    "AM",
    # "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    # "PE", #! Parrou na organização do arquivo
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    # "SP", #! Parrou na organização do arquivo
    "TO",
    # "SP",
]
# Lendo o arquivo csv de pessoas
pessoa_fields = {
    "V01317": "pessoas_brancas",
    "V01318": "pessoas_pretas",
    "V01319": "pessoas_amarelas",
    "V01320": "pessoas_pardas",
    "V01321": "pessoas_indigenas",
    "CD_SETOR": "CD_SETOR",
}
pessoa_fields_dypes = {
    "V01317": "Int64",
    "V01318": "Int64",
    "V01319": "Int64",
    "V01320": "Int64",
    "V01321": "Int64",
    "CD_SETOR": "object",
}
setor_fiels = {"v0001": "total_pessoas"}
setor_keep_fields = [
    "CD_SETOR",
    "SITUACAO",
    "CD_SIT",
    "CD_TIPO",
    "AREA_KM2",
    "CD_REGIAO",
    "NM_REGIAO",
    "CD_UF",
    "NM_UF",
    "CD_MUN",
    "NM_MUN",
    "CD_DIST",
    "NM_DIST",
    "CD_SUBDIST",
    "NM_SUBDIST",
    "CD_BAIRRO",
    "NM_BAIRRO",
    "CD_NU",
    "NM_NU",
    "CD_FCU",
    "NM_FCU",
    "CD_AGLOM",
    "NM_AGLOM",
    "CD_RGINT",
    "NM_RGINT",
    "CD_RGI",
    "NM_RGI",
    "CD_CONCURB",
    "NM_CONCURB",
    "v0001",
    "geometry",
]


int_fields = {
    "V01317": "pessoas_brancas",
    "V01318": "pessoas_pretas",
    "V01319": "pessoas_amarelas",
    "V01320": "pessoas_pardas",
    "V01321": "pessoas_indigenas",
}
race_fields = {
    "pessoas_brancas": "Brancos",
    "pessoas_pretas": "Pretos",
    "pessoas_amarelas": "Amarelas",
    "pessoas_pardas": "Pardos",
    "pessoas_indigenas": "Indígenas",
}

points_cols = [
    "CD_SETOR",
    "SITUACAO",
    "CD_SIT",
    "CD_TIPO",
    "AREA_KM2",
    "CD_REGIAO",
    "NM_REGIAO",
    "CD_UF",
    "NM_UF",
    "CD_MUN",
    "NM_MUN",
    "CD_DIST",
    "NM_DIST",
    "CD_SUBDIST",
    "NM_SUBDIST",
    "CD_BAIRRO",
    "NM_BAIRRO",
    "CD_NU",
    "NM_NU",
    "CD_FCU",
    "NM_FCU",
    "CD_AGLOM",
    "NM_AGLOM",
    "CD_RGINT",
    "NM_RGINT",
    "CD_RGI",
    "NM_RGI",
    "CD_CONCURB",
    "NM_CONCURB",
    "total_pessoas",
    *race_fields.keys(),
    "raca_cor",
    "tile_x",
    "tile_y",
    "quadkey",
    "geometry",
]

# %%

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


# %% [markdown]
# Abrindo o arquivo de agregados pegando apenas os campos necessários

# %%
pessoa_df = pd.read_csv(
    agregado_file,
    sep=";",
    encoding="latin1",
    usecols=[*pessoa_fields.keys()],  # * abrimos apenas as colunas que precisamos
    na_values=["X"],  # * aqui estamos transformando em x em NaN/None
    dtype=pessoa_fields_dypes,  # * aqui estamos informando os tipos corretos dos campos
)

pessoa_df.rename(columns=pessoa_fields, inplace=True)

pessoa_cols = pessoa_df.columns

# %% [markdown]
# # Trabalhando os setores sensitários
#
# Aqui vamos abrir cada um dos arquivos de setores censitários que baixamos anteriormente, renomear o campo `v0001` para `total_pessoas`.
# Em seguida iremos fazer a união dos dados do censo de 2022 (pessoa_df) com os setores censitários usando o campo `CD_SETOR` para comparação.
#
# Após a união, geramos pontos aleatórios para cada pessoa da raça/cor e salvamos em um arquivo geopackage que será ordenado pelo campo `quadkey` no final do processo.

# %%
# Lendo setores sensitários
setor_sensitario_folder = path.join(
    "/",
    "home",
    "kylefelipe",
    "mapa_repo",
    "estudos_tematicos",
    "SETORES_CENSITARIOS",
    "2022",
    "gpkg",
)
# lista os arquivos dos estados dentro da pasta de setores sensitários usando glob
setores_sensitarios_files = glob(path.join(setor_sensitario_folder, "*.gpkg"))

for setor_censitario_path in setores_sensitarios_files:
    sigla_uf = path.basename(setor_censitario_path).split("_")[0].lower()
    if sigla_uf.upper() not in states:
        continue
    print(f"Processando {sigla_uf}")
    setor_censitario_gdf = gpd.read_file(setor_censitario_path)
    # Remove colunas que não são necessárias
    setor_censitario_gdf.drop(
        columns=[c for c in setor_censitario_gdf.columns if c not in setor_keep_fields],
        inplace=True,
    )
    # Renomeia as colunas
    setor_censitario_gdf.rename(columns=setor_fiels, inplace=True)
    # Fazendo a união das tabelas
    joined_gdf = setor_censitario_gdf.merge(pessoa_df, on="CD_SETOR", how="left")
    # limpa a memória do setor censitário
    del setor_censitario_gdf
    crs = joined_gdf.crs
    output_file = path.join(rand_folder, f"{sigla_uf}_pontos_pessoas.gpkg")
    makedirs(path.dirname(output_file), exist_ok=True)
    cols_to_keep = [col for col in joined_gdf.columns if col not in ["geometry"]]

    # criando os pontos aleatórios do estado
    for idx, row in tqdm(
        joined_gdf.iterrows(),
        desc="Processando setores",
        unit="setor",
        total=joined_gdf.shape[0],
    ):
        # Barra de progresso para raças (loop interno)
        for race, race_label in tqdm(
            race_fields.items(),
            desc=f"Setor {row['CD_SETOR']}",
            unit="raça",
            leave=False,
        ):
            qt_pessoas = row[race]
            if pd.isnull(qt_pessoas) or qt_pessoas == 0:
                continue
            qt_pessoas = qt_pessoas

            # Gera pontos aleatórios para a raça atual
            points = generate_random_points(row.geometry, qt_pessoas)

            # Cria o GeoDataFrame para os pontos
            points_gdf = gpd.GeoDataFrame(
                {
                    "geometry": points,
                    "raca_cor": [race_label] * len(points),
                },
                crs=crs,
            )

            # Adiciona atributos da linha ao GeoDataFrame
            for col in cols_to_keep:
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
            # reordena as colunas
            points_gdf = points_gdf[points_cols]

            # Exporta os dados para o arquivo GPKG
            mode = "a" if path.exists(output_file) else "w"
            points_gdf.to_file(output_file, driver="GPKG", mode=mode)
            # limpa a memória dos pontos
            del points_gdf

    # limpa a memória do setor censitário
    print(f"Arquivo do estado {sigla_uf} processado")
    del joined_gdf

    # print("Ordenando o arquivo")
    # raca_cor_gdf = gpd.read_file(output_file)
    # raca_cor_gdf.sort_values(by="quadkey", inplace=True)
    # raca_cor_gdf.to_file(output_file, driver="GPKG", mode="w")
    # print(f"Arquivo do estado {sigla_uf} ordenado")
    # # limpa a memória do raca_cor_gdf
    # del raca_cor_gdf

# %%



