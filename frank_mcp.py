#!/usr/bin/env python3
"""
Frank MCP v0.5 — General-purpose OP_CAT + sCrypt AI Instructor

Hi, I'm Frank. I know OP_CAT and sCrypt-TS inside out. I help your AI build
covenants and programmable digital assets on Bitcoin forks and OP_CAT-enabled
chains — Fractal, Bitamp, your own regtest, anything Bitcoin-Core-compatible.

Features:
- Bitcoin-Core-compatible JSON-RPC (works for any fork)
- sCrypt-TS smart contract scaffolding and compilation
- CAT-721 NFT project generation
- General covenant templates (state machine, vault, token, atomic swap, ...)
- Self-improving learning system
"""
from __future__ import annotations

import hashlib
import base64
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from embit import script as _embit_script
from embit.networks import NETWORKS as _EMBIT_NETWORKS
from embit.transaction import Transaction as _EmbitTx

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent
LEARNINGS_PATH = PROJECT_DIR / "learnings.jsonl"
PROPOSALS_PATH = PROJECT_DIR / "proposals.jsonl"
TEMPLATES_DIR = PROJECT_DIR / "templates"

# Fractal network selector — drives the UniSat OpenAPI base URL.
#   mainnet → https://open-api-fractal.unisat.io
#   testnet → https://open-api-fractal-testnet.unisat.io
FRACTAL_NETWORK = os.getenv("FRACTAL_NETWORK", "mainnet").strip().lower()
_UNISAT_FRACTAL_BASES = {
    "mainnet": "https://open-api-fractal.unisat.io",
    "testnet": "https://open-api-fractal-testnet.unisat.io",
}
UNISAT_FRACTAL_API_BASE = _UNISAT_FRACTAL_BASES.get(
    FRACTAL_NETWORK, _UNISAT_FRACTAL_BASES["mainnet"]
)
# UniSat OpenAPI key (free dev key). NEVER a private key / seed.
UNISAT_FRACTAL_API_KEY = os.getenv("UNISAT_FRACTAL_API_KEY", "")
# Optional: a genuine Fractal Bitcoin Core JSON-RPC node endpoint, for the
# node-only tools routed through _fractal_rpc_call() (broadcast, mempool,
# network/mining info, block-by-hash, decode, raw-tx construction).
FRACTAL_NODE_RPC_URL = os.getenv("FRACTAL_NODE_RPC_URL", "")
# Where new users get a free Fractal API key.
UNISAT_DEV_CENTER_URL = "https://developer.unisat.io"
FRANK_VERSION = "0.5"

mcp = FastMCP(
    "fractal-frank",
    instructions="""Hi, I'm Frank — a general-purpose OP_CAT + sCrypt AI instructor.

I help you build covenants and programmable digital assets on Bitcoin forks and
OP_CAT-enabled chains. I am chain-agnostic by design: I ship the patterns; you
pick the chain. Fractal Bitcoin, Bitamp, your own regtest, or any future
Bitcoin-Core-compatible fork — I'll talk to all of them.

Key capabilities:
- Bitcoin-Core-compatible JSON-RPC (blocks, transactions, mempool, UTXOs, fees)
- sCrypt-TS smart contract scaffolding, compilation, and testing
- CAT-721 NFT collection generation with traits and royalties
- General covenant templates (state machine, vault, token, atomic swap,
  inscription wrapper, crowdfund)
- Self-improving memory system for learning and proposals

Use me to build covenant primitives on any OP_CAT-enabled chain.""",
)


