#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de API para o sistema de processamento de ortomosaicos.

Este módulo gerencia o recebimento de solicitações via API REST e
envia webhooks para notificar sobre o status do processamento.
"""

import os
import json
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uvicorn

# Importar o módulo principal
from main import processar_ortomosaico

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging global
# Mover para cá garante que o logger seja configurado quando o módulo é importado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str(Path("/root/processamento_ortomosaicos/logs/api.log"))),
        logging.StreamHandler() # Mantém o log no console também
    ]
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="API de Processamento de Ortomosaicos",
    description="API para processamento de ortomosaicos agrícolas",
    version="1.0.0"
)

# Modelos de dados
class ProcessamentoRequest(BaseModel):
    id_projeto: str
    id_talhao: str

class ProcessamentoResponse(BaseModel):
    id_projeto: str
    id_talhao: str
    status: str
    mensagem: str = None

# Função para enviar webhook
def enviar_webhook(id_projeto, id_talhao, status, mensagem=None):
    """
    Envia uma notificação webhook sobre o status do processamento.
    
    Args:
        id_projeto (str): ID do projeto
        id_talhao (str): ID do talhão
        status (str): Status do processamento ('iniciado', 'concluido', 'erro')
        mensagem (str, opcional): Mensagem adicional, especialmente útil para erros
    """
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        logger.warning("URL de webhook não configurada. Notificação não enviada.")
        return
    
    payload = {
        "id_projeto": id_projeto,
        "id_talhao": id_talhao,
        "status": status
    }
    
    if mensagem:
        payload["mensagem"] = mensagem
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"Webhook enviado com sucesso: {status}")
        else:
            logger.error(f"Falha ao enviar webhook: {response.status_code} - {response.text}")
    
    except Exception as e:
        logger.error(f"Erro ao enviar webhook: {str(e)}")

# Função para executar processamento em background
def executar_processamento_background(id_projeto, id_talhao):
    """Executa o processamento em background e envia webhooks."""
    logger.info(f"Iniciando processamento em background para projeto {id_projeto}, talhão {id_talhao}")
    try:
        # Verificar variáveis de ambiente
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        webhook_url = os.getenv("WEBHOOK_URL")
        
        logger.info(f"Configurações: SUPABASE_URL={'configurado' if supabase_url else 'não configurado'}, "
                   f"SUPABASE_KEY={'configurado' if supabase_key else 'não configurado'}, "
                   f"WEBHOOK_URL={'configurado' if webhook_url else 'não configurado'}")
        
        if not all([supabase_url, supabase_key]):
            raise ValueError("Credenciais do Supabase não configuradas")
        
        # Notificar início
        logger.info("Enviando webhook de início")
        enviar_webhook(id_projeto, id_talhao, "iniciado")
        
        # Executar processamento
        logger.info("Iniciando função de processamento")
        sucesso = processar_ortomosaico(id_projeto, id_talhao)
        logger.info(f"Processamento concluído com sucesso: {sucesso}")
        
    except Exception as e:
        logger.error(f"Erro no processamento background: {str(e)}", exc_info=True)
        try:
            enviar_webhook(id_projeto, id_talhao, "erro", mensagem=str(e))
        except Exception as webhook_error:
            logger.error(f"Erro ao enviar webhook de erro: {str(webhook_error)}")
        raise  # Re-lança a exceção para garantir que ela seja registrada pelo FastAPI

# Rotas da API
@app.post("/processar", response_model=ProcessamentoResponse)
async def iniciar_processamento(
    request: ProcessamentoRequest,
    background_tasks: BackgroundTasks
):
    """
    Inicia o processamento de um ortomosaico.
    
    Args:
        request: Objeto com id_projeto e id_talhao
        background_tasks: Objeto para execução em background
        
    Returns:
        Resposta com status inicial
    """
    try:
        # Validar dados de entrada
        if not request.id_projeto or not request.id_talhao:
            raise HTTPException(status_code=400, detail="ID de projeto e talhão são obrigatórios")
        
        # Iniciar processamento em background
        background_tasks.add_task(
            executar_processamento_background,
            request.id_projeto,
            request.id_talhao
        )
        
        return {
            "id_projeto": request.id_projeto,
            "id_talhao": request.id_talhao,
            "status": "iniciado",
            "mensagem": "Processamento iniciado com sucesso"
        }
    
    except Exception as e:
        logger.error(f"Erro ao iniciar processamento: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{id_projeto}")
async def verificar_status(id_projeto: str):
    """
    Verifica o status de processamento de um projeto.
    
    Esta é uma implementação básica que pode ser expandida para
    verificar o status real do processamento em um sistema de filas.
    
    Args:
        id_projeto: ID do projeto
        
    Returns:
        Status do processamento
    """
    # Implementação básica - em um sistema real, verificaria o status em um banco de dados
    # ou sistema de filas
    return {
        "id_projeto": id_projeto,
        "status": "em_processamento",
        "mensagem": "Verificação de status real não implementada nesta versão"
    }

# Ponto de entrada para execução direta
if __name__ == "__main__":
    # Iniciar servidor
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
