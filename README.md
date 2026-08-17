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

O Pydantic valida os registros carregados do JSON e os modelos de saída. Um produto deve ter nome não vazio, quantidade inteira não negativa e preço numérico não negativo. A rejeição de nomes de consulta vazios é feita por `_validate_product_name()`. Registros inválidos interrompem o carregamento com erro explícito.

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

As tools atuais são somente leitura e não podem criar, alterar ou excluir dados. Essa decisão reduz a superfície de risco, mas não elimina possíveis impactos sobre confidencialidade e disponibilidade.

| Tool | Dados acessados | Operação | Risco atual | Possível impacto de uso indevido |
| --- | --- | --- | --- | --- |
| `get_product` | Nome, preço e quantidade | Leitura | Baixo | Exposição ou enumeração de informações do inventário |
| `get_stock` | Quantidade disponível | Leitura | Baixo | Enumeração de estoque e acompanhamento excessivo da disponibilidade |

Chamadas em grande volume ainda podem consumir recursos do servidor. Alterações futuras nas tools ou nos dados retornados devem ser acompanhadas de uma nova avaliação de risco.

### Trust Boundary

Os argumentos recebidos de um cliente MCP são tratados como entrada não confiável.

```text
MCP Client
    ↓
MCP Server
    ↓
Tool
    ↓
InventoryService
    ↓
inventory.json
```

A validação acontece antes que os argumentos sejam utilizados pela camada de serviço. O servidor não assume que os dados enviados pelo cliente são válidos apenas porque chegaram pelo protocolo MCP. Os registros do `inventory.json` também são tratados como entrada externa e validados pelo Pydantic durante o carregamento.

### MCP Tool Annotations

As tools são classificadas semanticamente de acordo com seu comportamento. As duas operações atuais declaram:

```text
readOnlyHint=true
openWorldHint=false
```

`readOnlyHint=true` informa ao cliente MCP que a operação não pretende modificar estado.

`openWorldHint=false` indica que a tool trabalha sobre um domínio fechado e conhecido — neste caso, o inventário local — em vez de consultar sistemas externos ou fontes abertas.

Essas annotations funcionam como **metadados e hints para clientes MCP**, não como mecanismos de segurança. Um cliente não deve confiar nelas como substituto de validação, autorização ou outros controles reais.

### Risco de tools de escrita

Uma futura operação como:

```text
update_stock(name, quantity)
```

teria risco significativamente maior porque modificaria o estado persistente do sistema.

Uma chamada incorreta ou maliciosa poderia alterar o produto errado, registrar valores inválidos ou permitir mudanças não autorizadas. Uma futura tool como `update_stock` exigiria validação rigorosa, autenticação, autorização, auditoria e tracing. Operações destrutivas também exigiriam confirmação ou aprovação quando aplicável.

### Risco por transporte

No `stdio`, o servidor é iniciado localmente como subprocesso do cliente, reduzindo a exposição de rede. No SSE, servidor e cliente são processos separados e a comunicação usa um endpoint HTTP. Uma eventual publicação desse endpoint fora do host local exigiria controles adicionais de acesso e disponibilidade.

## Testes

A suíte atual valida:

- carregamento, busca, normalização e erros do `InventoryService`;
- retornos das tools e conversão de produto inexistente em erro previsível;
- rejeição de nomes vazios e valores que não sejam strings;
- rejeição de registros de inventário inválidos pelo Pydantic;
- registro das tools no servidor;
- seleção e configuração dos transportes SSE e `stdio`;
- integração real via `stdio`, incluindo `list_tools()`, chamada de `get_stock` e leitura das annotations MCP.

Os cenários incluem produtos existentes e inexistentes, espaços nas extremidades, diferenças entre maiúsculas e minúsculas e entradas inválidas. No teste ponta a ponta, um cliente FastMCP real inicia o servidor como subprocesso, valida `readOnlyHint` e `openWorldHint`, consulta o estoque carregado do JSON local e encerra a conexão pelo context manager.

## Qualidade de código

O projeto utiliza type hints, separa responsabilidades entre MCP, serviços, schemas e dados, e mantém dependências mínimas. O pytest cobre os comportamentos implementados, enquanto o Ruff verifica lint, imports, compatibilidade com Python 3.11 e formatação.

## Limitações atuais

- Os dados são carregados de um arquivo JSON local.
- Não existe banco de dados.
- Não existe integração com IA ou LLM.
- Não existem tools de escrita.
- Não há autenticação ou autorização.

## Possíveis evoluções

- tracing e logging estruturado, mantidos fora do escopo atual para preservar o foco didático do projeto;
- suporte a Streamable HTTP;
- persistência em banco de dados;
- autenticação e autorização;
- tools de escrita com safeguards;
- integração futura com LLM.
