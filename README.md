# Frank MCP

**A general-purpose OP_CAT + sCrypt AI instructor for building covenants and programmable digital assets on Bitcoin forks and OP_CAT-enabled chains.**

Frank is an [MCP](https://modelcontextprotocol.io) server you wire into Claude (or any other MCP-capable client). Once connected, your AI can scaffold sCrypt-TS projects, generate covenant templates, build CAT-721 NFT collections, and talk JSON-RPC to any Bitcoin-Core-compatible node — Fractal Bitcoin, Bitamp, Namecoin/AuxPoW chains, your own regtest, or any future fork that re-enables `OP_CAT`.

Frank is **chain-agnostic by design**. It ships the patterns; you pick the chain.

## Quick Start

```bash
# Install dependencies
cd frank-mcp
python -m venv venv
source venv/bin/activate
pip install fastmcp httpx python-dotenv

# Configure
cp .env.example .env
# Edit .env with your node's RPC URL + (optional) UniSat / OpenAPI key

# Add to Claude Code
claude mcp add frank -- ~/frank-mcp/venv/bin/python ~/frank-mcp/frank_mcp.py

# Restart Claude Code
```

## What Frank Does

| Category | Tools |
|----------|-------|
| **Node RPC** | Block height, transactions, mempool, UTXOs, fee estimation — any Bitcoin-Core-compatible node |
| **sCrypt-TS** | Project scaffolding, compilation, testing, advanced contract templates |
| **CAT-721** | NFT collection generation with traits, royalties, reveal mechanics |
| **Covenant Templates** | State machines, time-locked vaults, atomic swaps, token issuance, crowdfunds, inscription wrappers |
| **Self-Learning** | Persistent memory, improvement proposals |

## Configuration

Create `.env` in the project root:

```env
# Public-API path (any UniSat-style OpenAPI works — Fractal default shown).
FRACTAL_RPC_URL=https://open-api-fractal-testnet.unisat.io
FRACTAL_API_KEY=your_api_key

# Direct JSON-RPC path. Any Bitcoin Core-compatible node — Fractal, Bitamp,
# regtest, etc. — works here. Includes basic-auth in the URL if needed.
FRACTAL_RPC_NODE_URL=http://user:pass@localhost:8332
```

The env-var names start with `FRACTAL_` for backward compatibility with earlier Frank deployments. They are not Fractal-specific — point them at *any* Bitcoin-Core-compatible RPC.

## Companion Projects

Frank is one half of a two-companion setup designed to keep responsibilities clean:

- **Frank (this repo)** — the *generalist*. Knows OP_CAT, sCrypt-TS, and covenant patterns across any Bitcoin fork.
- **[Brad](https://github.com/bitbragi/brad-bitamp-mcp)** — the *specialist*. AI guardian for the [Bitamp](https://github.com/bitbragi/bitamp-testnet) chain in particular: safety scanning (AcoustID + NSFW + hash-only CSAM), PID manifest creation, Bitamp covenant scaffolding, legacy contract migration, and on-chain inscription validation.

If you're building a one-off covenant or teaching yourself OP_CAT, use Frank. If you're publishing audio/video on Bitamp specifically, use Brad. They share patterns but don't overlap responsibilities.

## Archive

The original Scribe-Protocol-era spec Frank used to ship around lives at [`archive/SCRIBE_COVENANT_EDITION_SPEC.md`](archive/SCRIBE_COVENANT_EDITION_SPEC.md). It's superseded by the current [Bitamp Covenant Edition spec](https://github.com/bitbragi/bitamp-testnet/blob/main/docs/BITAMP_COVENANT_EDITION_SPEC.md). See [`archive/README.md`](archive/README.md) for the lineage.

## Development

See [DEVELOPMENT.md](./DEVELOPMENT.md) for the roadmap.

## License

MIT
