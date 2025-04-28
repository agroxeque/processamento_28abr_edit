#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para recorte de ortomosaicos.

Este módulo contém funções para recortar ortomosaicos usando polígonos
georreferenciados.
"""

import os
import logging
import numpy as np
from pathlib import Path
import rasterio
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import shape

# Configuração de logging
logger = logging.getLogger(__name__)

def recortar(caminho_ortomosaico, caminho_poligono, caminho_saida):
    """
    Recorta um ortomosaico usando um polígono.
    
    Args:
        caminho_ortomosaico (Path): Caminho para o arquivo do ortomosaico
        caminho_poligono (Path): Caminho para o arquivo GeoJSON do polígono
        caminho_saida (Path): Caminho para salvar o ortomosaico recortado
        
    Returns:
        Path: Caminho do ortomosaico recortado
        
    Raises:
        Exception: Se ocorrer um erro durante o recorte
    """
    try:
        logger.info(f"Iniciando recorte do ortomosaico {caminho_ortomosaico}")
        
        # Carregar o polígono
        gdf = gpd.read_file(caminho_poligono)
        
        # Verificar se o GeoDataFrame está vazio
        if gdf.empty:
            raise ValueError("O arquivo do polígono está vazio ou inválido")
        
        # Extrair geometrias para o recorte
        geometrias = [shape(geom) for geom in gdf.geometry]
        
        # Abrir o ortomosaico
        with rasterio.open(caminho_ortomosaico) as src:
            # Realizar o recorte
            out_image, out_transform = mask(src, geometrias, crop=True, all_touched=True)
            
            # Atualizar metadados
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform
            })
            
            # Salvar o resultado
            with rasterio.open(caminho_saida, "w", **out_meta) as dest:
                dest.write(out_image)
        
        logger.info(f"Recorte concluído com sucesso: {caminho_saida}")
        return caminho_saida
    
    except Exception as e:
        logger.error(f"Erro ao recortar ortomosaico: {str(e)}", exc_info=True)
        raise

def verificar_cobertura_nuvens(caminho_ortomosaico, limiar=0.2):
    """
    Verifica a cobertura de nuvens em um ortomosaico.
    
    Esta é uma implementação simplificada que pode ser aprimorada com
    algoritmos mais sofisticados de detecção de nuvens.
    
    Args:
        caminho_ortomosaico (Path): Caminho para o arquivo do ortomosaico
        limiar (float): Limiar de brilho para considerar um pixel como nuvem (0-1)
        
    Returns:
        float: Porcentagem de cobertura de nuvens (0-1)
    """
    try:
        with rasterio.open(caminho_ortomosaico) as src:
            # Ler as bandas visíveis (assumindo RGB)
            red = src.read(1).astype(float) / 255.0
            green = src.read(2).astype(float) / 255.0
            blue = src.read(3).astype(float) / 255.0
            
            # Calcular brilho
            brilho = (red + green + blue) / 3.0
            
            # Contar pixels acima do limiar
            pixels_nuvem = np.sum(brilho > limiar)
            total_pixels = red.size
            
            # Calcular porcentagem
            porcentagem = pixels_nuvem / total_pixels
            
            logger.info(f"Cobertura de nuvens estimada: {porcentagem:.2%}")
            return porcentagem
    
    except Exception as e:
        logger.error(f"Erro ao verificar cobertura de nuvens: {str(e)}")
        return None

def verificar_qualidade_ortomosaico(caminho_ortomosaico):
    """
    Verifica a qualidade geral do ortomosaico.
    
    Args:
        caminho_ortomosaico (Path): Caminho para o arquivo do ortomosaico
        
    Returns:
        dict: Dicionário com métricas de qualidade
    """
    try:
        metricas = {}
        
        with rasterio.open(caminho_ortomosaico) as src:
            # Verificar resolução
            transform = src.transform
            resolucao_x = abs(transform[0])
            resolucao_y = abs(transform[4])
            metricas["resolucao"] = (resolucao_x + resolucao_y) / 2
            
            # Verificar número de bandas
            metricas["num_bandas"] = src.count
            
            # Verificar tamanho
            metricas["largura"] = src.width
            metricas["altura"] = src.height
            
            # Verificar sistema de coordenadas
            metricas["crs"] = src.crs.to_string()
            
            # Verificar valores nulos
            banda1 = src.read(1)
            metricas["porcentagem_nulos"] = np.sum(banda1 == 0) / banda1.size
        
        # Verificar cobertura de nuvens
        metricas["cobertura_nuvens"] = verificar_cobertura_nuvens(caminho_ortomosaico)
        
        logger.info(f"Métricas de qualidade calculadas: {metricas}")
        return metricas
    
    except Exception as e:
        logger.error(f"Erro ao verificar qualidade do ortomosaico: {str(e)}")
        return None
