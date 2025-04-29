#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para geração de relatórios.

Este módulo contém funções para gerar relatórios em PDF com análises
dos resultados do processamento de ortomosaicos.
"""

import matplotlib
matplotlib.use('Agg') # Definir backend Agg ANTES de importar pyplot
import os
import logging
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.patches import Patch
import rasterio
import geopandas as gpd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors as rl_colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from datetime import datetime
import tempfile
from PIL import Image as PILImage
from rasterio.enums import Resampling

# Configuração de logging
logger = logging.getLogger(__name__)

def gerar_relatorio(caminho_ortomosaico, caminho_indice, caminho_grade, caminho_poligono, caminho_saida):
    """
    Gera um relatório em PDF com análises dos resultados.
    
    Args:
        caminho_ortomosaico (Path): Caminho para o ortomosaico recortado
        caminho_indice (Path): Caminho para o arquivo do índice de vegetação
        caminho_grade (Path): Caminho para o arquivo GeoJSON da grade com ranking
        caminho_poligono (Path): Caminho para o arquivo GeoJSON do polígono
        caminho_saida (Path): Caminho para salvar o relatório
        
    Returns:
        Path: Caminho do relatório gerado
        
    Raises:
        Exception: Se ocorrer um erro durante a geração do relatório
    """
    try:
        logger.info(f"Iniciando geração do relatório para {caminho_saida}")
        
        # Criar diretório temporário para figuras
        logger.info("Criando diretório temporário para figuras...")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            logger.info(f"Diretório temporário criado: {temp_dir_path}")
            
            # Gerar figuras
            fig_ortomosaico = temp_dir_path / "ortomosaico.png"
            fig_indice = temp_dir_path / "indice.png"
            fig_grade = temp_dir_path / "grade.png"
            fig_histograma = temp_dir_path / "histograma.png"
            fig_categorias = temp_dir_path / "categorias.png"
            
            # Gerar visualizações
            logger.info("Iniciando geração da visualização do ortomosaico...")
            gerar_visualizacao_ortomosaico(caminho_ortomosaico, fig_ortomosaico)
            logger.info("Visualização do ortomosaico gerada.")

            logger.info("Iniciando geração da visualização do índice...")
            gerar_visualizacao_indice(caminho_indice, fig_indice)
            logger.info("Visualização do índice gerada.")

            logger.info("Iniciando geração da visualização da grade...")
            gerar_visualizacao_grade(caminho_grade, caminho_poligono, fig_grade)
            logger.info("Visualização da grade gerada.")

            logger.info("Iniciando geração do histograma do índice...")
            gerar_histograma_indice(caminho_indice, fig_histograma)
            logger.info("Histograma do índice gerado.")

            logger.info("Iniciando geração do gráfico de categorias...")
            gerar_grafico_categorias(caminho_grade, fig_categorias)
            logger.info("Gráfico de categorias gerado.")
            
            # Calcular estatísticas
            logger.info("Calculando métricas globais...")
            from ranking_gen import calcular_metricas_globais
            metricas = calcular_metricas_globais(caminho_grade)
            logger.info("Métricas globais calculadas.")
            
            # Criar PDF
            logger.info("Iniciando criação do documento PDF...")
            doc = SimpleDocTemplate(
                str(caminho_saida), # Garantir que seja string
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = styles["Title"]
            heading1_style = styles["Heading1"]
            heading2_style = styles["Heading2"]
            normal_style = styles["Normal"]
            
            # Elementos do relatório
            logger.info("Montando elementos do relatório...")
            elements = []
            
            # Título e data
            elements.append(Paragraph("Relatório de Análise de Ortomosaico", title_style))
            elements.append(Spacer(1, 0.25 * inch))
            elements.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y')}", normal_style))
            elements.append(Spacer(1, 0.5 * inch))
            
            # Seção 1: Visão Geral
            elements.append(Paragraph("1. Visão Geral", heading1_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Este relatório apresenta a análise do ortomosaico processado, incluindo o índice de vegetação VARI (Visible Atmospherically Resistant Index) e a classificação das células da grade.", normal_style))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Imagem do ortomosaico
            logger.info("Adicionando imagem do ortomosaico ao PDF...")
            elements.append(Paragraph("1.1. Ortomosaico Recortado", heading2_style))
            elements.append(Spacer(1, 0.1 * inch))
            img_orto = Image(str(fig_ortomosaico), width=6*inch, height=4*inch)
            img_orto.drawWidth = 6*inch # Definir explicitamente
            img_orto.drawHeight = 4*inch # Definir explicitamente
            elements.append(img_orto)
            elements.append(Spacer(1, 0.25 * inch))
            logger.info("Imagem do ortomosaico adicionada.")
            
            # Seção 2: Índice de Vegetação
            elements.append(Paragraph("2. Índice de Vegetação VARI", heading1_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("O índice VARI (Visible Atmospherically Resistant Index) é calculado pela fórmula: VARI = (G - R) / (G + R - B), onde G, R e B são as bandas verde, vermelha e azul, respectivamente.", normal_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Valores mais altos (verde) indicam vegetação mais saudável, enquanto valores mais baixos (vermelho) indicam vegetação menos saudável ou solo exposto.", normal_style))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Imagem do índice
            logger.info("Adicionando imagem do índice ao PDF...")
            img_indice = Image(str(fig_indice), width=6*inch, height=4*inch)
            img_indice.drawWidth = 6*inch
            img_indice.drawHeight = 4*inch
            elements.append(img_indice)
            elements.append(Spacer(1, 0.25 * inch))
            logger.info("Imagem do índice adicionada.")
            
            # Histograma
            logger.info("Adicionando histograma ao PDF...")
            elements.append(Paragraph("2.1. Distribuição de Valores do Índice", heading2_style))
            elements.append(Spacer(1, 0.1 * inch))
            img_hist = Image(str(fig_histograma), width=6*inch, height=3*inch)
            img_hist.drawWidth = 6*inch
            img_hist.drawHeight = 3*inch
            elements.append(img_hist)
            elements.append(Spacer(1, 0.25 * inch))
            logger.info("Histograma adicionado.")
            
            # Estatísticas do índice
            logger.info("Adicionando tabela de estatísticas do índice...")
            if metricas and "estatisticas_valor" in metricas:
                est = metricas["estatisticas_valor"]
                data = [
                    ["Estatística", "Valor"],
                    ["Mínimo", f"{est['min']:.4f}"],
                    ["Máximo", f"{est['max']:.4f}"],
                    ["Média", f"{est['media']:.4f}"],
                    ["Mediana", f"{est['mediana']:.4f}"],
                    ["Desvio Padrão", f"{est['desvio_padrao']:.4f}"]
                ]
                
                t = Table(data, colWidths=[2*inch, 2*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), rl_colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (1, 0), rl_colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, rl_colors.black)
                ]))
                
                elements.append(Paragraph("2.2. Estatísticas do Índice VARI", heading2_style))
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(t)
                elements.append(Spacer(1, 0.25 * inch))
                logger.info("Tabela de estatísticas do índice adicionada.")
            else:
                 logger.warning("Métricas de estatísticas do índice não encontradas.")
            
            # Seção 3: Classificação das Células
            elements.append(Paragraph("3. Classificação das Células", heading1_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("As células da grade foram classificadas com base no valor médio do índice VARI. A classificação é feita em percentis, onde as células são ordenadas do maior para o menor valor médio.", normal_style))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Imagem da grade
            logger.info("Adicionando imagem da grade ao PDF...")
            img_grade = Image(str(fig_grade), width=6*inch, height=4*inch)
            img_grade.drawWidth = 6*inch
            img_grade.drawHeight = 4*inch
            elements.append(img_grade)
            elements.append(Spacer(1, 0.25 * inch))
            logger.info("Imagem da grade adicionada.")
            
            # Gráfico de categorias
            logger.info("Adicionando gráfico de categorias ao PDF...")
            img_cat = Image(str(fig_categorias), width=6*inch, height=3*inch)
            img_cat.drawWidth = 6*inch
            img_cat.drawHeight = 3*inch
            elements.append(Paragraph("3.1. Distribuição de Categorias", heading2_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(img_cat)
            elements.append(Spacer(1, 0.25 * inch))
            logger.info("Gráfico de categorias adicionado.")
            
            # Estatísticas das categorias
            logger.info("Adicionando tabela de estatísticas das categorias...")
            if metricas and "contagem_categorias" in metricas and "percentual_categorias" in metricas:
                # Ordenar categorias
                categorias = ["Excelente", "Bom", "Médio", "Regular", "Ruim"]
                categorias = [c for c in categorias if c in metricas["contagem_categorias"]]
                
                data = [["Categoria", "Quantidade", "Percentual (%)"]]
                for cat in categorias:
                    if cat in metricas["contagem_categorias"]:
                        data.append([
                            cat,
                            str(metricas["contagem_categorias"][cat]),
                            f"{metricas['percentual_categorias'][cat]:.2f}"
                        ])
                
                t = Table(data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), rl_colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, rl_colors.black)
                ]))
                
                elements.append(Paragraph("3.2. Estatísticas das Categorias", heading2_style))
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(t)
                elements.append(Spacer(1, 0.25 * inch))
                logger.info("Tabela de estatísticas das categorias adicionada.")
            else:
                logger.warning("Métricas de categorias não encontradas.")

            # Seção 4: Conclusões
            elements.append(Paragraph("4. Conclusões", heading1_style))
            elements.append(Spacer(1, 0.1 * inch))
            
            # Gerar texto de conclusão com base nas métricas
            logger.info("Gerando texto de conclusão...")
            if metricas and "percentual_categorias" in metricas:
                percentual_bom_excelente = 0
                if "Excelente" in metricas["percentual_categorias"]:
                    percentual_bom_excelente += metricas["percentual_categorias"]["Excelente"]
                if "Bom" in metricas["percentual_categorias"]:
                    percentual_bom_excelente += metricas["percentual_categorias"]["Bom"]
                
                if percentual_bom_excelente > 60:
                    conclusao = f"A análise indica que a área apresenta condições predominantemente favoráveis, com {percentual_bom_excelente:.2f}% das células classificadas como 'Bom' ou 'Excelente'. Isso sugere uma vegetação saudável na maior parte da área analisada."
                elif percentual_bom_excelente > 30:
                    conclusao = f"A análise indica que a área apresenta condições moderadamente favoráveis, com {percentual_bom_excelente:.2f}% das células classificadas como 'Bom' ou 'Excelente'. Há oportunidades para melhorias em partes significativas da área."
                else:
                    conclusao = f"A análise indica que a área apresenta condições predominantemente desfavoráveis, com apenas {percentual_bom_excelente:.2f}% das células classificadas como 'Bom' ou 'Excelente'. Recomenda-se uma investigação mais detalhada para identificar as causas dos baixos valores do índice de vegetação."
            else:
                conclusao = "A análise do ortomosaico e do índice de vegetação VARI permitiu classificar as células da grade de acordo com a saúde da vegetação. Recomenda-se uma inspeção mais detalhada das áreas classificadas como 'Regular' ou 'Ruim' para identificar possíveis problemas."
            
            elements.append(Paragraph(conclusao, normal_style))
            elements.append(Spacer(1, 0.25 * inch))
            logger.info("Texto de conclusão adicionado.")
            
            # Gerar PDF
            logger.info("Iniciando a construção do PDF com reportlab (doc.build)...")
            doc.build(elements)
            logger.info("Construção do PDF finalizada.")
        
        logger.info(f"Relatório gerado com sucesso: {caminho_saida}")
        return caminho_saida
    
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {str(e)}", exc_info=True)
        raise

def gerar_visualizacao_ortomosaico(caminho_ortomosaico, caminho_saida):
    """
    Gera uma visualização do ortomosaico.
    
    Args:
        caminho_ortomosaico (Path): Caminho para o ortomosaico
        caminho_saida (Path): Caminho para salvar a visualização
    """
    logger.info("Iniciando gerar_visualizacao_ortomosaico...")
    try:
        with rasterio.open(caminho_ortomosaico) as src:
            logger.info("Lendo bandas RGB do ortomosaico com downsampling...")
            # Definir fator de downsampling para reduzir uso de memória na visualização
            downscale_factor = 4 
            out_shape = (
                3,
                int(src.height / downscale_factor),
                int(src.width / downscale_factor)
            )
            logger.info(f"Shape original: ({src.height}, {src.width}), Shape reamostrado: ({out_shape[1]}, {out_shape[2]})")

            # Ler as bandas RGB com reamostragem
            rgb_bands = src.read(
                (1, 2, 3), 
                out_shape=out_shape,
                resampling=Resampling.bilinear
            )
            red, green, blue = rgb_bands[0], rgb_bands[1], rgb_bands[2]
            # red = src.read(1)
            # green = src.read(2)
            # blue = src.read(3)
            
            logger.info("Normalizando bandas reamostradas...")
            # Normalizar valores para visualização
            def normalize(band):
                # Usar min/max em vez de percentil para reduzir uso de memória
                # min_val = np.percentile(band, 2)
                # max_val = np.percentile(band, 98)
                min_val = band.min()
                max_val = band.max()
                logger.info(f"Normalizando com min={min_val}, max={max_val}")
                # Evitar divisão por zero se min_val == max_val
                if max_val - min_val == 0:
                    logger.warning("Min e Max da banda são iguais, retornando banda zerada.")
                    return np.zeros_like(band, dtype=float) 
                return np.clip((band.astype(float) - min_val) / (max_val - min_val), 0, 1) # Garantir float
            
            red_norm = normalize(red)
            green_norm = normalize(green)
            blue_norm = normalize(blue)
            
            logger.info("Criando imagem RGB stack...")
            # Criar imagem RGB
            rgb = np.dstack((red_norm, green_norm, blue_norm))
            
            logger.info("Plotando imagem do ortomosaico com matplotlib...")
            # Plotar
            plt.figure(figsize=(10, 8))
            plt.imshow(rgb)
            plt.title("Ortomosaico Recortado")
            plt.axis('off')
            plt.tight_layout()
            logger.info(f"Salvando imagem do ortomosaico em {caminho_saida}...")
            plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
            plt.close()
            logger.info("Imagem do ortomosaico salva e plot fechado.")
    
    except Exception as e:
        logger.error(f"Erro dentro de gerar_visualizacao_ortomosaico: {str(e)}", exc_info=True)
        logger.info("Criando imagem de erro para ortomosaico...")
        # Criar uma imagem de erro
        plt.figure(figsize=(10, 8))
        plt.text(0.5, 0.5, "Erro ao gerar visualização do ortomosaico", 
                 horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()
    logger.info("Finalizando gerar_visualizacao_ortomosaico.")

def gerar_visualizacao_indice(caminho_indice, caminho_saida):
    """
    Gera uma visualização do índice de vegetação.
    
    Args:
        caminho_indice (Path): Caminho para o arquivo do índice
        caminho_saida (Path): Caminho para salvar a visualização
    """
    logger.info("Iniciando gerar_visualizacao_indice...")
    try:
        with rasterio.open(caminho_indice) as src:
            logger.info("Lendo dados do índice...")
            # Ler o índice
            indice = src.read(1)
            
            # Criar colormap personalizado para VARI
            cmap = plt.cm.RdYlGn
            
            logger.info("Plotando imagem do índice com matplotlib...")
            # Plotar
            plt.figure(figsize=(10, 8))
            im = plt.imshow(indice, cmap=cmap, vmin=-0.5, vmax=0.5)
            plt.colorbar(im, label="Valor do Índice VARI")
            plt.title("Índice de Vegetação VARI")
            plt.axis('off')
            plt.tight_layout()
            logger.info(f"Salvando imagem do índice em {caminho_saida}...")
            plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
            plt.close()
            logger.info("Imagem do índice salva e plot fechado.")
    
    except Exception as e:
        logger.error(f"Erro dentro de gerar_visualizacao_indice: {str(e)}", exc_info=True)
        logger.info("Criando imagem de erro para índice...")
        # Criar uma imagem de erro
        plt.figure(figsize=(10, 8))
        plt.text(0.5, 0.5, "Erro ao gerar visualização do índice", 
                 horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()
    logger.info("Finalizando gerar_visualizacao_indice.")

def gerar_visualizacao_grade(caminho_grade, caminho_poligono, caminho_saida):
    """
    Gera uma visualização da grade com ranking.
    
    Args:
        caminho_grade (Path): Caminho para o arquivo GeoJSON da grade
        caminho_poligono (Path): Caminho para o arquivo GeoJSON do polígono
        caminho_saida (Path): Caminho para salvar a visualização
    """
    logger.info("Iniciando gerar_visualizacao_grade...")
    try:
        logger.info("Lendo arquivos da grade e polígono com geopandas...")
        # Carregar a grade e o polígono
        grade = gpd.read_file(caminho_grade)
        poligono = gpd.read_file(caminho_poligono)
        
        # Definir cores para categorias
        cores_categorias = {
            "Excelente": "#1a9850",
            "Bom": "#91cf60",
            "Médio": "#ffffbf",
            "Regular": "#fc8d59",
            "Ruim": "#d73027"
        }
        
        logger.info("Plotando visualização da grade com matplotlib...")
        # Plotar
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plotar polígono
        poligono.boundary.plot(ax=ax, color='black', linewidth=1.5)
        
        # Plotar grade com cores por categoria
        logger.info("Iterando sobre categorias para plotar grade...")
        categorias_presentes = grade["categoria"].unique()
        for categoria, cor in cores_categorias.items():
            if categoria in categorias_presentes:
                logger.debug(f"Plotando categoria: {categoria}")
                grade[grade["categoria"] == categoria].plot(
                    ax=ax,
                    color=cor,
                    edgecolor='white',
                    linewidth=0.5,
                    alpha=0.7
                )
        logger.info("Plotagem da grade concluída.")
        
        # Adicionar legenda
        logger.info("Adicionando legenda...")
        patches = [Patch(color=cor, label=cat) for cat, cor in cores_categorias.items() 
                  if cat in categorias_presentes]
        ax.legend(handles=patches, title="Categorias", loc="lower right")
        
        # Configurar gráfico
        ax.set_title("Classificação das Células")
        ax.set_axis_off()
        plt.tight_layout()
        logger.info(f"Salvando imagem da grade em {caminho_saida}...")
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info("Imagem da grade salva e plot fechado.")
    
    except Exception as e:
        logger.error(f"Erro dentro de gerar_visualizacao_grade: {str(e)}", exc_info=True)
        logger.info("Criando imagem de erro para grade...")
        # Criar uma imagem de erro
        plt.figure(figsize=(10, 8))
        plt.text(0.5, 0.5, "Erro ao gerar visualização da grade", 
                 horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()
    logger.info("Finalizando gerar_visualizacao_grade.")

def gerar_histograma_indice(caminho_indice, caminho_saida):
    """
    Gera um histograma do índice de vegetação.
    
    Args:
        caminho_indice (Path): Caminho para o arquivo do índice
        caminho_saida (Path): Caminho para salvar o histograma
    """
    logger.info("Iniciando gerar_histograma_indice...")
    try:
        with rasterio.open(caminho_indice) as src:
            logger.info("Lendo dados do índice para histograma...")
            # Ler o índice
            indice = src.read(1)
            
            # Ignorar valores nodata
            nodata = src.nodata
            if nodata is not None:
                indice_valid = indice[indice != nodata]
                logger.info(f"Histograma: {len(indice.flatten()) - len(indice_valid)} pixels nodata ignorados.")
            else:
                 indice_valid = indice.flatten()

            if indice_valid.size == 0:
                logger.warning("Não há dados válidos no índice para gerar histograma.")
                raise ValueError("Não há dados válidos no índice para gerar histograma.")

            logger.info(f"Histograma: {len(indice_valid)} pixels válidos.")
            
            # Limitar valores para melhor visualização
            indice_clipped = np.clip(indice_valid, -0.5, 0.5)
            logger.info("Valores do índice clipados entre -0.5 e 0.5 para histograma.")
            
            # Plotar histograma
            logger.info("Plotando histograma com matplotlib...")
            plt.figure(figsize=(10, 6))
            plt.hist(indice_clipped, bins=50, color='#4CAF50', alpha=0.7)
            plt.title("Distribuição de Valores do Índice VARI")
            plt.xlabel("Valor do Índice")
            plt.ylabel("Frequência")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            logger.info(f"Salvando histograma em {caminho_saida}...")
            plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
            plt.close()
            logger.info("Histograma salvo e plot fechado.")
    
    except Exception as e:
        logger.error(f"Erro dentro de gerar_histograma_indice: {str(e)}", exc_info=True)
        logger.info("Criando imagem de erro para histograma...")
        # Criar uma imagem de erro
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "Erro ao gerar histograma", 
                 horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()
    logger.info("Finalizando gerar_histograma_indice.")

def gerar_grafico_categorias(caminho_grade, caminho_saida):
    """
    Gera um gráfico de barras com a contagem de células por categoria.
    
    Args:
        caminho_grade (Path): Caminho para o arquivo GeoJSON da grade
        caminho_saida (Path): Caminho para salvar o gráfico
    """
    logger.info("Iniciando gerar_grafico_categorias...")
    try:
        logger.info("Lendo arquivo da grade com geopandas...")
        # Carregar a grade
        grade = gpd.read_file(caminho_grade)
        
        logger.info("Contando células por categoria...")
        # Contar células por categoria
        contagem = grade["categoria"].value_counts()
        
        # Ordenar categorias
        ordem_categorias = ["Excelente", "Bom", "Médio", "Regular", "Ruim"]
        contagem = contagem.reindex(ordem_categorias).fillna(0) # Garantir que todas as categorias existam
        
        # Definir cores
        cores = ["#1a9850", "#91cf60", "#ffffbf", "#fc8d59", "#d73027"]
        
        logger.info("Plotando gráfico de barras de categorias...")
        # Plotar gráfico de barras
        plt.figure(figsize=(10, 6))
        bars = plt.bar(contagem.index, contagem.values, color=cores)
        plt.title("Distribuição de Células por Categoria")
        plt.xlabel("Categoria")
        plt.ylabel("Número de Células")
        plt.grid(True, axis='y', alpha=0.3)
        plt.tight_layout()
        logger.info(f"Salvando gráfico de categorias em {caminho_saida}...")
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info("Gráfico de categorias salvo e plot fechado.")
    
    except Exception as e:
        logger.error(f"Erro dentro de gerar_grafico_categorias: {str(e)}", exc_info=True)
        logger.info("Criando imagem de erro para gráfico de categorias...")
        # Criar uma imagem de erro
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "Erro ao gerar gráfico de categorias", 
                 horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()
    logger.info("Finalizando gerar_grafico_categorias.")
