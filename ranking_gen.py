#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para geração de ranking de células.

Este módulo contém funções para classificar e rankear células de uma grade
com base em índices de vegetação.
"""

import os
import logging
import numpy as np
from pathlib import Path
import rasterio
import geopandas as gpd
from shapely.geometry import shape, mapping
import json
from rasterio.features import rasterize
import pandas as pd
from rasterstats import zonal_stats

# Configuração de logging
logger = logging.getLogger(__name__)

def gerar_ranking(caminho_indice, caminho_grade, caminho_saida):
    """
    Gera um ranking de células com base em um índice de vegetação.
    
    Args:
        caminho_indice (Path): Caminho para o arquivo do índice de vegetação
        caminho_grade (Path): Caminho para o arquivo GeoJSON da grade de entrada
        caminho_saida (Path): Caminho para salvar a grade com ranking
        
    Returns:
        Path: Caminho do arquivo de saída
        
    Raises:
        Exception: Se ocorrer um erro durante o processo
    """
    try:
        logger.info(f"Gerando ranking para {caminho_grade} com base em {caminho_indice}")
        
        # Carregar a grade
        grade = gpd.read_file(caminho_grade)
        
        # Verificar se a grade está vazia
        if grade.empty:
            raise ValueError("A grade de entrada está vazia ou inválida")
        
        # Calcular estatísticas zonais para cada célula
        stats = zonal_stats(
            grade,
            caminho_indice,
            stats=["min", "max", "mean", "median", "std", "count"],
            geojson_out=True,
            nodata=-9999
        )
        
        # Converter para GeoDataFrame
        gdf_stats = gpd.GeoDataFrame.from_features(stats)
        
        # Adicionar identificador único se não existir
        if "id" not in gdf_stats.columns:
            gdf_stats["id"] = range(1, len(gdf_stats) + 1)
        
        # Classificar células com base na média do índice
        # Para VARI, valores mais altos indicam vegetação mais saudável
        gdf_stats["valor_medio"] = gdf_stats["mean"]
        
        # Ordenar células pelo valor médio (decrescente)
        gdf_stats = gdf_stats.sort_values(by="valor_medio", ascending=False)
        
        # Atribuir ranking
        gdf_stats["ranking"] = range(1, len(gdf_stats) + 1)
        
        # Calcular percentil
        gdf_stats["percentil"] = 100 * (1 - (gdf_stats["ranking"] / len(gdf_stats)))
        
        # Classificar em categorias
        def classificar_celula(percentil):
            if percentil >= 80:
                return "Excelente"
            elif percentil >= 60:
                return "Bom"
            elif percentil >= 40:
                return "Médio"
            elif percentil >= 20:
                return "Regular"
            else:
                return "Ruim"
        
        gdf_stats["categoria"] = gdf_stats["percentil"].apply(classificar_celula)
        
        # Salvar o resultado
        gdf_stats.to_file(caminho_saida, driver="GeoJSON")
        
        logger.info(f"Ranking gerado com sucesso: {caminho_saida}")
        return caminho_saida
    
    except Exception as e:
        logger.error(f"Erro ao gerar ranking: {str(e)}", exc_info=True)
        raise

def calcular_metricas_globais(caminho_grade_ranking):
    """
    Calcula métricas globais a partir da grade com ranking.
    
    Args:
        caminho_grade_ranking (Path): Caminho para o arquivo GeoJSON da grade com ranking
        
    Returns:
        dict: Dicionário com métricas globais
    """
    try:
        # Carregar a grade com ranking
        grade = gpd.read_file(caminho_grade_ranking)
        
        # Calcular métricas por categoria
        contagem_categorias = grade["categoria"].value_counts().to_dict()
        percentual_categorias = (grade["categoria"].value_counts(normalize=True) * 100).to_dict()
        
        # Calcular área por categoria
        grade["area"] = grade.geometry.area
        area_total = grade["area"].sum()
        area_por_categoria = grade.groupby("categoria")["area"].sum().to_dict()
        percentual_area = {k: (v / area_total) * 100 for k, v in area_por_categoria.items()}
        
        # Estatísticas do valor médio
        estatisticas_valor = {
            "min": float(grade["valor_medio"].min()),
            "max": float(grade["valor_medio"].max()),
            "media": float(grade["valor_medio"].mean()),
            "mediana": float(grade["valor_medio"].median()),
            "desvio_padrao": float(grade["valor_medio"].std())
        }
        
        # Compilar métricas
        metricas = {
            "total_celulas": len(grade),
            "contagem_categorias": contagem_categorias,
            "percentual_categorias": percentual_categorias,
            "area_total": float(area_total),
            "area_por_categoria": area_por_categoria,
            "percentual_area_por_categoria": percentual_area,
            "estatisticas_valor": estatisticas_valor
        }
        
        logger.info(f"Métricas globais calculadas: {metricas}")
        return metricas
    
    except Exception as e:
        logger.error(f"Erro ao calcular métricas globais: {str(e)}")
        return None

def identificar_hotspots(caminho_grade_ranking, limiar_percentil=90):
    """
    Identifica hotspots (áreas de interesse) com base no ranking.
    
    Args:
        caminho_grade_ranking (Path): Caminho para o arquivo GeoJSON da grade com ranking
        limiar_percentil (float): Percentil mínimo para considerar uma célula como hotspot
        
    Returns:
        GeoDataFrame: GeoDataFrame contendo apenas os hotspots
    """
    try:
        # Carregar a grade com ranking
        grade = gpd.read_file(caminho_grade_ranking)
        
        # Filtrar células acima do limiar
        hotspots = grade[grade["percentil"] >= limiar_percentil].copy()
        
        logger.info(f"Identificados {len(hotspots)} hotspots com percentil >= {limiar_percentil}")
        return hotspots
    
    except Exception as e:
        logger.error(f"Erro ao identificar hotspots: {str(e)}")
        return None
