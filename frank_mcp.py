#!/usr/bin/env python3
"""
Frank MCP v0.4 — Your OP_CAT AI Instructor

Hi, I'm Frank. Your OP_CAT AI Instructor. I know everything about building
on Fractal Bitcoin with OP_CAT. I'm an MCP server your AI connects to.

Features:
- Full Fractal Bitcoin RPC integration
- sCrypt-TS smart contract scaffolding and compilation
- CAT-721 NFT project generation
- ScribeMaster covenant templates
- Self-improving learning system
"""
from __future__ import annotations

import hashlib
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

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent
LEARNINGS_PATH = PROJECT_DIR / "learnings.jsonl"
PROPOSALS_PATH = PROJECT_DIR / "proposals.jsonl"
TEMPLATES_DIR = PROJECT_DIR / "templates"

FRACTAL_RPC_URL = os.getenv(
    "FRACTAL_RPC_URL", "https://open-api-fractal-testnet.unisat.io"
).rstrip("/")
FRACTAL_API_KEY = os.getenv("FRACTAL_API_KEY", "")
FRACTAL_RPC_NODE_URL = os.getenv("FRACTAL_RPC_NODE_URL", "")
FRANK_VERSION = "0.4"

mcp = FastMCP(
    "frank-mcp",
    instructions="""Hi, I'm Frank. Your OP_CAT AI Instructor.

I know everything about building on Fractal Bitcoin with OP_CAT. I'm an MCP server
your AI connects to for covenant development, sCrypt contracts, CAT-721 NFTs,
and the Scribe Protocol.

Key capabilities:
- Fractal Bitcoin RPC (blocks, transactions, mempool, UTXOs)
- sCrypt-TS smart contract scaffolding, compilation, and testing
- CAT-721 NFT collection generation with traits and royalties
- ScribeMaster covenant templates (vaults, atomic swaps, tokens, etc.)
- Self-improving memory system for learning and proposals

Use me to build covenant-native applications on Fractal.""",
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


async def _fractal_rpc_call(method: str, params: list[Any] | None = None) -> dict[str, Any]:
    """Make a JSON-RPC call to Fractal Bitcoin node."""
    if not FRACTAL_RPC_NODE_URL:
        return {"error": "FRACTAL_RPC_NODE_URL not configured in .env"}

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or [],
    }
    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(FRACTAL_RPC_NODE_URL, json=payload, headers=headers)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as exc:
        return {"error": f"RPC error: {exc}"}


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH & IDENTITY
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def ping() -> str:
    """Health check. Returns pong + UTC timestamp + Frank version."""
    return f"pong @ {_now()} (frank-mcp v{FRANK_VERSION})"


