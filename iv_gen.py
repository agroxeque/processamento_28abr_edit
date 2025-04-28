#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para cálculo de índices de vegetação.

Este módulo contém funções para calcular diferentes índices de vegetação
a partir de imagens multiespectrais.
"""

import os
import logging
import numpy as np
from pathlib import Path
import rasterio

# Configuração de logging
logger = logging.getLogger(__name__)

def calcular_vari(caminho_ortomosaico, caminho_saida):
    """
    Calcula o índice de vegetação VARI (Visible Atmospherically Resistant Index).
    
    VARI = (G - R) / (G + R - B)
    
    Args:
        caminho_ortomosaico (Path): Caminho para o arquivo do ortomosaico
        caminho_saida (Path): Caminho para salvar o índice calculado
        
    Returns:
        Path: Caminho do arquivo de saída
        
    Raises:
        Exception: Se ocorrer um erro durante o cálculo
    """
    try:
        logger.info(f"Calculando índice VARI para {caminho_ortomosaico}")
        
        with rasterio.open(caminho_ortomosaico) as src:
            # Verificar se o ortomosaico tem pelo menos 3 bandas (RGB)
            if src.count < 3:
                raise ValueError("O ortomosaico deve ter pelo menos 3 bandas (RGB)")
            
            # Ler as bandas RGB
            red = src.read(1).astype(np.float32)
            green = src.read(2).astype(np.float32)
            blue = src.read(3).astype(np.float32)
            
            # Evitar divisão por zero
            epsilon = 1e-10
            denominador = green + red - blue
            denominador = np.where(np.abs(denominador) < epsilon, epsilon, denominador)
            
            # Calcular VARI
            vari = (green - red) / denominador
            
            # Limitar valores entre -1 e 1
            vari = np.clip(vari, -1.0, 1.0)
            
            # Preparar metadados para o arquivo de saída
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "dtype": "float32",
                "count": 1,
                "nodata": -9999
            })
            
            # Salvar o resultado
            with rasterio.open(caminho_saida, "w", **out_meta) as dest:
                dest.write(vari.astype(np.float32), 1)
        
        logger.info(f"Índice VARI calculado com sucesso: {caminho_saida}")
        return caminho_saida
    
    except Exception as e:
        logger.error(f"Erro ao calcular índice VARI: {str(e)}", exc_info=True)
        raise

def calcular_ndvi(caminho_ortomosaico, caminho_saida, banda_nir=4, banda_red=1):
    """
    Calcula o índice de vegetação NDVI (Normalized Difference Vegetation Index).
    
    NDVI = (NIR - RED) / (NIR + RED)
    
    Args:
        caminho_ortomosaico (Path): Caminho para o arquivo do ortomosaico
        caminho_saida (Path): Caminho para salvar o índice calculado
        banda_nir (int): Número da banda NIR no ortomosaico
        banda_red (int): Número da banda RED no ortomosaico
        
    Returns:
        Path: Caminho do arquivo de saída
    """
    try:
        logger.info(f"Calculando índice NDVI para {caminho_ortomosaico}")
        
        with rasterio.open(caminho_ortomosaico) as src:
            # Verificar se o ortomosaico tem as bandas necessárias
            if src.count < max(banda_nir, banda_red):
                raise ValueError(f"O ortomosaico deve ter pelo menos {max(banda_nir, banda_red)} bandas")
            
            # Ler as bandas NIR e RED
            nir = src.read(banda_nir).astype(np.float32)
            red = src.read(banda_red).astype(np.float32)
            
            # Evitar divisão por zero
            epsilon = 1e-10
            denominador = nir + red
            denominador = np.where(np.abs(denominador) < epsilon, epsilon, denominador)
            
            # Calcular NDVI
            ndvi = (nir - red) / denominador
            
            # Limitar valores entre -1 e 1
            ndvi = np.clip(ndvi, -1.0, 1.0)
            
            # Preparar metadados para o arquivo de saída
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "dtype": "float32",
                "count": 1,
                "nodata": -9999
            })
            
            # Salvar o resultado
            with rasterio.open(caminho_saida, "w", **out_meta) as dest:
                dest.write(ndvi.astype(np.float32), 1)
        
        logger.info(f"Índice NDVI calculado com sucesso: {caminho_saida}")
        return caminho_saida
    
    except Exception as e:
        logger.error(f"Erro ao calcular índice NDVI: {str(e)}")
        raise

def calcular_gndvi(caminho_ortomosaico, caminho_saida, banda_nir=4, banda_green=2):
    """
    Calcula o índice de vegetação GNDVI (Green Normalized Difference Vegetation Index).
    
    GNDVI = (NIR - GREEN) / (NIR + GREEN)
    
    Args:
        caminho_ortomosaico (Path): Caminho para o arquivo do ortomosaico
        caminho_saida (Path): Caminho para salvar o índice calculado
        banda_nir (int): Número da banda NIR no ortomosaico
        banda_green (int): Número da banda GREEN no ortomosaico
        
    Returns:
        Path: Caminho do arquivo de saída
    """
    try:
        logger.info(f"Calculando índice GNDVI para {caminho_ortomosaico}")
        
        with rasterio.open(caminho_ortomosaico) as src:
            # Verificar se o ortomosaico tem as bandas necessárias
            if src.count < max(banda_nir, banda_green):
                raise ValueError(f"O ortomosaico deve ter pelo menos {max(banda_nir, banda_green)} bandas")
            
            # Ler as bandas NIR e GREEN
            nir = src.read(banda_nir).astype(np.float32)
            green = src.read(banda_green).astype(np.float32)
            
            # Evitar divisão por zero
            epsilon = 1e-10
            denominador = nir + green
            denominador = np.where(np.abs(denominador) < epsilon, epsilon, denominador)
            
            # Calcular GNDVI
            gndvi = (nir - green) / denominador
            
            # Limitar valores entre -1 e 1
            gndvi = np.clip(gndvi, -1.0, 1.0)
            
            # Preparar metadados para o arquivo de saída
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "dtype": "float32",
                "count": 1,
                "nodata": -9999
            })
            
            # Salvar o resultado
            with rasterio.open(caminho_saida, "w", **out_meta) as dest:
                dest.write(gndvi.astype(np.float32), 1)
        
        logger.info(f"Índice GNDVI calculado com sucesso: {caminho_saida}")
        return caminho_saida
    
    except Exception as e:
        logger.error(f"Erro ao calcular índice GNDVI: {str(e)}")
        raise

def calcular_estatisticas_indice(caminho_indice):
    """
    Calcula estatísticas básicas de um índice de vegetação.
    
    Args:
        caminho_indice (Path): Caminho para o arquivo do índice
        
    Returns:
        dict: Dicionário com estatísticas (min, max, média, desvio padrão)
    """
    try:
        with rasterio.open(caminho_indice) as src:
            # Ler o índice
            indice = src.read(1)
            
            # Ignorar valores nodata
            nodata = src.nodata
            if nodata is not None:
                indice = indice[indice != nodata]
            
            # Calcular estatísticas
            estatisticas = {
                "min": float(np.min(indice)),
                "max": float(np.max(indice)),
                "media": float(np.mean(indice)),
                "mediana": float(np.median(indice)),
                "desvio_padrao": float(np.std(indice)),
                "percentil_25": float(np.percentile(indice, 25)),
                "percentil_75": float(np.percentile(indice, 75))
            }
            
            logger.info(f"Estatísticas calculadas: {estatisticas}")
            return estatisticas
    
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {str(e)}")
        return None
