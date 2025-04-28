#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para geração de relatórios.

Este módulo contém funções para gerar relatórios em PDF com análises
dos resultados do processamento de ortomosaicos.
"""

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
        logger.info(f"Gerando relatório para {caminho_saida}")
        
        # Criar diretório temporário para figuras
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            # Gerar figuras
            fig_ortomosaico = temp_dir_path / "ortomosaico.png"
            fig_indice = temp_dir_path / "indice.png"
            fig_grade = temp_dir_path / "grade.png"
            fig_histograma = temp_dir_path / "histograma.png"
            fig_categorias = temp_dir_path / "categorias.png"
            
            # Gerar visualizações
            gerar_visualizacao_ortomosaico(caminho_ortomosaico, fig_ortomosaico)
            gerar_visualizacao_indice(caminho_indice, fig_indice)
            gerar_visualizacao_grade(caminho_grade, caminho_poligono, fig_grade)
            gerar_histograma_indice(caminho_indice, fig_histograma)
            gerar_grafico_categorias(caminho_grade, fig_categorias)
            
            # Calcular estatísticas
            from ranking_gen import calcular_metricas_globais
            metricas = calcular_metricas_globais(caminho_grade)
            
            # Criar PDF
            doc = SimpleDocTemplate(
                caminho_saida,
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
            elements.append(Paragraph("1.1. Ortomosaico Recortado", heading2_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Image(str(fig_ortomosaico), width=6*inch, height=4*inch))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Seção 2: Índice de Vegetação
            elements.append(Paragraph("2. Índice de Vegetação VARI", heading1_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("O índice VARI (Visible Atmospherically Resistant Index) é calculado pela fórmula: VARI = (G - R) / (G + R - B), onde G, R e B são as bandas verde, vermelha e azul, respectivamente.", normal_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Valores mais altos (verde) indicam vegetação mais saudável, enquanto valores mais baixos (vermelho) indicam vegetação menos saudável ou solo exposto.", normal_style))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Imagem do índice
            elements.append(Image(str(fig_indice), width=6*inch, height=4*inch))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Histograma
            elements.append(Paragraph("2.1. Distribuição de Valores do Índice", heading2_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Image(str(fig_histograma), width=6*inch, height=3*inch))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Estatísticas do índice
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
            
            # Seção 3: Classificação das Células
            elements.append(Paragraph("3. Classificação das Células", heading1_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("As células da grade foram classificadas com base no valor médio do índice VARI. A classificação é feita em percentis, onde as células são ordenadas do maior para o menor valor médio.", normal_style))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Imagem da grade
            elements.append(Image(str(fig_grade), width=6*inch, height=4*inch))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Gráfico de categorias
            elements.append(Paragraph("3.1. Distribuição de Categorias", heading2_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Image(str(fig_categorias), width=6*inch, height=3*inch))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Estatísticas das categorias
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
            
            # Seção 4: Conclusões
            elements.append(Paragraph("4. Conclusões", heading1_style))
            elements.append(Spacer(1, 0.1 * inch))
            
            # Gerar texto de conclusão com base nas métricas
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
            
            # Gerar PDF
            doc.build(elements)
        
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
    try:
        with rasterio.open(caminho_ortomosaico) as src:
            # Ler as bandas RGB
            red = src.read(1)
            green = src.read(2)
            blue = src.read(3)
            
            # Normalizar valores para visualização
            def normalize(band):
                min_val = np.percentile(band, 2)
                max_val = np.percentile(band, 98)
                return np.clip((band - min_val) / (max_val - min_val), 0, 1)
            
            red_norm = normalize(red)
            green_norm = normalize(green)
            blue_norm = normalize(blue)
            
            # Criar imagem RGB
            rgb = np.dstack((red_norm, green_norm, blue_norm))
            
            # Plotar
            plt.figure(figsize=(10, 8))
            plt.imshow(rgb)
            plt.title("Ortomosaico Recortado")
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
            plt.close()
    
    except Exception as e:
        logger.error(f"Erro ao gerar visualização do ortomosaico: {str(e)}")
        # Criar uma imagem de erro
        plt.figure(figsize=(10, 8))
        plt.text(0.5, 0.5, "Erro ao gerar visualização do ortomosaico", 
                 horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()

def gerar_visualizacao_indice(caminho_indice, caminho_saida):
    """
    Gera uma visualização do índice de vegetação.
    
    Args:
        caminho_indice (Path): Caminho para o arquivo do índice
        caminho_saida (Path): Caminho para salvar a visualização
    """
    try:
        with rasterio.open(caminho_indice) as src:
            # Ler o índice
            indice = src.read(1)
            
            # Criar colormap personalizado para VARI
            cmap = plt.cm.RdYlGn
            
            # Plotar
            plt.figure(figsize=(10, 8))
            im = plt.imshow(indice, cmap=cmap, vmin=-0.5, vmax=0.5)
            plt.colorbar(im, label="Valor do Índice VARI")
            plt.title("Índice de Vegetação VARI")
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
            plt.close()
    
    except Exception as e:
        logger.error(f"Erro ao gerar visualização do índice: {str(e)}")
        # Criar uma imagem de erro
        plt.figure(figsize=(10, 8))
        plt.text(0.5, 0.5, "Erro ao gerar visualização do índice", 
                 horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()

def gerar_visualizacao_grade(caminho_grade, caminho_poligono, caminho_saida):
    """
    Gera uma visualização da grade com ranking.
    
    Args:
        caminho_grade (Path): Caminho para o arquivo GeoJSON da grade
        caminho_poligono (Path): Caminho para o arquivo GeoJSON do polígono
        caminho_saida (Path): Caminho para salvar a visualização
    """
    try:
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
        
        # Plotar
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plotar polígono
        poligono.boundary.plot(ax=ax, color='black', linewidth=1.5)
        
        # Plotar grade com cores por categoria
        for categoria, cor in cores_categorias.items():
            if categoria in grade["categoria"].values:
                grade[grade["categoria"] == categoria].plot(
                    ax=ax,
                    color=cor,
                    edgecolor='white',
                    linewidth=0.5,
                    alpha=0.7
                )
        
        # Adicionar legenda
        patches = [Patch(color=cor, label=cat) for cat, cor in cores_categorias.items() 
                  if cat in grade["categoria"].values]
        ax.legend(handles=patches, title="Categorias", loc="lower right")
        
        # Configurar gráfico
        ax.set_title("Classificação das Células")
        ax.set_axis_off()
        plt.tight_layout()
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()
    
    except Exception as e:
        logger.error(f"Erro ao gerar visualização da grade: {str(e)}")
        # Criar uma imagem de erro
        plt.figure(figsize=(10, 8))
        plt.text(0.5, 0.5, "Erro ao gerar visualização da grade", 
                 horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()

def gerar_histograma_indice(caminho_indice, caminho_saida):
    """
    Gera um histograma do índice de vegetação.
    
    Args:
        caminho_indice (Path): Caminho para o arquivo do índice
        caminho_saida (Path): Caminho para salvar o histograma
    """
    try:
        with rasterio.open(caminho_indice) as src:
            # Ler o índice
            indice = src.read(1)
            
            # Ignorar valores nodata
            nodata = src.nodata
            if nodata is not None:
                indice = indice[indice != nodata]
            
            # Limitar valores para melhor visualização
            indice = np.clip(indice, -0.5, 0.5)
            
            # Plotar histograma
            plt.figure(figsize=(10, 6))
            plt.hist(indice.flatten(), bins=50, color='#4CAF50', alpha=0.7)
            plt.title("Distribuição de Valores do Índice VARI")
            plt.xlabel("Valor do Índice")
            plt.ylabel("Frequência")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
            plt.close()
    
    except Exception as e:
        logger.error(f"Erro ao gerar histograma: {str(e)}")
        # Criar uma imagem de erro
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "Erro ao gerar histograma", 
                 horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()

def gerar_grafico_categorias(caminho_grade, caminho_saida):
    """
    Gera um gráfico de barras com a contagem de células por categoria.
    
    Args:
        caminho_grade (Path): Caminho para o arquivo GeoJSON da grade
        caminho_saida (Path): Caminho para salvar o gráfico
    """
    try:
        # Carregar a grade
        grade = gpd.read_file(caminho_grade)
        
        # Contar células por categoria
        contagem = grade["categoria"].value_counts()
        
        # Ordenar categorias
        ordem_categorias = ["Excelente", "Bom", "Médio", "Regular", "Ruim"]
        contagem = contagem.reindex(ordem_categorias)
        
        # Definir cores
        cores = ["#1a9850", "#91cf60", "#ffffbf", "#fc8d59", "#d73027"]
        cores = [c for i, c in enumerate(cores) if ordem_categorias[i] in contagem.index]
        
        # Plotar gráfico de barras
        plt.figure(figsize=(10, 6))
        contagem.plot(kind='bar', color=cores)
        plt.title("Distribuição de Células por Categoria")
        plt.xlabel("Categoria")
        plt.ylabel("Número de Células")
        plt.grid(True, axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()
    
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico de categorias: {str(e)}")
        # Criar uma imagem de erro
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "Erro ao gerar gráfico de categorias", 
                 horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()