def _now() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, entry: dict) -> None:
    """Append a JSON object as a line to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
    """Read all entries from a JSONL file."""
    if not path.exists():
        return []
    entries = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


async def _unisat_get(path: str, params: dict | None = None) -> dict[str, Any]:
    """GET a UniSat Fractal OpenAPI endpoint using the free-key path.

    Single source of UniSat client logic: auth header, base URL (from
    FRACTAL_NETWORK), HTTP handling, and UniSat envelope checking. Returns
    {"ok": True, "data": <payload>} or {"ok": False, "error": <friendly msg>}.
    """
    if not UNISAT_FRACTAL_API_KEY:
        return {"ok": False, "error": (
            "Set UNISAT_FRACTAL_API_KEY in .env — get a free Fractal key at the "
            f"UniSat Developer Center: {UNISAT_DEV_CENTER_URL}"
        )}
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {UNISAT_FRACTAL_API_KEY}",
    }
    url = f"{UNISAT_FRACTAL_API_BASE}{path}"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            body = r.json()
    except httpx.HTTPStatusError as exc:
        sc = exc.response.status_code
        if sc in (401, 403):
            return {"ok": False, "error": (
                f"UniSat rejected the request (HTTP {sc}). Check that "
                f"UNISAT_FRACTAL_API_KEY is a valid Fractal key from "
                f"{UNISAT_DEV_CENTER_URL}."
            )}
        if sc == 429:
            return {"ok": False, "error": (
                "UniSat rate limit hit (HTTP 429) — wait a moment and retry."
            )}
        return {"ok": False, "error": f"UniSat HTTP {sc} for {path}."}
    except httpx.HTTPError as exc:
        return {"ok": False, "error": f"Network error contacting UniSat ({path}): {exc}"}

    # UniSat envelope: {"code": 0, "msg": "ok", "data": ...}; code!=0 is an error.
    if isinstance(body, dict) and body.get("code") not in (0, None):
        return {"ok": False, "error": (
            f"UniSat API error (code {body.get('code')}): {body.get('msg')}"
        )}
    data = body.get("data") if isinstance(body, dict) else body
    return {"ok": True, "data": data}


async def _unisat_post(path: str, payload: dict | None = None) -> dict[str, Any]:
    """POST to a UniSat Fractal OpenAPI endpoint (writes: broadcast, inscribe).

    Mirrors _unisat_get's auth/base/envelope discipline. Returns
    {"ok": True, "data": <payload>} or {"ok": False, "error": <friendly msg>}.
    """
    if not UNISAT_FRACTAL_API_KEY:
        return {"ok": False, "error": (
            "Set UNISAT_FRACTAL_API_KEY in .env — get a free Fractal key at the "
            f"UniSat Developer Center: {UNISAT_DEV_CENTER_URL}"
        )}
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {UNISAT_FRACTAL_API_KEY}",
    }
    url = f"{UNISAT_FRACTAL_API_BASE}{path}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers=headers, json=payload or {})
            r.raise_for_status()
            body = r.json()
    except httpx.HTTPStatusError as exc:
        sc = exc.response.status_code
        if sc in (401, 403):
            return {"ok": False, "error": (
                f"UniSat rejected the request (HTTP {sc}). Your key may lack access "
                f"to this endpoint — check the plan/tier at {UNISAT_DEV_CENTER_URL}."
            )}
        if sc == 429:
            return {"ok": False, "error": (
                "UniSat rate limit hit (HTTP 429) — wait a moment and retry."
            )}
        return {"ok": False, "error": f"UniSat HTTP {sc} for {path}."}
    except httpx.HTTPError as exc:
        return {"ok": False, "error": f"Network error contacting UniSat ({path}): {exc}"}

    if isinstance(body, dict) and body.get("code") not in (0, None):
        return {"ok": False, "error": (
            f"UniSat API error (code {body.get('code')}): {body.get('msg')}"
        )}
    data = body.get("data") if isinstance(body, dict) else body
    return {"ok": True, "data": data}


# ── Offline helpers (no network) ──────────────────────────────────────────────

def _embit_network() -> dict:
    """Pick the embit network table from FRACTAL_NETWORK.

    Fractal mainnet uses Bitcoin-mainnet address encodings (bc / 1 / 3).
    Testnet HRP is treated best-effort (embit 'test' = tb).
    """
    return _EMBIT_NETWORKS["test"] if FRACTAL_NETWORK == "testnet" else _EMBIT_NETWORKS["main"]


# Minimal Bitcoin Script opcode names for offline disassembly.
_OPCODES = {
    0x00: "OP_0", 0x4c: "OP_PUSHDATA1", 0x4d: "OP_PUSHDATA2", 0x4e: "OP_PUSHDATA4",
    0x4f: "OP_1NEGATE", 0x61: "OP_NOP", 0x63: "OP_IF", 0x64: "OP_NOTIF",
    0x67: "OP_ELSE", 0x68: "OP_ENDIF", 0x69: "OP_VERIFY", 0x6a: "OP_RETURN",
    0x6b: "OP_TOALTSTACK", 0x6c: "OP_FROMALTSTACK", 0x76: "OP_DUP",
    0x87: "OP_EQUAL", 0x88: "OP_EQUALVERIFY", 0x69: "OP_VERIFY",
    0xa6: "OP_RIPEMD160", 0xa7: "OP_SHA1", 0xa8: "OP_SHA256",
    0xa9: "OP_HASH160", 0xaa: "OP_HASH256", 0xac: "OP_CHECKSIG",
    0xad: "OP_CHECKSIGVERIFY", 0xae: "OP_CHECKMULTISIG", 0xaf: "OP_CHECKMULTISIGVERIFY",
    0xb1: "OP_CHECKLOCKTIMEVERIFY", 0xb2: "OP_CHECKSEQUENCEVERIFY",
    0xba: "OP_CHECKSIGADD",
}
for _i in range(1, 17):  # OP_1 .. OP_16
    _OPCODES[0x50 + _i] = f"OP_{_i}"


def _disasm_script(raw: bytes) -> str:
    """Disassemble a Bitcoin script to ASM (offline, no node)."""
    out: list[str] = []
    i, n = 0, len(raw)
    while i < n:
        op = raw[i]; i += 1
        if 1 <= op <= 0x4b:  # direct push
            out.append(raw[i:i + op].hex()); i += op
        elif op == 0x4c and i < n:  # PUSHDATA1
            ln = raw[i]; i += 1; out.append(raw[i:i + ln].hex()); i += ln
        elif op == 0x4d and i + 1 < n:  # PUSHDATA2
            ln = int.from_bytes(raw[i:i + 2], "little"); i += 2
            out.append(raw[i:i + ln].hex()); i += ln
        elif op == 0x4e and i + 3 < n:  # PUSHDATA4
            ln = int.from_bytes(raw[i:i + 4], "little"); i += 4
            out.append(raw[i:i + ln].hex()); i += ln
        else:
            out.append(_OPCODES.get(op, f"OP_UNKNOWN(0x{op:02x})"))
    return " ".join(out)


async def _fractal_rpc_call(
    method: str, params: list[Any] | None = None, unisat_hint: str | None = None
) -> dict[str, Any]:
    """Make a JSON-RPC call to a Fractal Bitcoin Core node (FRACTAL_NODE_RPC_URL)."""
    if not FRACTAL_NODE_RPC_URL:
        msg = (
            "This tool needs a Fractal Bitcoin Core node. Set FRACTAL_NODE_RPC_URL "
            "in .env (optional, power-user). Most read-only queries (blockchain "
            "info, transactions, UTXOs, address balances) work with just the free "
            "UniSat key, no node required."
        )
        if unisat_hint:
            msg += f" Tip: {unisat_hint}"
        return {"error": msg}

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or [],
    }
    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(FRACTAL_NODE_RPC_URL, json=payload, headers=headers)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as exc:
        msg = (
            f"Could not reach the Fractal node set in FRACTAL_NODE_RPC_URL "
            f"({exc.__class__.__name__}). Check the node is running and the URL/auth "
            f"are correct."
        )
        if unisat_hint:
            msg += f" Or skip the node entirely: {unisat_hint}"
        return {"error": msg}


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH & IDENTITY
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def ping() -> str:
    """Health check. Returns pong + UTC timestamp + Frank version."""
    return f"pong @ {_now()} (fractal-frank v{FRANK_VERSION})"


@mcp.tool()
def frank_info() -> str:
    """Get information about Frank MCP and its capabilities."""
    return json.dumps({
        "name": "Frank MCP",
        "version": FRANK_VERSION,
        "tagline": "General-purpose OP_CAT + sCrypt AI instructor",
        "description": (
            "Build covenants and programmable digital assets on any "
            "Bitcoin fork or OP_CAT-enabled chain — Fractal, Bitamp, "
            "your own regtest, or whatever ships next."
        ),
        "capabilities": [
            "Bitcoin-Core-compatible JSON-RPC (any fork)",
            "sCrypt-TS smart contract development",
            "CAT-721 NFT scaffolding",
            "General covenant templates (state machine, vault, token, atomic swap, ...)",
            "Self-improving learning system",
        ],
        "networks": ["any Bitcoin-Core-compatible OP_CAT-enabled chain"],
        "project_dir": str(PROJECT_DIR),
        "learnings_count": len(_read_jsonl(LEARNINGS_PATH)),
        "proposals_count": len(_read_jsonl(PROPOSALS_PATH)),
    }, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# SELF-IMPROVING LEARNING SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def log_learning(topic: str, insight: str, source: str = "user", tags: list[str] | None = None) -> str:
    """Persist a learning/insight to learnings.jsonl for future recall.

    Args:
        topic: The topic or category of this learning
        insight: The actual insight or knowledge gained
        source: Where this learning came from (user, experiment, documentation, etc.)
        tags: Optional list of tags for easier filtering
    """
    entry = {
        "ts": _now(),
        "topic": topic,
        "insight": insight,
        "source": source,
        "tags": tags or [],
    }
    _append_jsonl(LEARNINGS_PATH, entry)
    return f"Logged learning on '{topic}' ({len(insight)} chars) with tags: {tags or []}"


@mcp.tool()
def get_learnings(topic_filter: str = "", tag_filter: str = "", limit: int = 50) -> str:
    """Read back logged learnings. Filter by topic or tag substring.

    Args:
        topic_filter: Filter learnings containing this substring in topic
        tag_filter: Filter learnings containing this tag
        limit: Maximum number of learnings to return
    """
    rows = _read_jsonl(LEARNINGS_PATH)
    if not rows:
        return "No learnings logged yet."

    topic_needle = topic_filter.lower().strip()
    tag_needle = tag_filter.lower().strip()

    filtered = []
    for entry in rows:
        if topic_needle and topic_needle not in entry.get("topic", "").lower():
            continue
        if tag_needle:
            tags = [t.lower() for t in entry.get("tags", [])]
            if not any(tag_needle in t for t in tags):
                continue
        filtered.append(entry)

    filtered = filtered[-limit:]
    if not filtered:
        return f"No learnings match topic='{topic_filter}' tag='{tag_filter}'."
    return json.dumps(filtered, indent=2, ensure_ascii=False)


@mcp.tool()
def propose_improvement(
    area: str,
    suggestion: str,
    rationale: str = "",
    patch_file: str = "",
    patch_content: str = "",
    auto_apply: bool = False
) -> str:
    """Capture an idea for improving Frank itself.

    Can optionally include a patch that modifies templates or non-core files.
    Core frank_mcp.py modifications require manual review.

    Args:
        area: Area of improvement (tools, templates, documentation, etc.)
        suggestion: What should be improved
        rationale: Why this improvement matters
        patch_file: Optional file path to patch (relative to project dir)
        patch_content: Optional new content for the file
        auto_apply: If True and patch_file is in templates/, apply automatically
    """
    entry = {
        "ts": _now(),
        "area": area,
        "suggestion": suggestion,
        "rationale": rationale,
        "patch_file": patch_file,
        "has_patch": bool(patch_content),
        "applied": False,
    }

    # Auto-apply patches to templates directory only
    if auto_apply and patch_file and patch_content:
        target = PROJECT_DIR / patch_file
        # Safety: only allow patches to templates/ directory
        if patch_file.startswith("templates/"):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(patch_content, encoding="utf-8")
            entry["applied"] = True
            entry["applied_at"] = _now()

    _append_jsonl(PROPOSALS_PATH, entry)

    status = "Proposal recorded"
    if entry["applied"]:
        status = f"Proposal recorded and patch applied to {patch_file}"
    elif patch_file:
        status = f"Proposal recorded with pending patch for {patch_file}"

    return f"{status} for area '{area}'."


@mcp.tool()
def get_proposals(area_filter: str = "", pending_only: bool = False, limit: int = 20) -> str:
    """Read back improvement proposals.

    Args:
        area_filter: Filter by area substring
        pending_only: Only show proposals with unapplied patches
        limit: Maximum number to return
    """
    rows = _read_jsonl(PROPOSALS_PATH)
    if not rows:
        return "No proposals recorded yet."

    area_needle = area_filter.lower().strip()

    filtered = []
    for entry in rows:
        if area_needle and area_needle not in entry.get("area", "").lower():
            continue
        if pending_only and (not entry.get("has_patch") or entry.get("applied")):
            continue
        filtered.append(entry)

    filtered = filtered[-limit:]
    if not filtered:
        return f"No proposals match area='{area_filter}' pending_only={pending_only}."
    return json.dumps(filtered, indent=2, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════════════
# FRACTAL BITCOIN DATA
#   Read tools default to UniSat OpenAPI (free key, no node). Node-only tools
#   (broadcast, mempool, network/mining, block-by-hash, decode, raw-tx build)
#   require FRACTAL_NODE_RPC_URL.
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def fractal_get_block_height() -> str:
    """Fetch current Fractal blockchain info (height + tip) via UniSat OpenAPI.

    Backend: UniSat (free key). Network selected by FRACTAL_NETWORK (default mainnet).
    """
    res = await _unisat_get("/v1/indexer/blockchain/info")
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_blockchain_info() -> str:
    """Get Fractal blockchain info (chain, height, tip, headers) via UniSat OpenAPI.

    Backend: UniSat (free key). Network selected by FRACTAL_NETWORK (default mainnet).
    Note: returns UniSat's indexer fields (chain/blocks/headers/bestBlockHash/...),
    not the full Bitcoin-Core getblockchaininfo struct (no softfork/size_on_disk).
    """
    res = await _unisat_get("/v1/indexer/blockchain/info")
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_block(blockhash: str, verbosity: int = 1) -> str:
    """Get block data by hash. verbosity: 0=hex, 1=json, 2=json+tx details."""
    result = await _fractal_rpc_call("getblock", [blockhash, verbosity])
    return json.dumps(result, indent=2)


@mcp.tool()
async def fractal_get_block_hash(height: int) -> str:
    """Get block hash at given height."""
    result = await _fractal_rpc_call("getblockhash", [height])
    return json.dumps(result, indent=2)


@mcp.tool()
async def fractal_get_raw_transaction(txid: str, verbose: bool = True) -> str:
    """Get a Fractal transaction via UniSat OpenAPI.

    Backend: UniSat (free key).
    - verbose=True  → UniSat indexer summary (txid, nIn/nOut, in/out satoshi,
      height, confirmations, inscription counts).
    - verbose=False → raw transaction hex.
    Note: the verbose summary is UniSat's indexer view, NOT a full Bitcoin-Core
    vin/vout decode. For a full decode, call this with verbose=False and pass the
    hex to fractal_decode_raw_transaction (or use a node).
    """
    path = f"/v1/indexer/tx/{txid}" if verbose else f"/v1/indexer/rawtx/{txid}"
    res = await _unisat_get(path)
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_decode_raw_transaction(hex_string: str) -> str:
    """Decode a raw transaction hex into vin/vout/version/locktime (offline, local).

    Backend: local (embit) — no node, no network. Fractal shares Bitcoin's tx
    format, so a standard decoder applies. Output mirrors Bitcoin-Core
    decoderawtransaction (txid, version, locktime, vin[], vout[]); vout values are
    shown in both satoshi and FB. Field note: `vsize`/`weight` are not computed
    offline here, and scriptPubKey `type` uses embit's classifier (p2tr/p2wpkh/
    p2pkh/p2sh/p2wsh or "nonstandard").
    """
    try:
        raw = bytes.fromhex(hex_string.strip())
        tx = _EmbitTx.parse(raw)
    except Exception as exc:
        return json.dumps({"error": f"Could not decode transaction hex: {exc}"}, indent=2)

    net = _embit_network()
    vin = []
    for inp in tx.vin:
        wit = []
        try:
            wit = [item.hex() for item in inp.witness.items] if inp.witness else []
        except Exception:
            wit = []
        vin.append({
            "txid": inp.txid[::-1].hex(),
            "vout": inp.vout,
            "scriptSig": {"hex": inp.script_sig.data.hex()},
            "txinwitness": wit,
            "sequence": inp.sequence,
        })
    vout = []
    for n, o in enumerate(tx.vout):
        spk = o.script_pubkey
        try:
            stype = spk.script_type() or "nonstandard"
        except Exception:
            stype = "nonstandard"
        entry: dict[str, Any] = {
            "n": n,
            "value_sat": o.value,
            "value": o.value / 1e8,
            "scriptPubKey": {"hex": spk.data.hex(), "type": stype},
        }
        try:
            entry["scriptPubKey"]["address"] = spk.address(net)
        except Exception:
            pass
        vout.append(entry)

    return json.dumps({
        "txid": tx.txid().hex(),
        "version": tx.version,
        "locktime": tx.locktime,
        "size": len(raw),
        "vin": vin,
        "vout": vout,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_send_raw_transaction(hex_string: str, max_fee_rate: float = 0.10) -> str:
    """Broadcast an already-signed raw transaction via UniSat OpenAPI.

    Backend: UniSat (free key) — POST /v1/indexer/local_pushtx. Frank does NOT
    sign or fund anything; you pass a transaction you signed yourself with your
    own wallet, and this only relays the finished hex.

    Args:
        hex_string: The fully-signed transaction in hex
        max_fee_rate: Ignored on the UniSat path (no client-side fee ceiling);
            kept for signature compatibility. Set fees when you build the tx.

    Returns:
        The broadcast txid on success, or a clean UniSat error.
    """
    res = await _unisat_post("/v1/indexer/local_pushtx", {"txHex": hex_string.strip()})
    if not res["ok"]:
        return res["error"]
    return json.dumps({"txid": res["data"]}, indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_test_mempool_accept(hex_strings: list[str]) -> str:
    """Test if transactions would be accepted to mempool without broadcasting.

    Args:
        hex_strings: List of raw transaction hex strings to test
    """
    result = await _fractal_rpc_call("testmempoolaccept", [hex_strings])
    return json.dumps(result, indent=2)


@mcp.tool()
async def fractal_get_mempool_info() -> str:
    """Get mempool state (size, bytes, usage, fees)."""
    result = await _fractal_rpc_call("getmempoolinfo")
    return json.dumps(result, indent=2)


@mcp.tool()
async def fractal_get_raw_mempool(verbose: bool = False) -> str:
    """Get all transaction IDs in mempool. verbose=True includes fee info."""
    result = await _fractal_rpc_call("getrawmempool", [verbose])
    return json.dumps(result, indent=2)


@mcp.tool()
async def fractal_estimate_smart_fee(conf_target: int = 6, estimate_mode: str = "economical") -> str:
    """Get recommended Fractal fee rates (sat/vB) via UniSat OpenAPI.

    Backend: UniSat (free key) — GET /v1/indexer/fees/recommended. Returns the
    full tier set (fastestFee / halfHourFee / hourFee / economyFee / minimumFee)
    plus a `feerate` chosen from conf_target:
      conf_target<=1 → fastestFee, <=3 → halfHourFee, <=6 → hourFee, else economyFee.

    Note: UniSat reports sat/vB tiers, not Bitcoin-Core's estimatesmartfee
    {feerate (FB/kvB), blocks}. `estimate_mode` is unused (UniSat has no
    economical/conservative split).
    """
    res = await _unisat_get("/v1/indexer/fees/recommended")
    if not res["ok"]:
        return res["error"]
    tiers = res["data"] or {}
    if conf_target <= 1:
        chosen = tiers.get("fastestFee")
    elif conf_target <= 3:
        chosen = tiers.get("halfHourFee")
    elif conf_target <= 6:
        chosen = tiers.get("hourFee")
    else:
        chosen = tiers.get("economyFee")
    return json.dumps({
        "feerate_sat_vb": chosen,
        "conf_target": conf_target,
        "tiers": tiers,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_list_unspent(
    min_conf: int = 1,
    max_conf: int = 9999999,
    addresses: list[str] | None = None,
    max_utxos: int = 1000,
) -> str:
    """List UTXOs for one or more addresses via UniSat OpenAPI.

    Backend: UniSat (free key). Requires `addresses` — UniSat has no wallet
    context, so a wallet-wide listunspent is only possible against a node.

    Args:
        min_conf: Minimum confirmations (computed from the current tip; default 1)
        max_conf: Maximum confirmations
        addresses: One or more Fractal addresses to list UTXOs for (required)
        max_utxos: Safety cap on total UTXOs fetched across all addresses
            (default 1000). UniSat paginates; this walks the cursor until the
            address is exhausted or the cap is hit, then flags `truncated`.

    Each UTXO carries txid/vout/satoshi/address/scriptPk/height/confirmations and
    any inscriptions.
    """
    if not addresses:
        return (
            "fractal_list_unspent needs one or more `addresses`. UniSat has no "
            "wallet context, so a wallet-wide listunspent requires a Fractal node "
            "(set FRACTAL_NODE_RPC_URL)."
        )
    info = await _unisat_get("/v1/indexer/blockchain/info")
    if not info["ok"]:
        return info["error"]
    tip = info["data"]["blocks"]

    PAGE = 100
    utxos: list[dict[str, Any]] = []
    truncated: dict[str, int] = {}
    hit_cap = False
    for addr in addresses:
        cursor = 0
        fetched = 0
        total = 0
        while True:
            if len(utxos) >= max_utxos:
                hit_cap = True
                truncated[addr] = total or fetched
                break
            res = await _unisat_get(
                f"/v1/indexer/address/{addr}/utxo-data",
                params={"cursor": cursor, "size": PAGE},
            )
            if not res["ok"]:
                return res["error"]
            data = res["data"] or {}
            total = data.get("total", 0)
            page = data.get("utxo", [])
            if not page:
                break
            for u in page:
                h = u.get("height") or 0
                conf = (tip - h + 1) if h else 0
                if conf < min_conf or conf > max_conf:
                    continue
                utxos.append({
                    "txid": u.get("txid"),
                    "vout": u.get("vout"),
                    "address": u.get("address"),
                    "satoshi": u.get("satoshi"),
                    "scriptPk": u.get("scriptPk"),
                    "height": h,
                    "confirmations": conf,
                    "inscriptions": u.get("inscriptions", []),
                })
                if len(utxos) >= max_utxos:
                    break
            fetched += len(page)
            cursor += PAGE
            if fetched >= total:
                break

    out: dict[str, Any] = {"count": len(utxos), "utxo": utxos}
    if truncated:
        out["truncated"] = {
            "note": f"hit max_utxos={max_utxos} cap; more UTXOs exist. "
                    f"Raise max_utxos or narrow the confirmation window.",
            "address_totals": truncated,
            "cap_hit": hit_cap,
        }
    return json.dumps(out, indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_tx_out(txid: str, vout: int, include_mempool: bool = True) -> str:
    """Get details about a transaction output (outpoint) via UniSat OpenAPI.

    Backend: UniSat (free key). Returns satoshi, address, scriptPk/scriptType and
    spend flags (isSpent/isSpending/isOpInRBF) for the given txid:vout.

    Args:
        txid: Transaction ID
        vout: Output index
        include_mempool: Ignored — UniSat indexes confirmed outputs; spend status
            is conveyed via the isSpent/isSpending flags in the response.
    """
    res = await _unisat_get(f"/v1/indexer/utxo/{txid}/{vout}")
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_address_info(address: str) -> str:
    """Get a Fractal address summary via UniSat OpenAPI.

    Backend: UniSat (free key). Returns confirmed/pending balance (satoshi), UTXO
    counts, and inscription holdings for the address.
    Note: this is UniSat's indexer summary, NOT Bitcoin-Core getaddressinfo wallet
    metadata (no ismine/labels/derivation — those require a node wallet).
    """
    res = await _unisat_get(f"/v1/indexer/address/{address}/balance")
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_validate_address(address: str) -> str:
    """Validate a Fractal/Bitcoin address (offline, local).

    Backend: local (embit) — checks encoding + checksum + network and returns the
    derived scriptPubKey and type. Network comes from FRACTAL_NETWORK: mainnet is
    validated strictly against the `bc` HRP / mainnet base58 versions; testnet is
    best-effort (HRP not hard-failed). Output mirrors the useful fields of
    Bitcoin-Core validateaddress (isvalid, address, scriptPubKey, type); wallet
    fields (ismine/iswatchonly) are node-only and omitted.
    """
    address = address.strip()
    try:
        spk = _embit_script.address_to_scriptpubkey(address)
    except Exception as exc:
        return json.dumps({"isvalid": False, "address": address,
                           "reason": str(exc)}, indent=2, ensure_ascii=False)
    net = _embit_network()
    try:
        stype = spk.script_type() or "nonstandard"
    except Exception:
        stype = "nonstandard"
    # Network sanity: re-deriving the address from the spk should round-trip.
    network_ok = True
    try:
        network_ok = spk.address(net) == address
    except Exception:
        network_ok = False
    return json.dumps({
        "isvalid": True,
        "address": address,
        "scriptPubKey": spk.data.hex(),
        "type": stype,
        "network": FRACTAL_NETWORK,
        "network_match": network_ok,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_network_info() -> str:
    """Get P2P network state (version, connections, relay fees)."""
    result = await _fractal_rpc_call("getnetworkinfo")
    return json.dumps(result, indent=2)


@mcp.tool()
async def fractal_get_mining_info() -> str:
    """Get mining-related info (difficulty, hashrate, etc)."""
    result = await _fractal_rpc_call("getmininginfo")
    return json.dumps(result, indent=2)


@mcp.tool()
async def fractal_decode_script(hex_script: str) -> str:
    """Decode a hex script into ASM + type + address (offline, local).

    Backend: local (embit + opcode table) — no node. Returns {asm, type, hex,
    address?}. `type` uses embit's classifier (p2tr/p2wpkh/p2pkh/p2sh/p2wsh or
    "nonstandard"); `address` is included when the script is a standard payable
    type for the current FRACTAL_NETWORK. Bitcoin-Core's nested `p2sh`/`segwit`
    wrapper hints are not reproduced offline.
    """
    try:
        raw = bytes.fromhex(hex_script.strip())
    except Exception as exc:
        return json.dumps({"error": f"Invalid script hex: {exc}"}, indent=2)
    spk = _embit_script.Script(raw)
    try:
        stype = spk.script_type() or "nonstandard"
    except Exception:
        stype = "nonstandard"
    out: dict[str, Any] = {
        "asm": _disasm_script(raw),
        "type": stype,
        "hex": raw.hex(),
    }
    try:
        out["address"] = spk.address(_embit_network())
    except Exception:
        pass
    return json.dumps(out, indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_create_raw_transaction(
    inputs: list[dict],
    outputs: dict[str, float],
    locktime: int = 0
) -> str:
    """Create an unsigned raw transaction.

    Args:
        inputs: List of {"txid": "...", "vout": n} objects
        outputs: Dict of {address: amount} pairs
        locktime: Block height or timestamp for locktime (default 0)

    Example:
        inputs=[{"txid": "abc123...", "vout": 0}]
        outputs={"bc1q...": 0.001, "bc1q...": 0.0005}
    """
    result = await _fractal_rpc_call("createrawtransaction", [inputs, outputs, locktime])
    return json.dumps(result, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# FRACTAL ASSETS — INSCRIPTIONS / BRC-20 / RUNES (UniSat OpenAPI, free key)
#   CAT-20 / CAT-721 are NOT indexed by UniSat on Fractal (no endpoint) — Frank
#   can scaffold CAT covenants but cannot read CAT token/collection state here.
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def fractal_get_inscription_info(inscription_id: str) -> str:
    """Get a single inscription's metadata + content via UniSat OpenAPI.

    Backend: UniSat (free key) — GET /v1/indexer/inscription/info/{inscriptionId}.
    Returns owner address, content type/length/body, number, genesis utxo, and any
    brc20 payload. `inscription_id` looks like "<txid>i<index>".
    """
    res = await _unisat_get(f"/v1/indexer/inscription/info/{inscription_id}")
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_address_inscriptions(address: str, cursor: int = 0, size: int = 20) -> str:
    """List inscriptions held by an address via UniSat OpenAPI.

    Backend: UniSat (free key) — GET /v1/indexer/address/{address}/inscription-data.
    Returns total + a page of inscription UTXOs (cursor/size paginate).
    """
    res = await _unisat_get(
        f"/v1/indexer/address/{address}/inscription-data",
        params={"cursor": cursor, "size": size},
    )
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_brc20_info(ticker: str) -> str:
    """Get BRC-20 token info (supply, minted, holders) via UniSat OpenAPI.

    Backend: UniSat (free key) — GET /v1/indexer/brc20/{ticker}/info.
    """
    res = await _unisat_get(f"/v1/indexer/brc20/{ticker}/info")
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_brc20_holders(ticker: str, start: int = 0, limit: int = 20) -> str:
    """List BRC-20 holders (ranked by balance) via UniSat OpenAPI.

    Backend: UniSat (free key) — GET /v1/indexer/brc20/{ticker}/holders.
    """
    res = await _unisat_get(
        f"/v1/indexer/brc20/{ticker}/holders", params={"start": start, "limit": limit}
    )
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_address_brc20(
    address: str, ticker: str | None = None, start: int = 0, limit: int = 20
) -> str:
    """Get an address's BRC-20 balances via UniSat OpenAPI.

    Backend: UniSat (free key).
    - ticker omitted → summary of ALL ticks the address holds
      (GET /v1/indexer/address/{address}/brc20/summary).
    - ticker given → detailed balance for that one tick
      (GET /v1/indexer/address/{address}/brc20/{ticker}/info).
    """
    if ticker:
        res = await _unisat_get(f"/v1/indexer/address/{address}/brc20/{ticker}/info")
    else:
        res = await _unisat_get(
            f"/v1/indexer/address/{address}/brc20/summary",
            params={"start": start, "limit": limit},
        )
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_rune_info(runeid: str) -> str:
    """Get a rune's info (supply, mints, terms, holders) via UniSat OpenAPI.

    Backend: UniSat (free key) — GET /v1/indexer/runes/{runeid}/info.
    `runeid` is the "<block>:<tx>" id (e.g. "1:0").
    """
    res = await _unisat_get(f"/v1/indexer/runes/{runeid}/info")
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_rune_holders(runeid: str, start: int = 0, limit: int = 20) -> str:
    """List holders of a rune via UniSat OpenAPI.

    Backend: UniSat (free key) — GET /v1/indexer/runes/{runeid}/holders.
    """
    res = await _unisat_get(
        f"/v1/indexer/runes/{runeid}/holders", params={"start": start, "limit": limit}
    )
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_address_runes(address: str, start: int = 0, limit: int = 20) -> str:
    """List an address's rune balances via UniSat OpenAPI.

    Backend: UniSat (free key) — GET /v1/indexer/address/{address}/runes/balance-list.
    """
    res = await _unisat_get(
        f"/v1/indexer/address/{address}/runes/balance-list",
        params={"start": start, "limit": limit},
    )
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════════════
# INSCRIBE ORDERS (UniSat OpenAPI) — NO-KEYS: returns PAYMENT INSTRUCTIONS only.
#   Frank never pays, signs, or funds. The user funds the returned pay-to address
#   from their own wallet to execute the order.
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def fractal_create_inscribe_order(
    text: str,
    receive_address: str,
    fee_rate: float,
    output_value: int = 546,
    filename: str = "inscription.txt",
) -> str:
    """Create a UniSat inscribe order for a text payload (returns PAYMENT INSTRUCTIONS).

    Backend: UniSat (free key) — POST /v2/inscribe/order/create. Frank does NOT
    pay, sign, or fund anything: it returns an order id plus a pay-to address and
    amount that YOU fund from your own wallet to execute the inscription. No
    private keys are ever handled.

    Args:
        text: The inscription content (UTF-8 text; encoded to a data URL).
        receive_address: Where the finished inscription is delivered (your address).
        fee_rate: Network fee rate in sat/vB (see fractal_estimate_smart_fee).
        output_value: Sats locked in the inscription output (default 546).
        filename: Logical filename for the payload (default inscription.txt).
    """
    data_url = (
        "data:text/plain;charset=utf-8;base64,"
        + base64.b64encode(text.encode("utf-8")).decode("ascii")
    )
    payload = {
        "receiveAddress": receive_address,
        "feeRate": fee_rate,
        "outputValue": output_value,
        "files": [{"filename": filename, "dataURL": data_url}],
    }
    res = await _unisat_post("/v2/inscribe/order/create", payload)
    if not res["ok"]:
        return res["error"]
    d = res["data"] or {}
    pay_addr = d.get("payAddress")
    amount = d.get("amount")
    return json.dumps({
        "orderId": d.get("orderId"),
        "status": d.get("status"),
        "payAddress": pay_addr,
        "amount_sat": amount,
        "receiveAddress": receive_address,
        "payment_instruction": (
            f"Send {amount} sat (FB) to {pay_addr} from your own wallet to execute "
            f"this inscription. fractal-frank does not pay, sign, or fund this — the "
            f"order stays pending until you fund it, and lapses if you don't."
        ),
        "raw": d,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_inscribe_order(order_id: str) -> str:
    """Get the status of a UniSat inscribe order via UniSat OpenAPI.

    Backend: UniSat (free key) — GET /v2/inscribe/order/{orderId}. Status moves
    pending → inscribing → minted (or closed/refunded). Read-only; no funds move.
    """
    res = await _unisat_get(f"/v2/inscribe/order/{order_id}")
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_list_inscribe_orders(cursor: int = 0, size: int = 20, sort: str = "desc") -> str:
    """List inscribe orders created with this API key via UniSat OpenAPI.

    Backend: UniSat (free key) — GET /v2/inscribe/order/list. Read-only.
    """
    res = await _unisat_get(
        "/v2/inscribe/order/list", params={"cursor": cursor, "size": size, "sort": sort}
    )
    if not res["ok"]:
        return res["error"]
    return json.dumps(res["data"], indent=2, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════════════
# SCRYPT-TS SMART CONTRACT DEVELOPMENT
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def scrypt_create_project(name: str, target_dir: str = "") -> str:
    """Scaffold a minimal sCrypt-TS smart contract project.

    Args:
        name: Project name (will also be the main contract name)
        target_dir: Target directory (default: ~/scrypt-projects)
    """
    base = Path(target_dir).expanduser() if target_dir else (Path.home() / "scrypt-projects")
    project = base / name
    if project.exists():
        return f"Project already exists: {project}"

    (project / "src" / "contracts").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "artifacts").mkdir()

    pkg = {
        "name": name,
        "version": "0.1.0",
        "scripts": {
            "build": "scrypt-cli compile",
            "test": "mocha --require ts-node/register 'tests/**/*.test.ts'",
            "deploy": "ts-node scripts/deploy.ts",
        },
        "devDependencies": {
            "scrypt-ts": "latest",
            "scrypt-cli": "latest",
            "ts-node": "^10",
            "typescript": "^5",
            "mocha": "^10",
            "@types/mocha": "^10",
            "chai": "^4",
            "@types/chai": "^4",
        },
    }
    (project / "package.json").write_text(json.dumps(pkg, indent=2))

    contract_name = name[:1].upper() + name[1:]
    contract_src = f'''import {{ SmartContract, method, prop, assert, PubKey, Sig }} from 'scrypt-ts'

export class {contract_name} extends SmartContract {{
    @prop()
    readonly owner: PubKey

    constructor(owner: PubKey) {{
        super(...arguments)
        this.owner = owner
    }}

    @method()
    public unlock(sig: Sig) {{
        assert(this.checkSig(sig, this.owner), 'signature check failed')
    }}
}}
'''
    (project / "src" / "contracts" / f"{name}.ts").write_text(contract_src)

    test_src = f'''import {{ expect }} from 'chai'
import {{ {contract_name} }} from '../src/contracts/{name}'
import {{ PubKey, bsv, toHex }} from 'scrypt-ts'

describe('{contract_name}', () => {{
    let instance: {contract_name}

    before(async () => {{
        await {contract_name}.loadArtifact()
        const privateKey = bsv.PrivateKey.fromRandom('testnet')
        const publicKey = privateKey.toPublicKey()
        instance = new {contract_name}(PubKey(toHex(publicKey)))
    }})

    it('should compile successfully', () => {{
        expect(instance).to.not.be.undefined
    }})

    it('should have correct owner', () => {{
        expect(instance.owner).to.not.be.empty
    }})
}})
'''
    (project / "tests" / f"{name}.test.ts").write_text(test_src)

    tsconfig = {
        "compilerOptions": {
            "target": "ES2020",
            "module": "commonjs",
            "experimentalDecorators": True,
            "strict": True,
            "esModuleInterop": True,
            "outDir": "dist",
            "resolveJsonModule": True,
            "declaration": True,
        },
        "include": ["src/**/*", "tests/**/*"],
    }
    (project / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))

    return f"Created sCrypt project at {project}"


@mcp.tool()
def scrypt_compile(project_dir: str, contract_file: str = "") -> str:
    """Compile sCrypt contracts in a project directory.

    Args:
        project_dir: Path to the sCrypt project
        contract_file: Specific contract file to compile (optional)
    """
    project = Path(project_dir).expanduser().resolve()
    if not project.exists():
        return f"Project directory not found: {project}"

    if not (project / "package.json").exists():
        return f"Not a valid sCrypt project (no package.json): {project}"

    cmd = ["npx", "scrypt-cli", "compile"]
    if contract_file:
        cmd.extend(["--contract", contract_file])

    try:
        result = subprocess.run(
            cmd, cwd=project, capture_output=True, text=True, timeout=120
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            return f"Compilation failed:\n{output}"
        return f"Compilation successful:\n{output}"
    except subprocess.TimeoutExpired:
        return "Compilation timed out after 120 seconds"
    except FileNotFoundError:
        return "scrypt-cli not found. Run 'npm install' in the project first."


@mcp.tool()
def scrypt_test(project_dir: str, test_pattern: str = "") -> str:
    """Run sCrypt tests in a project directory.

    Args:
        project_dir: Path to the sCrypt project
        test_pattern: Specific test file pattern (optional)
    """
    project = Path(project_dir).expanduser().resolve()
    if not project.exists():
        return f"Project directory not found: {project}"

    cmd = ["npx", "mocha", "--require", "ts-node/register"]
    if test_pattern:
        cmd.append(test_pattern)
    else:
        cmd.append("tests/**/*.test.ts")

    try:
        result = subprocess.run(
            cmd, cwd=project, capture_output=True, text=True, timeout=180
        )
        return f"Test results:\n{result.stdout}{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Tests timed out after 180 seconds"
    except FileNotFoundError:
        return "mocha not found. Run 'npm install' in the project first."


@mcp.tool()
def scrypt_create_advanced_contract(
    project_dir: str,
    contract_name: str,
    contract_type: str = "hashlock",
    params: dict | None = None
) -> str:
    """Create an advanced sCrypt contract from templates.

    Args:
        project_dir: Path to the sCrypt project
        contract_name: Name for the new contract
        contract_type: Template type (hashlock, multisig, oracle, auction, escrow)
        params: Optional parameters for the template
    """
    project = Path(project_dir).expanduser().resolve()
    contracts_dir = project / "src" / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)

    class_name = contract_name[:1].upper() + contract_name[1:]

    templates = {
        "hashlock": _gen_hashlock_contract(class_name),
        "multisig": _gen_multisig_contract(class_name),
        "oracle": _gen_oracle_contract(class_name),
        "auction": _gen_auction_contract(class_name),
        "escrow": _gen_escrow_contract(class_name),
    }

    if contract_type not in templates:
        return f"Unknown contract type: {contract_type}. Available: {', '.join(templates.keys())}"

    contract_file = contracts_dir / f"{contract_name}.ts"
    contract_file.write_text(templates[contract_type])

    return f"Created {contract_type} contract at {contract_file}"


def _gen_hashlock_contract(class_name: str) -> str:
    return f'''import {{ SmartContract, method, prop, assert, ByteString, Sha256, sha256 }} from 'scrypt-ts'

export class {class_name} extends SmartContract {{
    @prop()
    readonly hash: Sha256

    @prop()
    readonly lockTime: bigint

    constructor(hash: Sha256, lockTime: bigint) {{
        super(...arguments)
        this.hash = hash
        this.lockTime = lockTime
    }}

    @method()
    public unlock(preimage: ByteString) {{
        assert(sha256(preimage) == this.hash, 'hash mismatch')
        assert(this.ctx.locktime >= this.lockTime, 'too early')
    }}
}}
'''


def _gen_multisig_contract(class_name: str) -> str:
    return f'''import {{ SmartContract, method, prop, assert, PubKey, Sig, FixedArray }} from 'scrypt-ts'

export class {class_name} extends SmartContract {{
    static readonly N = 3
    static readonly M = 2

    @prop()
    readonly pubKeys: FixedArray<PubKey, typeof {class_name}.N>

    constructor(pubKeys: FixedArray<PubKey, typeof {class_name}.N>) {{
        super(...arguments)
        this.pubKeys = pubKeys
    }}

    @method()
    public unlock(sigs: FixedArray<Sig, typeof {class_name}.M>, signerIndices: FixedArray<bigint, typeof {class_name}.M>) {{
        let validSigs = 0n
        for (let i = 0; i < {class_name}.M; i++) {{
            const idx = Number(signerIndices[i])
            if (this.checkSig(sigs[i], this.pubKeys[idx])) {{
                validSigs++
            }}
        }}
        assert(validSigs >= BigInt({class_name}.M), 'not enough valid signatures')
    }}
}}
'''


def _gen_oracle_contract(class_name: str) -> str:
    return f'''import {{ SmartContract, method, prop, assert, ByteString, PubKey, Sig, Sha256, sha256 }} from 'scrypt-ts'

export class {class_name} extends SmartContract {{
    @prop()
    readonly oraclePubKey: PubKey

    @prop()
    readonly dataHash: Sha256

    constructor(oraclePubKey: PubKey, dataHash: Sha256) {{
        super(...arguments)
        this.oraclePubKey = oraclePubKey
        this.dataHash = dataHash
    }}

    @method()
    public verify(data: ByteString, oracleSig: Sig) {{
        assert(sha256(data) == this.dataHash, 'data hash mismatch')
        assert(this.checkSig(oracleSig, this.oraclePubKey), 'oracle signature invalid')
    }}
}}
'''


def _gen_auction_contract(class_name: str) -> str:
    return f'''import {{ SmartContract, method, prop, assert, PubKey, Sig, hash256 }} from 'scrypt-ts'

export class {class_name} extends SmartContract {{
    @prop(true)
    highestBidder: PubKey

    @prop(true)
    highestBid: bigint

    @prop()
    readonly auctioneer: PubKey

    @prop()
    readonly deadline: bigint

    constructor(auctioneer: PubKey, deadline: bigint) {{
        super(...arguments)
        this.auctioneer = auctioneer
        this.deadline = deadline
        this.highestBidder = auctioneer
        this.highestBid = 0n
    }}

    @method()
    public bid(bidder: PubKey, bidAmount: bigint) {{
        assert(this.ctx.locktime < this.deadline, 'auction ended')
        assert(bidAmount > this.highestBid, 'bid too low')
        this.highestBidder = bidder
        this.highestBid = bidAmount
        assert(this.ctx.hashOutputs == hash256(this.buildStateOutput(this.ctx.utxo.value + bidAmount)))
    }}

    @method()
    public close(sig: Sig) {{
        assert(this.ctx.locktime >= this.deadline, 'auction not ended')
        assert(this.checkSig(sig, this.auctioneer), 'not auctioneer')
    }}
}}
'''


def _gen_escrow_contract(class_name: str) -> str:
    return f'''import {{ SmartContract, method, prop, assert, PubKey, Sig }} from 'scrypt-ts'

export class {class_name} extends SmartContract {{
    @prop()
    readonly buyer: PubKey

    @prop()
    readonly seller: PubKey

    @prop()
    readonly arbiter: PubKey

    constructor(buyer: PubKey, seller: PubKey, arbiter: PubKey) {{
        super(...arguments)
        this.buyer = buyer
        this.seller = seller
        this.arbiter = arbiter
    }}

    @method()
    public release(buyerSig: Sig) {{
        assert(this.checkSig(buyerSig, this.buyer), 'buyer signature invalid')
    }}

    @method()
    public refund(sellerSig: Sig) {{
        assert(this.checkSig(sellerSig, this.seller), 'seller signature invalid')
    }}

    @method()
    public arbitrate(arbiterSig: Sig) {{
        assert(this.checkSig(arbiterSig, this.arbiter), 'arbiter signature invalid')
    }}
}}
'''


# ══════════════════════════════════════════════════════════════════════════════
# CAT-721 NFT SCAFFOLDING
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def cat_scaffold_721(name: str, symbol: str, target_dir: str = "") -> str:
    """Scaffold a CAT-721 NFT collection for Fractal Bitcoin.

    Args:
        name: Collection name
        symbol: Token symbol (e.g., "PUNK")
        target_dir: Target directory (default: ~/cat721-projects)
    """
    base = Path(target_dir).expanduser() if target_dir else (Path.home() / "cat721-projects")
    slug = name.lower().replace(" ", "-")
    project = base / slug

    if project.exists():
        return f"CAT-721 project already exists: {project}"

    (project / "metadata").mkdir(parents=True)
    (project / "assets").mkdir()

    collection = {
        "standard": "CAT-721",
        "name": name,
        "symbol": symbol,
        "network": "fractal-testnet",
        "max_supply": 10000,
        "description": f"{name} CAT-721 collection on Fractal Bitcoin",
        "created_at": _now(),
    }
    (project / "metadata" / "collection.json").write_text(json.dumps(collection, indent=2))

    readme = f"""# {name} ({symbol})

