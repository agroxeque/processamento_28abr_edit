#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo principal que orquestra o fluxo de processamento de ortomosaicos.

Este módulo coordena a execução dos diferentes componentes do sistema,
gerenciando o fluxo de trabalho desde o recebimento dos arquivos de entrada
até a geração dos produtos finais.
"""

import os
import sys
import time
import logging
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Importação dos módulos do sistema
import sb_connect
import recorte_ortomosaico
import iv_gen
import ranking_gen
import relatorio_gen

# Configuração de logging
def setup_logging():
    """Configura o sistema de logs."""
    log_dir = Path("~/processamento_ortomosaicos/logs").expanduser()
    log_file = log_dir / f"processamento_{time.strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def criar_diretorio_temporario(id_projeto):
    """Cria um diretório temporário para o projeto."""
    tmp_dir = Path("~/processamento_ortomosaicos/tmp").expanduser() / id_projeto
    tmp_dir.mkdir(exist_ok=True)
    return tmp_dir

def processar_ortomosaico(id_projeto, id_talhao):
    """
    Função principal que coordena o fluxo de processamento.
    
    Args:
        id_projeto (str): Identificador único do projeto
        id_talhao (str): Identificador único do talhão
        
    Returns:
        bool: True se o processamento foi concluído com sucesso, False caso contrário
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Iniciando processamento do projeto {id_projeto}, talhão {id_talhao}")
    
    # Criar diretório temporário
    tmp_dir = criar_diretorio_temporario(id_projeto)
    logger.info(f"Diretório temporário criado: {tmp_dir}")
    
    try:
        # Conectar ao Supabase e baixar arquivos de entrada
        logger.info("Conectando ao Supabase e baixando arquivos de entrada")
        supabase = sb_connect.conectar()
        
        # Caminhos dos arquivos de entrada no bucket
        ortomosaico_path = f"Ortomosaicos/{id_projeto}/ortomosaico.tif"
        poligono_path = f"talhoes/{id_talhao}/poligono.geojson"
        grade_path = f"talhoes/{id_talhao}/grade_entrada.geojson"
        
        # Baixar arquivos
        ortomosaico_local = tmp_dir / "ortomosaico.tif"
        poligono_local = tmp_dir / "poligono.geojson"
        grade_local = tmp_dir / "grade_entrada.geojson"
        
        sb_connect.baixar_arquivo(supabase, ortomosaico_path, ortomosaico_local)
        sb_connect.baixar_arquivo(supabase, poligono_path, poligono_local)
        sb_connect.baixar_arquivo(supabase, grade_path, grade_local)
        
        # Recortar ortomosaico
        logger.info("Recortando ortomosaico")
        ortomosaico_recortado = tmp_dir / "ortomosaico_recortado.tif"
        recorte_ortomosaico.recortar(ortomosaico_local, poligono_local, ortomosaico_recortado)
        
        # Gerar índice de vegetação
        logger.info("Calculando índice de vegetação VARI")
        vari_path = tmp_dir / "vari.tif"
        iv_gen.calcular_vari(ortomosaico_recortado, vari_path)
        
        # Gerar ranking
        logger.info("Gerando ranking das células")
        grade_saida_path = tmp_dir / "grade_saida.geojson"
        ranking_gen.gerar_ranking(vari_path, grade_local, grade_saida_path)
        
        # Gerar relatório
        logger.info("Gerando relatório")
        relatorio_path = tmp_dir / "relatorio.pdf"
        relatorio_gen.gerar_relatorio(
            ortomosaico_recortado, 
            vari_path, 
            grade_saida_path, 
            poligono_local,
            relatorio_path
        )
        
        # Enviar arquivos de saída para o Supabase
        logger.info("Enviando arquivos de saída para o Supabase")
        sb_connect.enviar_arquivo(supabase, ortomosaico_recortado, f"produtos_finais/{id_projeto}/ortomosaico_recortado.tif")
        sb_connect.enviar_arquivo(supabase, vari_path, f"produtos_finais/{id_projeto}/vari.tif")
        sb_connect.enviar_arquivo(supabase, grade_saida_path, f"produtos_finais/{id_projeto}/grade_saida.geojson")
        sb_connect.enviar_arquivo(supabase, relatorio_path, f"produtos_finais/{id_projeto}/relatorio.pdf")
        
        # Notificar conclusão via webhook
        logger.info("Notificando conclusão via webhook")
        from api import enviar_webhook
        enviar_webhook(id_projeto, id_talhao, "concluido")
        
        logger.info(f"Processamento do projeto {id_projeto} concluído com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro no processamento: {str(e)}", exc_info=True)
        # Notificar erro via webhook
        from api import enviar_webhook
        enviar_webhook(id_projeto, id_talhao, "erro", mensagem=str(e))
        return False
    
    finally:
        # Limpar arquivos temporários se necessário
        # Comentado para permitir debug se necessário
        # import shutil
        # shutil.rmtree(tmp_dir)
        pass

if __name__ == "__main__":
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Configurar logging
    logger = setup_logging()
    
    # Verificar argumentos da linha de comando
    if len(sys.argv) < 3:
        logger.error("Uso: python main.py <id_projeto> <id_talhao>")
        sys.exit(1)
    
    id_projeto = sys.argv[1]
    id_talhao = sys.argv[2]
    
    # Executar processamento
    sucesso = processar_ortomosaico(id_projeto, id_talhao)
    
    # Sair com código apropriado
    sys.exit(0 if sucesso else 1)