@mcp.tool()
def frank_info() -> str:
    """Get information about Frank MCP and its capabilities."""
    return json.dumps({
        "name": "Frank MCP",
        "version": FRANK_VERSION,
        "tagline": "Your OP_CAT AI Instructor",
        "description": "I know everything about building on Fractal Bitcoin with OP_CAT.",
        "capabilities": [
            "Fractal Bitcoin RPC (full node access)",
            "sCrypt-TS smart contract development",
            "CAT-721 NFT scaffolding",
            "ScribeMaster covenant generation",
            "Scribe Protocol support",
            "Self-improving learning system",
        ],
        "networks": ["fractal-mainnet", "fractal-testnet"],
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
# FRACTAL BITCOIN RPC (Full Node Access)
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def fractal_get_block_height() -> str:
    """Fetch current Fractal testnet blockchain info (height + tip) via UniSat OpenAPI."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if FRACTAL_API_KEY:
        headers["Authorization"] = f"Bearer {FRACTAL_API_KEY}"
    url = f"{FRACTAL_RPC_URL}/v1/indexer/blockchain/info"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as exc:
        return f"HTTP error contacting Fractal RPC ({url}): {exc}"
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
async def fractal_get_blockchain_info() -> str:
    """Get comprehensive blockchain info from Fractal node (getblockchaininfo RPC)."""
    result = await _fractal_rpc_call("getblockchaininfo")
    return json.dumps(result, indent=2)


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
    """Get raw transaction data. verbose=True returns decoded JSON."""
    result = await _fractal_rpc_call("getrawtransaction", [txid, verbose])
    return json.dumps(result, indent=2)


@mcp.tool()
async def fractal_decode_raw_transaction(hex_string: str) -> str:
    """Decode a raw transaction hex string without broadcasting."""
    result = await _fractal_rpc_call("decoderawtransaction", [hex_string])
    return json.dumps(result, indent=2)


@mcp.tool()
async def fractal_send_raw_transaction(hex_string: str, max_fee_rate: float = 0.10) -> str:
    """Broadcast a signed raw transaction to the Fractal network.

    Args:
        hex_string: The signed transaction in hex format
        max_fee_rate: Maximum fee rate in BTC/kvB (default 0.10)

    Returns:
        Transaction ID if successful, error otherwise
    """
    result = await _fractal_rpc_call("sendrawtransaction", [hex_string, max_fee_rate])
    return json.dumps(result, indent=2)


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
    """Estimate fee rate for confirmation within conf_target blocks.

    Args:
        conf_target: Target number of blocks for confirmation (1-1008)
        estimate_mode: "economical" or "conservative"
    """
    result = await _fractal_rpc_call("estimatesmartfee", [conf_target, estimate_mode])
    return json.dumps(result, indent=2)


@mcp.tool()
async def fractal_list_unspent(
    min_conf: int = 1,
    max_conf: int = 9999999,
    addresses: list[str] | None = None
) -> str:
    """List unspent transaction outputs (UTXOs).

    Args:
        min_conf: Minimum confirmations (default 1)
        max_conf: Maximum confirmations
        addresses: Filter by specific addresses (optional)
    """
    params: list[Any] = [min_conf, max_conf]
    if addresses:
        params.append(addresses)
    result = await _fractal_rpc_call("listunspent", params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def fractal_get_tx_out(txid: str, vout: int, include_mempool: bool = True) -> str:
    """Get details about an unspent transaction output.

    Args:
        txid: Transaction ID
        vout: Output index
        include_mempool: Whether to include mempool (default True)
    """
    result = await _fractal_rpc_call("gettxout", [txid, vout, include_mempool])
    return json.dumps(result, indent=2)


@mcp.tool()
async def fractal_get_address_info(address: str) -> str:
    """Get information about a Bitcoin address."""
    result = await _fractal_rpc_call("getaddressinfo", [address])
    return json.dumps(result, indent=2)


@mcp.tool()
async def fractal_validate_address(address: str) -> str:
    """Validate a Bitcoin address and return info about it."""
    result = await _fractal_rpc_call("validateaddress", [address])
    return json.dumps(result, indent=2)


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
    """Decode a hex-encoded script to human-readable format."""
    result = await _fractal_rpc_call("decodescript", [hex_script])
    return json.dumps(result, indent=2)


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
# SCRIBEMASTER COVENANT GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def scribe_scaffold_master(
    name: str,
    covenant_type: str = "state-machine",
    target_dir: str = "",
    params: dict | None = None
) -> str:
    """Generate a ScribeMaster covenant project for Fractal Bitcoin.

    ScribeMaster covenants use OP_CAT to create stateful Bitcoin contracts
    that enforce spending conditions across multiple transactions.

    Args:
        name: Project name
        covenant_type: Type of covenant:
            - "state-machine": General state machine
            - "vault": Time-locked vault with recovery
            - "crowdfund": Crowdfunding with refunds
            - "token": Token issuance covenant
            - "inscription": Ordinals-style inscription
            - "atomic-swap": Cross-chain atomic swap
        target_dir: Target directory (default: ~/scribe-covenants)
        params: Type-specific parameters
    """
    base = Path(target_dir).expanduser() if target_dir else (Path.home() / "scribe-covenants")
    project = base / name

    if project.exists():
        return f"ScribeMaster project already exists: {project}"

    (project / "src" / "covenants").mkdir(parents=True)
    (project / "src" / "lib").mkdir()
    (project / "tests").mkdir()
    (project / "scripts").mkdir()

    class_name = "".join(word.capitalize() for word in name.replace("-", "_").split("_"))

    pkg = {
        "name": f"scribe-{name}",
        "version": "0.1.0",
        "description": f"ScribeMaster {covenant_type} covenant for Fractal Bitcoin",
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

A **{covenant_type}** ScribeMaster covenant for Fractal Bitcoin.

## Quick Start

```bash
npm install
npm run build
npm test
```

## Powered by Frank MCP

Generated with Frank MCP v{FRANK_VERSION} — Your OP_CAT AI Instructor.
"""
    (project / "README.md").write_text(readme)

    return f"Scaffolded ScribeMaster {covenant_type} covenant at {project}"


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
