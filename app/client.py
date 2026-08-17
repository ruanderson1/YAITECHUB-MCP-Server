"""Demonstration client for the Inventory MCP server."""

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import SSETransport, StdioTransport

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVER_PATH = PROJECT_ROOT / "app" / "server.py"
DEFAULT_SSE_URL = "http://127.0.0.1:8000/sse"


@dataclass(frozen=True)
class ToolCallExample:
    """Representa uma chamada de demonstração e seu resultado esperado."""

    tool_name: str
    product_name: str
    expected: str


# Cobre os principais resultados sem transformar o cliente em uma suíte de testes.
EXAMPLE_CALLS = (
    ToolCallExample(
        tool_name="get_product",
        product_name="Mouse",
        expected="produto Mouse, quantidade 25 e preço 89.90",
    ),
    ToolCallExample(
        tool_name="get_stock",
        product_name="Mouse",
        expected="quantidade 25",
    ),
    ToolCallExample(
        tool_name="get_product",
        product_name="Notebook",
        expected="produto Notebook, quantidade 8 e preço 3499.90",
    ),
    ToolCallExample(
        tool_name="get_stock",
        product_name="Teclado",
        expected="quantidade 12",
    ),
    ToolCallExample(
        tool_name="get_product",
        product_name="Produto Inexistente",
        expected=("erro product_not_found informando que o produto não foi encontrado"),
    ),
    ToolCallExample(
        tool_name="get_stock",
        product_name="Shampoo",
        expected=("erro product_not_found informando que o produto não foi encontrado"),
    ),
    ToolCallExample(
        tool_name="get_product",
        product_name="",
        expected="erro de validação: o nome não pode ser vazio",
    ),
    ToolCallExample(
        tool_name="get_stock",
        product_name="   ",
        expected="erro de validação: o nome não pode conter apenas espaços",
    ),
)


def _fastmcp_command() -> str:
    """Localiza o executável FastMCP no ambiente Python atual."""
    executable_name = "fastmcp.exe" if os.name == "nt" else "fastmcp"
    return str(Path(sys.executable).with_name(executable_name))


def _create_transport(mode: str, sse_url: str) -> StdioTransport | SSETransport:
    """Cria o transporte solicitado para a conexão com o servidor."""
    if mode == "sse":
        return SSETransport(sse_url)

    # Em stdio, o ciclo de vida do servidor pertence ao cliente.
    return StdioTransport(
        command=_fastmcp_command(),
        args=[
            "run",
            str(SERVER_PATH),
            "--transport",
            "stdio",
            "--no-banner",
            "--log-level",
            "ERROR",
        ],
        cwd=str(PROJECT_ROOT),
        keep_alive=False,
    )


async def _show_available_tools(client: Client) -> None:
    """Solicita ao servidor e exibe as tools MCP que ele disponibiliza."""
    print("------ Solicitando ao servidor a lista de tools... --------")
    tools = await client.list_tools()

    print("\nTools retornadas pelo servidor:")
    for tool in tools:
        print(f"- {tool.name}: {tool.description or 'Sem descrição.'}")


async def _run_examples(client: Client) -> None:
    """Executa os exemplos e diferencia respostas normais de erros das tools."""
    print("\n EXECUTANDO:")

    for number, example in enumerate(EXAMPLE_CALLS, start=1):
        arguments = {"name": example.product_name}
        print(f"\n{number}. Chamando {example.tool_name} com {arguments}")
        print(f"   Esperado: {example.expected}.")

        # Erros de negócio ficam no resultado; falhas de conexão encerram o cliente.
        result = await client.call_tool(
            example.tool_name,
            arguments,
            raise_on_error=False,
        )

        if result.is_error:
            error_messages = [
                content.text for content in result.content if hasattr(content, "text")
            ]
            print(f"   Resultado: erro retornado: {' '.join(error_messages)}")
        else:
            print(f"   Resultado: {result.data}")


async def run_client(mode: str = "stdio", sse_url: str = DEFAULT_SSE_URL) -> None:
    """Connect to the inventory server and demonstrate its read-only tools."""
    transport = _create_transport(mode, sse_url)

    async with Client(transport) as client:
        await _show_available_tools(client)
        await _run_examples(client)


def main() -> None:
    """Executa o cliente de demonstração com os argumentos da linha de comando."""

    parser = argparse.ArgumentParser(description="Run the inventory MCP client.")
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse"),
        default="stdio",
        help="MCP transport to use (default: stdio).",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_SSE_URL,
        help=f"SSE server URL (default: {DEFAULT_SSE_URL}).",
    )
    args = parser.parse_args()

    try:
        asyncio.run(run_client(args.transport, args.url))
    except Exception as exc:
        print(f"Erro ao conectar ou executar o servidor MCP: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except KeyboardInterrupt:
        print("Execução interrompida pelo usuário.", file=sys.stderr)
        raise SystemExit(130) from None


if __name__ == "__main__":
    main()
