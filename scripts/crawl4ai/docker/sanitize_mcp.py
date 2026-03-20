"""
sanitize_mcp.py - Monkey-patch para sanitizar metadados MCP do Crawl4AI.

Problema: O backend do GitHub Copilot (modelos claude-sonnet-4.5/4.6) rejeita
requests contendo tools MCP com:
  - description vazia ("")
  - $ref / $defs no JSON Schema dos parametros

Este modulo e importado automaticamente via sitecustomize.py ANTES do
server.py iniciar. Ele patcha:
  1. inspect.getdoc() -> preenche descriptions vazias de tools @mcp_tool
  2. Pydantic model_json_schema() -> resolve $ref/$defs inline

Ref: https://github.com/anomalyco/opencode/issues/14488
"""

from __future__ import annotations

import copy
import logging

logger = logging.getLogger("sanitize_mcp")

# ---------------------------------------------------------------------------
# Descriptions default para tools sem docstring
# ---------------------------------------------------------------------------

DEFAULT_DESCRIPTIONS: dict[str, str] = {
    "md": (
        "Fetches content from a specified URL, converts to markdown. "
        "Supports filtering strategies: fit, raw, bm25, or llm."
    ),
}

# ---------------------------------------------------------------------------
# 1. Resolver $ref/$defs inline
# ---------------------------------------------------------------------------


def resolve_refs(schema: dict) -> dict:
    """
    Resolve todas as ocorrencias de $ref apontando para #/$defs/...
    substituindo inline pela definicao real. Remove $defs ao final.
    Fallback: se a ref nao for encontrada, remove o $ref e mantém o resto.
    """
    schema = copy.deepcopy(schema)
    defs = schema.pop("$defs", None)
    if defs is None:
        return schema

    def _resolve(node: dict, depth: int = 0) -> dict:
        if depth > 20:
            return {}
        if "$ref" in node:
            ref_path = node["$ref"]
            parts = ref_path.lstrip("#/").split("/")
            if len(parts) == 2 and parts[0] == "$defs" and parts[1] in defs:
                resolved = copy.deepcopy(defs[parts[1]])
                # Preserva campos irmaos do $ref (ex: default, description)
                merged = {k: v for k, v in node.items() if k != "$ref"}
                merged.update(resolved)
                return _resolve(merged, depth + 1)
            else:
                logger.warning("$ref nao resolvido: %s", ref_path)
                return {k: v for k, v in node.items() if k != "$ref"}
        if "properties" in node:
            node["properties"] = {
                k: _resolve(v, depth + 1)
                for k, v in node["properties"].items()
            }
        if "items" in node and isinstance(node["items"], dict):
            node["items"] = _resolve(node["items"], depth + 1)
        for combo_key in ("anyOf", "oneOf", "allOf"):
            if combo_key in node:
                node[combo_key] = [
                    _resolve(item, depth + 1) if isinstance(item, dict) else item
                    for item in node[combo_key]
                ]
        return node

    return _resolve(schema)


# ---------------------------------------------------------------------------
# 2. Limpar campos problematicos do schema
# ---------------------------------------------------------------------------


def clean_schema(schema: dict) -> dict:
    """Remove title de nivel raiz e de properties (nao padrao MCP)."""
    schema = copy.deepcopy(schema)
    schema.pop("title", None)
    schema.pop("description", None)  # description do model, nao da tool
    for prop in schema.get("properties", {}).values():
        if isinstance(prop, dict):
            prop.pop("title", None)
    return schema


# ---------------------------------------------------------------------------
# 3. Patch: inspect.getdoc
# ---------------------------------------------------------------------------


def _patch_getdoc():
    """
    Patcha inspect.getdoc para retornar descriptions default quando a
    funcao decorada com @mcp_tool nao tem docstring.
    """
    import inspect

    original_getdoc = inspect.getdoc

    def patched_getdoc(obj):
        doc = original_getdoc(obj)
        if doc:
            return doc
        name = getattr(obj, "__mcp_name__", None)
        if name and name in DEFAULT_DESCRIPTIONS:
            return DEFAULT_DESCRIPTIONS[name]
        if name:
            return f"MCP tool: {name}"
        return doc

    inspect.getdoc = patched_getdoc
    logger.info("Patched inspect.getdoc")


# ---------------------------------------------------------------------------
# 4. Patch: Pydantic model_json_schema
# ---------------------------------------------------------------------------


def _patch_pydantic_schemas():
    """
    Patcha model_json_schema das classes Pydantic usadas como input
    dos endpoints MCP para resolver $ref e limpar schemas.
    """
    try:
        import sys
        # schemas pode nao estar importado ainda; vamos registrar um
        # import hook ou patchear depois. A forma mais segura e patchear
        # via __init_subclass__ ou no BaseModel diretamente.
        from pydantic import BaseModel

        original_method = BaseModel.model_json_schema.__func__

        @classmethod
        def patched_json_schema(cls, *args, **kwargs):
            schema = original_method(cls, *args, **kwargs)
            if "$defs" in schema or "$ref" in schema:
                schema = resolve_refs(schema)
            schema = clean_schema(schema)
            return schema

        BaseModel.model_json_schema = patched_json_schema
        logger.info("Patched BaseModel.model_json_schema")
    except Exception as e:
        logger.error("Falha ao patchear Pydantic: %s", e)


# ---------------------------------------------------------------------------
# 5. Aplicar todos os patches
# ---------------------------------------------------------------------------


def apply():
    """Aplica todos os monkey-patches. Chamado via sitecustomize.py."""
    _patch_getdoc()
    _patch_pydantic_schemas()
    logger.info("Sanitizacao MCP ativa")


apply()
