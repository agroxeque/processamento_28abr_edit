#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para conexão com o Supabase.

Este módulo gerencia a conexão com o Supabase para armazenamento e
recuperação de arquivos nos buckets.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import supabase

# Configuração de logging
logger = logging.getLogger(__name__)

def conectar():
    """
    Estabelece conexão com o Supabase.
    
    Returns:
        objeto de cliente Supabase
    
    Raises:
        Exception: Se não for possível conectar ao Supabase
    """
    # Carregar variáveis de ambiente se ainda não foram carregadas
    if not os.getenv("SUPABASE_URL"):
        load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("Credenciais do Supabase não configuradas no arquivo .env")
    
    try:
        client = supabase.create_client(url, key)
        logger.info("Conexão com Supabase estabelecida com sucesso")
        return client
    
    except Exception as e:
        logger.error(f"Erro ao conectar com Supabase: {str(e)}")
        raise

def baixar_arquivo(client, caminho_bucket, caminho_local):
    """
    Baixa um arquivo do bucket do Supabase.
    
    Args:
        client: Cliente Supabase
        caminho_bucket (str): Caminho do arquivo no bucket
        caminho_local (Path): Caminho local onde o arquivo será salvo
        
    Returns:
        Path: Caminho do arquivo baixado
        
    Raises:
        Exception: Se ocorrer um erro ao baixar o arquivo
    """
    try:
        # Extrair nome do bucket e caminho do arquivo
        partes = caminho_bucket.split('/', 1)
        bucket = partes[0]
        caminho_arquivo = partes[1] if len(partes) > 1 else ""
        
        logger.info(f"Baixando arquivo {caminho_arquivo} do bucket {bucket}")
        
        # Garantir que o diretório de destino exista
        caminho_local.parent.mkdir(parents=True, exist_ok=True)
        
        # Baixar o arquivo
        response = client.storage.from_(bucket).download(caminho_arquivo)
        
        # Salvar o arquivo localmente
        with open(caminho_local, 'wb') as f:
            f.write(response)
        
        logger.info(f"Arquivo baixado com sucesso para {caminho_local}")
        return caminho_local
    
    except Exception as e:
        logger.error(f"Erro ao baixar arquivo {caminho_bucket}: {str(e)}")
        raise

def enviar_arquivo(client, caminho_local, caminho_bucket):
    """
    Envia um arquivo para o bucket do Supabase.
    
    Args:
        client: Cliente Supabase
        caminho_local (Path): Caminho local do arquivo
        caminho_bucket (str): Caminho de destino no bucket
        
    Returns:
        str: URL público do arquivo (se disponível)
        
    Raises:
        Exception: Se ocorrer um erro ao enviar o arquivo
    """
    try:
        # Extrair nome do bucket e caminho do arquivo
        partes = caminho_bucket.split('/', 1)
        bucket = partes[0]
        caminho_arquivo = partes[1] if len(partes) > 1 else ""
        
        logger.info(f"Enviando arquivo {caminho_local} para {bucket}/{caminho_arquivo}")
        
        # Verificar se o arquivo existe
        if not Path(caminho_local).exists():
            raise FileNotFoundError(f"Arquivo {caminho_local} não encontrado")
        
        # Ler o arquivo
        with open(caminho_local, 'rb') as f:
            file_data = f.read()
        
        # Enviar o arquivo
        response = client.storage.from_(bucket).upload(
            caminho_arquivo,
            file_data,
            {"content-type": "application/octet-stream", "upsert": True}
        )
        
        logger.info(f"Arquivo enviado com sucesso para {caminho_bucket}")
        
        # Retornar URL público se disponível
        try:
            url = client.storage.from_(bucket).get_public_url(caminho_arquivo)
            return url
        except:
            return None
    
    except Exception as e:
        logger.error(f"Erro ao enviar arquivo {caminho_local} para {caminho_bucket}: {str(e)}")
        raise

def listar_arquivos(client, bucket):
    """
    Lista os arquivos em um bucket.
    
    Args:
        client: Cliente Supabase
        bucket (str): Nome do bucket
        
    Returns:
        list: Lista de arquivos no bucket
    """
    try:
        logger.info(f"Listando arquivos no bucket {bucket}")
        response = client.storage.from_(bucket).list()
        return response
    
    except Exception as e:
        logger.error(f"Erro ao listar arquivos no bucket {bucket}: {str(e)}")
        raise

def excluir_arquivo(client, caminho_bucket):
    """
    Exclui um arquivo do bucket.
    
    Args:
        client: Cliente Supabase
        caminho_bucket (str): Caminho do arquivo no bucket
        
    Returns:
        bool: True se o arquivo foi excluído com sucesso
    """
    try:
        # Extrair nome do bucket e caminho do arquivo
        partes = caminho_bucket.split('/', 1)
        bucket = partes[0]
        caminho_arquivo = partes[1] if len(partes) > 1 else ""
        
        logger.info(f"Excluindo arquivo {caminho_arquivo} do bucket {bucket}")
        
        # Excluir o arquivo
        client.storage.from_(bucket).remove([caminho_arquivo])
        
        logger.info(f"Arquivo {caminho_bucket} excluído com sucesso")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao excluir arquivo {caminho_bucket}: {str(e)}")
        raise
