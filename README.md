# Sistema de Processamento de Ortomosaicos

Este sistema realiza o processamento de ortomosaicos de campos agrícolas, gerando índices de vegetação, classificação de células e relatórios de análise.

## Estrutura do Sistema

```
~/processamento_ortomosaicos/
├── assets/                  # Artefatos (logos, etc.)
├── logs/                    # Arquivos de log
├── tmp/                     # Arquivos temporários (organizados por ID de projeto)
├── .env                     # Arquivo de configuração com credenciais
├── main.py                  # Módulo principal que orquestra o fluxo
├── api.py                   # API REST para recebimento de solicitações
├── sb_connect.py            # Conexão com Supabase
├── recorte_ortomosaico.py   # Processamento de recorte
├── iv_gen.py                # Cálculo de índices de vegetação
├── ranking_gen.py           # Classificação e ranking
├── relatorio_gen.py         # Geração de relatórios
└── requirements.txt         # Dependências do sistema
```

## Fluxo de Processamento

1. **Entrada**: O sistema recebe três arquivos de entrada:
   - `ortomosaico.tif`: Imagem aérea georreferenciada do campo agrícola
   - `poligono.geojson`: Delimitação do talhão
   - `grade_entrada.geojson`: Grade de células para análise

2. **Processamento**:
   - Recorte do ortomosaico usando o polígono
   - Cálculo do índice de vegetação VARI
   - Classificação e ranking das células
   - Geração de relatório em PDF

3. **Saída**: O sistema gera quatro arquivos de saída:
   - `ortomosaico_recortado.tif`: Versão recortada do ortomosaico
   - `vari.tif`: Índice de vegetação
   - `grade_saida.geojson`: Grade com ranking
   - `relatorio.pdf`: Relatório com análises

## Instalação

1. Clone o repositório ou copie os arquivos para o diretório `~/processamento_ortomosaicos/`
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Configure o arquivo `.env` com as credenciais necessárias

## Uso

### Via Linha de Comando

```bash
python main.py <id_projeto> <id_talhao>
```

### Via API REST

Inicie o servidor API:
```bash
python api.py
```

Envie uma solicitação POST para iniciar o processamento:
```bash
curl -X POST "http://localhost:8000/processar" \
     -H "Content-Type: application/json" \
     -d '{"id_projeto": "123", "id_talhao": "456"}'
```

## Índice de Vegetação VARI

O índice VARI (Visible Atmospherically Resistant Index) é calculado pela fórmula:

```
VARI = (G - R) / (G + R - B)
```

Onde:
- G: Banda verde
- R: Banda vermelha
- B: Banda azul

Valores mais altos indicam vegetação mais saudável.

## Classificação das Células

As células são classificadas em cinco categorias com base no percentil do valor médio do índice VARI:

- **Excelente**: Percentil >= 80
- **Bom**: Percentil >= 60 e < 80
- **Médio**: Percentil >= 40 e < 60
- **Regular**: Percentil >= 20 e < 40
- **Ruim**: Percentil < 20

## Contribuição

Para contribuir com o projeto, siga as diretrizes de desenvolvimento:

1. Mantenha a estrutura modular
2. Documente todas as funções e módulos
3. Implemente tratamento de erros adequado
4. Adicione logs para facilitar o diagnóstico de problemas
5. Escreva testes para novas funcionalidades

## Licença

Este projeto é proprietário e confidencial.
