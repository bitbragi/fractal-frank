# Frank MCP

**A general-purpose OP_CAT + sCrypt AI instructor for building covenants and programmable digital assets on Bitcoin forks and OP_CAT-enabled chains.**

Frank is an [MCP](https://modelcontextprotocol.io) server you wire into Claude (or any other MCP-capable client). Once connected, your AI can scaffold sCrypt-TS projects, generate covenant templates, build CAT-721 NFT collections, and talk JSON-RPC to any Bitcoin-Core-compatible node — Fractal Bitcoin, Bitamp, Namecoin/AuxPoW chains, your own regtest, or any future fork that re-enables `OP_CAT`.

Frank is **chain-agnostic by design**. It ships the patterns; you pick the chain.

## Quick Start

All you need is a **free** UniSat Fractal API key — no node required. Most read
tools (blockchain info, transactions, UTXOs, address balances) run on the free key.

```bash
# 1. Clone
git clone https://github.com/bitbragi/fractal-frank.git
cd fractal-frank

# 2. Virtualenv + dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# 4. Get a free Fractal key at https://developer.unisat.io and paste it into .env:
#    UNISAT_FRACTAL_API_KEY=...

# 5. Run (stdio MCP server)
python frank_mcp.py
```

### Add to an MCP client

**Claude Code (one-liner):**

```bash
claude mcp add fractal-frank -- ~/fractal-frank/venv/bin/python ~/fractal-frank/frank_mcp.py
```

**Any MCP client (JSON config):** the key is supplied via the `.env` file in the
project directory (loaded automatically), so no secrets go in the client config:

```json
{
  "mcpServers": {
    "fractal-frank": {
      "command": "/home/you/fractal-frank/venv/bin/python",
      "args": ["/home/you/fractal-frank/frank_mcp.py"]
    }
  }
}
```

Prefer to pass config inline instead of `.env`? Add an `env` block:

```json
"env": { "UNISAT_FRACTAL_API_KEY": "your_key", "FRACTAL_NETWORK": "mainnet" }
```

## What Frank Does

| Category | Tools | Backend |
|----------|-------|---------|
| **Fractal data (read)** | Blockchain info, transactions, UTXOs, address balances, fee rates, broadcast | UniSat free key |
| **Assets (read)** | Inscriptions (by id / by address), BRC-20 (info / holders / address balances), Runes (info / holders / address balances) | UniSat free key |
| **Inscribe orders** | Create / get / list inscribe orders — returns **payment instructions only**, never handles keys or funds | UniSat free key |
| **Offline tx tools** | Decode raw transaction, decode script, validate address — pure local compute via `embit` | local |
| **Fractal node (power-user)** | Mempool, network/mining info, block-by-hash, raw-tx build, testmempoolaccept | `FRACTAL_NODE_RPC_URL` |
| **sCrypt-TS** | Project scaffolding, compilation, testing, advanced contract templates | local |
| **CAT-721 / Covenants** | NFT collection + covenant scaffolding (state machines, vaults, swaps, token issuance, crowdfunds, inscription wrappers) | local |
| **Self-Learning** | Persistent memory, improvement proposals | local |

> **CAT-20 / CAT-721 reads:** Frank can *scaffold* CAT covenants, but UniSat does
> not index CAT tokens/collections on Fractal (no public endpoint), so there are
> no CAT read tools. Inscriptions, BRC-20, and Runes are fully covered.
>
> **Inscribe orders never touch keys.** `fractal_create_inscribe_order` returns an
> order id plus a pay-to address and amount; you fund it from your own wallet. The
> order lapses if unfunded. Frank never pays, signs, or holds a private key.

## Configuration

Create `.env` in the project root:

```env
# Network selector: "mainnet" (default) or "testnet".
# Picks the UniSat OpenAPI base URL automatically — no host to set by hand.
FRACTAL_NETWORK=mainnet

# UniSat OpenAPI key (free dev key from the UniSat Developer Center).
# A public API key — NOT a private key or seed. Frank never handles those.
UNISAT_FRACTAL_API_KEY=your_unisat_fractal_api_key_here

# Optional direct JSON-RPC path to a Fractal Bitcoin Core node, for the advanced
# getblockchaininfo-style tools. Any Bitcoin Core-compatible node works; include
# basic-auth in the URL if needed. Leave blank if you don't run a node.
FRACTAL_NODE_RPC_URL=http://user:pass@localhost:8332
```

`FRACTAL_NETWORK` resolves to `https://open-api-fractal.unisat.io` (mainnet) or
`https://open-api-fractal-testnet.unisat.io` (testnet). The optional
`FRACTAL_NODE_RPC_URL` is the only place a node endpoint is configured.

## Archive

The original Scribe-Protocol-era spec Frank used to ship around lives at [`archive/SCRIBE_COVENANT_EDITION_SPEC.md`](archive/SCRIBE_COVENANT_EDITION_SPEC.md). It's superseded by the current [Bitamp Covenant Edition spec](https://github.com/bitbragi/bitamp-testnet/blob/main/docs/BITAMP_COVENANT_EDITION_SPEC.md). See [`archive/README.md`](archive/README.md) for the lineage.

## Development

See [DEVELOPMENT.md](./DEVELOPMENT.md) for the roadmap.

## License

MIT