CAT-721 NFT collection for Fractal Bitcoin.

## Structure
- `metadata/collection.json` — Collection metadata
- `assets/` — Media files

## Deploy
```sh
cat-cli deploy --network fractal-testnet ./metadata/collection.json
```
"""
    (project / "README.md").write_text(readme)

    return f"Scaffolded CAT-721 project at {project}"


@mcp.tool()
def cat_scaffold_721_advanced(
    name: str,
    symbol: str,
    max_supply: int = 10000,
    royalty_percent: float = 5.0,
    reveal_type: str = "instant",
    traits: list[str] | None = None,
    target_dir: str = ""
) -> str:
    """Scaffold an advanced CAT-721 NFT collection with royalties and traits.

    Args:
        name: Collection name
        symbol: Token symbol
        max_supply: Maximum number of NFTs
        royalty_percent: Creator royalty percentage (0-15)
        reveal_type: "instant", "delayed", or "progressive"
        traits: Trait categories (default: background, body, accessory, expression)
        target_dir: Target directory
    """
    base = Path(target_dir).expanduser() if target_dir else (Path.home() / "cat721-projects")
    slug = name.lower().replace(" ", "-")
    project = base / slug

    if project.exists():
        return f"CAT-721 project already exists: {project}"

    (project / "metadata" / "tokens").mkdir(parents=True)
    (project / "assets" / "images").mkdir(parents=True)
    (project / "assets" / "layers").mkdir()
    (project / "scripts").mkdir()
    (project / "config").mkdir()

    royalty_percent = max(0, min(15, royalty_percent))
    if not traits:
        traits = ["background", "body", "accessory", "expression"]

    collection = {
        "standard": "CAT-721",
        "version": "1.1",
        "name": name,
        "symbol": symbol,
        "network": "fractal-testnet",
        "max_supply": max_supply,
        "description": f"{name} CAT-721 collection on Fractal Bitcoin",
        "royalties": {
            "percentage": royalty_percent,
            "recipient": "<REPLACE_WITH_YOUR_ADDRESS>",
        },
        "reveal": {"type": reveal_type},
        "traits": {category: [] for category in traits},
        "created_at": _now(),
    }
    (project / "metadata" / "collection.json").write_text(json.dumps(collection, indent=2))

    trait_config = {
        category: {
            "name": category.title(),
            "values": [
                {"name": "Common", "rarity": 60},
                {"name": "Uncommon", "rarity": 25},
                {"name": "Rare", "rarity": 10},
                {"name": "Legendary", "rarity": 5},
            ],
        }
        for category in traits
    }
    (project / "config" / "traits.json").write_text(json.dumps(trait_config, indent=2))

    return f"Scaffolded advanced CAT-721 at {project} ({len(traits)} traits, {royalty_percent}% royalties)"


# ══════════════════════════════════════════════════════════════════════════════
# COVENANT TEMPLATE GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def covenant_scaffold_master(
    name: str,
    covenant_type: str = "state-machine",
    target_dir: str = "",
    params: dict | None = None
) -> str:
    """Generate a stateful OP_CAT covenant project (chain-agnostic).

    Stateful covenants use OP_CAT to enforce spending conditions across
    multiple transactions on any Bitcoin-Core-compatible OP_CAT-enabled
    chain (Fractal, Bitamp, your own regtest, etc.).

    Args:
        name: Project name
        covenant_type: Type of covenant:
            - "state-machine": General state machine
            - "vault": Time-locked vault with recovery
            - "crowdfund": Crowdfunding with refunds
            - "token": Token issuance covenant
            - "inscription": Ordinals-style inscription wrapper
            - "atomic-swap": Cross-chain atomic swap
        target_dir: Target directory (default: ~/op-cat-covenants)
        params: Type-specific parameters
    """
    base = Path(target_dir).expanduser() if target_dir else (Path.home() / "op-cat-covenants")
    project = base / name

    if project.exists():
        return f"Covenant project already exists: {project}"

    (project / "src" / "covenants").mkdir(parents=True)
    (project / "src" / "lib").mkdir()
    (project / "tests").mkdir()
    (project / "scripts").mkdir()

    class_name = "".join(word.capitalize() for word in name.replace("-", "_").split("_"))

    pkg = {
        "name": f"covenant-{name}",
        "version": "0.1.0",
        "description": f"{covenant_type} OP_CAT covenant (chain-agnostic)",
        "scripts": {
            "build": "scrypt-cli compile && tsc",
            "test": "mocha --require ts-node/register 'tests/**/*.test.ts'",
        },
        "devDependencies": {
            "scrypt-ts": "latest",
            "scrypt-cli": "latest",
            "typescript": "^5",
            "ts-node": "^10",
            "mocha": "^10",
            "@types/mocha": "^10",
            "chai": "^4",
        },
    }
    (project / "package.json").write_text(json.dumps(pkg, indent=2))

    tsconfig = {
        "compilerOptions": {
            "target": "ES2020",
            "module": "commonjs",
            "strict": True,
            "esModuleInterop": True,
            "experimentalDecorators": True,
            "outDir": "dist",
        },
        "include": ["src/**/*"],
    }
    (project / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))

    covenant_lib = '''import { SmartContract, prop, method, assert, ByteString, Sha256, sha256 } from 'scrypt-ts'

export abstract class StatefulCovenant extends SmartContract {
    @prop(true)
    stateHash: Sha256

    constructor(initialStateHash: Sha256) {
        super(...arguments)
        this.stateHash = initialStateHash
    }

    @method()
    protected verifyCurrentState(stateData: ByteString): void {
        assert(sha256(stateData) == this.stateHash, 'state hash mismatch')
    }

    @method()
    protected updateState(newStateData: ByteString): void {
        this.stateHash = sha256(newStateData)
    }
}
'''
    (project / "src" / "lib" / "covenant.ts").write_text(covenant_lib)

    generators = {
        "state-machine": _gen_state_machine_covenant,
        "vault": _gen_vault_covenant,
        "crowdfund": _gen_crowdfund_covenant,
        "token": _gen_token_covenant,
        "inscription": _gen_inscription_covenant,
        "atomic-swap": _gen_atomic_swap_covenant,
    }

    if covenant_type not in generators:
        return f"Unknown covenant type: {covenant_type}. Available: {', '.join(generators.keys())}"

    covenant_code = generators[covenant_type](class_name, params or {})
    (project / "src" / "covenants" / f"{name}.ts").write_text(covenant_code)

    index_ts = f'''export * from './covenants/{name}'
export * from './lib/covenant'
'''
    (project / "src" / "index.ts").write_text(index_ts)

    readme = f"""# {name}

