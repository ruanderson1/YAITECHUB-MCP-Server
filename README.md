# inventory-mcp

Servidor MCP de demonstração para consultas de inventário, desenvolvido em Python com FastMCP. O projeto apoia o estudo dos principais conceitos do Model Context Protocol (MCP), com separação entre transporte, interface MCP, regras de negócio, validação e dados.

O escopo atual é intencionalmente somente leitura: o servidor permite consultar produtos e quantidades em estoque, sem operações de cadastro, alteração ou exclusão.

## Tecnologias

- Python 3.11+
- FastMCP
- Pydantic
- pytest
- Ruff

## Arquitetura

- `app/server.py`: cria o servidor FastMCP, registra as tools e inicia o transporte `stdio` ou SSE.
- `app/client.py`: cliente demonstrativo que lista e chama as tools por `stdio` ou SSE.
- `app/tools/`: interface MCP; valida entradas, delega ao serviço e transforma erros esperados em respostas estáveis.
- `app/services/`: regras de consulta e carregamento do inventário.
- `app/schemas/`: modelos Pydantic que definem e validam os contratos de produto e estoque.
- `app/data/`: fonte local de dados, atualmente o arquivo `inventory.json`.
- `tests/`: testes automatizados do serviço, das tools e da configuração do servidor.

```text
Client → MCP Server → Tool → InventoryService → inventory.json
```

As tools não acessam o arquivo diretamente. Elas delegam as regras de negócio ao `InventoryService`.

## Tools MCP

### `get_product`

- **Propósito:** consultar os dados completos de um produto pelo nome.
- **Entrada:** `name` (`string` não vazia).
- **Saída em caso de sucesso:** objeto com `name`, `quantity` e `price`.
- **Saída para produto inexistente:** objeto com `error: "product_not_found"` e uma `message` descritiva.
- **Descrição MCP:** `Use this tool to retrieve the complete data of a product by name, including its price and stock quantity.`
- **Classificação:** somente leitura.

```json
{
  "name": "Mouse",
  "quantity": 25,
  "price": 89.9
}
```

### `get_stock`

- **Propósito:** consultar somente a quantidade atual de um produto pelo nome.
- **Entrada:** `name` (`string` não vazia).
- **Saída em caso de sucesso:** objeto com `quantity`.
- **Saída para produto inexistente:** objeto com `error: "product_not_found"` e uma `message` descritiva.
- **Descrição MCP:** `Use this tool to retrieve only the current stock quantity of a product by name.`
- **Classificação:** somente leitura.

```json
{
  "quantity": 25
}
```

## Validação de entrada

As tools exigem que `name` seja uma string com conteúdo. Nomes vazios ou formados apenas por espaços são rejeitados antes da consulta. O serviço aplica `strip()` para remover espaços nas extremidades e `casefold()` para comparar nomes sem diferenciação entre maiúsculas e minúsculas.

O Pydantic valida os registros carregados do JSON e os objetos retornados. Um produto deve ter nome não vazio, quantidade inteira não negativa e preço numérico não negativo. Registros inválidos interrompem o carregamento com erro explícito.

## Tratamento de erros

O `InventoryService` lança `ProductNotFoundError` quando não encontra o produto solicitado. As tools capturam esse erro esperado e retornam um payload previsível:

```json
{
  "error": "product_not_found",
  "message": "Product not found: Monitor"
}
```

Erros de entrada, como nome vazio ou valor que não seja string, não são ocultados: são reportados como erros da chamada da tool.

## Transportes MCP

- **`stdio`:** comunica-se pela entrada e saída padrão. Neste projeto, o cliente inicia o servidor FastMCP como subprocesso, realiza as chamadas e encerra o processo ao finalizar.
- **SSE:** comunica-se por um endpoint HTTP com Server-Sent Events. Servidor e cliente rodam em processos separados; por padrão, o servidor atende em `http://127.0.0.1:8000/sse`.

## Como executar

Os comandos abaixo usam PowerShell e devem ser executados na raiz do projeto.

### Criar e ativar o ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Instalar as dependências

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Executar via `stdio`

O cliente usa `stdio` por padrão e inicia o servidor como subprocesso:

```powershell
.\.venv\Scripts\python.exe -m app.client
```

Para iniciar apenas o servidor diretamente:

```powershell
.\.venv\Scripts\python.exe -m app.server --transport stdio
```

### Executar via SSE

Inicie o servidor em um terminal (`sse` é o transporte padrão do servidor):

```powershell
.\.venv\Scripts\python.exe -m app.server
```

O comando explícito equivalente é `python -m app.server --transport sse`. Em outro terminal, conecte o cliente:

```powershell
.\.venv\Scripts\python.exe -m app.client --transport sse
```

O cliente aceita outro endpoint por meio de `--url`.

### Executar os testes

```powershell
.\.venv\Scripts\pytest.exe
```

### Executar o Ruff

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
```

## Tool Risk Assessment

| Tool | O que acessa | Tipo de operação | Risco | Possível impacto de uso indevido |
| --- | --- | --- | --- | --- |
| `get_product` | Nome, quantidade e preço no inventário local | Leitura | Baixo | Exposição repetida ou não autorizada dos dados disponíveis no arquivo local |
| `get_stock` | Quantidade em estoque do produto consultado | Leitura | Baixo | Enumeração ou consulta excessiva das quantidades disponíveis |

As tools atuais não modificam dados. Operações de escrita foram evitadas intencionalmente para manter reduzidos o escopo e a superfície de risco.

Uma futura tool como `update_stock` teria risco superior e exigiria controles adicionais, incluindo validação rigorosa, autenticação e autorização, auditoria das alterações e tracing das chamadas.

## Testes

A suíte atual valida:

- carregamento, busca, normalização e erros do `InventoryService`;
- retornos das tools e conversão de produto inexistente em erro previsível;
- rejeição de nomes vazios e valores que não sejam strings;
- rejeição de registros de inventário inválidos pelo Pydantic;
- registro das tools no servidor;
- seleção e configuração dos transportes SSE e `stdio`.

Os cenários incluem produtos existentes e inexistentes, espaços nas extremidades, diferenças entre maiúsculas e minúsculas e entradas inválidas. A suíte também possui um teste de integração ponta a ponta via `stdio`: um cliente FastMCP real inicia o servidor como subprocesso, lista as tools e consulta o estoque carregado do JSON local.

## Qualidade de código

O projeto utiliza type hints, separa responsabilidades entre MCP, serviços, schemas e dados, e mantém dependências mínimas. O pytest cobre os comportamentos implementados, enquanto o Ruff verifica lint, imports, compatibilidade com Python 3.11 e formatação.

## Limitações atuais

- Os dados são carregados de um arquivo JSON local.
- Não existe banco de dados.
- Não existe integração com IA ou LLM.
- Não existem tools de escrita.
- Não há autenticação ou autorização.

## Possíveis evoluções

- tracing e logging estruturado;
- suporte a Streamable HTTP;
- persistência em banco de dados;
- autenticação e autorização;
- tools de escrita com safeguards;
- integração futura com LLM.