A **{covenant_type}** OP_CAT covenant. Chain-agnostic — deploy on any
Bitcoin-Core-compatible OP_CAT-enabled fork (Fractal, Bitamp, regtest).

## Quick Start

```bash
npm install
npm run build
npm test
```

## Powered by Frank MCP

Generated with Frank MCP v{FRANK_VERSION} — general-purpose OP_CAT + sCrypt
AI instructor. https://github.com/bitbragi/fractal-frank
"""
    (project / "README.md").write_text(readme)

    return f"Scaffolded {covenant_type} covenant at {project}"


def _gen_state_machine_covenant(class_name: str, params: dict) -> str:
    return f'''import {{ SmartContract, prop, method, assert, ByteString, Sha256, sha256, hash256, PubKey, Sig }} from 'scrypt-ts'

export class {class_name} extends SmartContract {{
    @prop(true)
    stateHash: Sha256

    @prop()
    readonly owner: PubKey

    constructor(initialStateHash: Sha256, owner: PubKey) {{
        super(...arguments)
        this.stateHash = initialStateHash
        this.owner = owner
    }}

    @method()
    public transition(currentState: ByteString, newState: ByteString, sig: Sig) {{
        assert(sha256(currentState) == this.stateHash, 'invalid current state')
        assert(this.checkSig(sig, this.owner), 'invalid signature')
        this.stateHash = sha256(newState)
        const output = this.buildStateOutput(this.ctx.utxo.value)
        assert(hash256(output) == this.ctx.hashOutputs, 'invalid outputs')
    }}

    @method()
    public finalize(finalState: ByteString, sig: Sig) {{
        assert(sha256(finalState) == this.stateHash, 'invalid state')
        assert(this.checkSig(sig, this.owner), 'invalid signature')
    }}
}}
'''


def _gen_vault_covenant(class_name: str, params: dict) -> str:
    locktime = params.get("locktime_blocks", 144)
    return f'''import {{ SmartContract, prop, method, assert, hash256, PubKey, Sig }} from 'scrypt-ts'

export class {class_name} extends SmartContract {{
    @prop()
    readonly owner: PubKey

    @prop()
    readonly recoveryKey: PubKey

    @prop()
    readonly locktime: bigint

    @prop(true)
    withdrawInitiated: boolean

    @prop(true)
    withdrawBlock: bigint

    constructor(owner: PubKey, recoveryKey: PubKey) {{
        super(...arguments)
        this.owner = owner
        this.recoveryKey = recoveryKey
        this.locktime = {locktime}n
        this.withdrawInitiated = false
        this.withdrawBlock = 0n
    }}

    @method()
    public initiateWithdraw(sig: Sig) {{
        assert(!this.withdrawInitiated, 'withdrawal already initiated')
        assert(this.checkSig(sig, this.owner), 'invalid owner signature')
        this.withdrawInitiated = true
        this.withdrawBlock = this.ctx.locktime + this.locktime
        const output = this.buildStateOutput(this.ctx.utxo.value)
        assert(hash256(output) == this.ctx.hashOutputs, 'invalid outputs')
    }}

    @method()
    public completeWithdraw(sig: Sig) {{
        assert(this.withdrawInitiated, 'withdrawal not initiated')
        assert(this.ctx.locktime >= this.withdrawBlock, 'timelock not expired')
        assert(this.checkSig(sig, this.owner), 'invalid owner signature')
    }}

    @method()
    public recover(sig: Sig) {{
        assert(this.checkSig(sig, this.recoveryKey), 'invalid recovery signature')
    }}
}}
'''


def _gen_crowdfund_covenant(class_name: str, params: dict) -> str:
    goal = params.get("goal_sats", 1000000)
    return f'''import {{ SmartContract, prop, method, assert, hash256, PubKey, Sig }} from 'scrypt-ts'

export class {class_name} extends SmartContract {{
    @prop()
    readonly creator: PubKey

    @prop()
    readonly goal: bigint

    @prop()
    readonly deadline: bigint

    @prop(true)
    totalRaised: bigint

    constructor(creator: PubKey, deadline: bigint) {{
        super(...arguments)
        this.creator = creator
        this.goal = {goal}n
        this.deadline = deadline
        this.totalRaised = 0n
    }}

    @method()
    public contribute(amount: bigint) {{
        assert(this.ctx.locktime < this.deadline, 'crowdfund ended')
        assert(amount > 0n, 'must contribute positive amount')
        this.totalRaised += amount
        const newBalance = this.ctx.utxo.value + amount
        const output = this.buildStateOutput(newBalance)
        assert(hash256(output) == this.ctx.hashOutputs, 'invalid outputs')
    }}

    @method()
    public withdraw(sig: Sig) {{
        assert(this.totalRaised >= this.goal, 'goal not reached')
        assert(this.checkSig(sig, this.creator), 'invalid creator signature')
    }}
}}
'''


def _gen_token_covenant(class_name: str, params: dict) -> str:
    max_supply = params.get("max_supply", 21000000)
    return f'''import {{ SmartContract, prop, method, assert, ByteString, Sha256, sha256, hash256, PubKey, Sig }} from 'scrypt-ts'

export class {class_name} extends SmartContract {{
    @prop()
    readonly issuer: PubKey

    @prop()
    readonly maxSupply: bigint

    @prop(true)
    totalSupply: bigint

    @prop(true)
    balanceRoot: Sha256

    constructor(issuer: PubKey, initialBalanceRoot: Sha256) {{
        super(...arguments)
        this.issuer = issuer
        this.maxSupply = {max_supply}n
        this.totalSupply = 0n
        this.balanceRoot = initialBalanceRoot
    }}

    @method()
    public mint(amount: bigint, sig: Sig) {{
        assert(this.checkSig(sig, this.issuer), 'not issuer')
        assert(this.totalSupply + amount <= this.maxSupply, 'exceeds max supply')
        this.totalSupply += amount
        const output = this.buildStateOutput(this.ctx.utxo.value)
        assert(hash256(output) == this.ctx.hashOutputs, 'invalid outputs')
    }}
}}
'''


def _gen_inscription_covenant(class_name: str, params: dict) -> str:
    return f'''import {{ SmartContract, prop, method, assert, ByteString, Sha256, sha256, PubKey, Sig, len }} from 'scrypt-ts'

export class {class_name} extends SmartContract {{
    @prop()
    readonly owner: PubKey

    @prop()
    readonly contentHash: Sha256

    @prop()
    readonly contentType: ByteString

    constructor(owner: PubKey, contentHash: Sha256, contentType: ByteString) {{
        super(...arguments)
        this.owner = owner
        this.contentHash = contentHash
        this.contentType = contentType
    }}

    @method()
    public transfer(newOwner: PubKey, sig: Sig) {{
        assert(this.checkSig(sig, this.owner), 'not owner')
    }}

    @method()
    public verifyContent(content: ByteString) {{
        assert(sha256(content) == this.contentHash, 'content mismatch')
        assert(len(content) <= 400000n, 'content too large')
    }}
}}
'''


def _gen_atomic_swap_covenant(class_name: str, params: dict) -> str:
    return f'''import {{ SmartContract, prop, method, assert, ByteString, Sha256, sha256, PubKey, Sig }} from 'scrypt-ts'

export class {class_name} extends SmartContract {{
    @prop()
    readonly partyA: PubKey

    @prop()
    readonly partyB: PubKey

    @prop()
    readonly hashLock: Sha256

    @prop()
    readonly timeLock: bigint

    constructor(partyA: PubKey, partyB: PubKey, hashLock: Sha256, timeLock: bigint) {{
        super(...arguments)
        this.partyA = partyA
        this.partyB = partyB
        this.hashLock = hashLock
        this.timeLock = timeLock
    }}

    @method()
    public claim(preimage: ByteString, sig: Sig) {{
        assert(sha256(preimage) == this.hashLock, 'invalid preimage')
        assert(this.checkSig(sig, this.partyB), 'invalid claimant signature')
    }}

    @method()
    public refund(sig: Sig) {{
        assert(this.ctx.locktime >= this.timeLock, 'timelock not expired')
        assert(this.checkSig(sig, this.partyA), 'invalid refund signature')
    }}
}}
'''


# ══════════════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run()
