# Frank MCP

**Your OP_CAT AI Instructor**

Frank is an MCP server that connects your AI to the Fractal Bitcoin ecosystem. Build covenants, smart contracts, and NFT collections with OP_CAT.

## Quick Start

```bash
# Install dependencies
cd frank-mcp
python -m venv venv
source venv/bin/activate
pip install fastmcp httpx python-dotenv

# Configure
cp .env.example .env
# Edit .env with your Fractal RPC credentials

# Add to Claude Code
claude mcp add frank -- ~/frank-mcp/venv/bin/python ~/frank-mcp/frank_mcp.py

# Restart Claude Code
```

## What Frank Does

| Category | Tools |
|----------|-------|
| **Fractal RPC** | Block height, transactions, mempool, UTXOs, fee estimation |
| **sCrypt-TS** | Project scaffolding, compilation, testing, advanced templates |
| **CAT-721** | NFT collection generation with traits, royalties, reveal mechanics |
| **ScribeMaster** | Covenant templates: vaults, atomic swaps, tokens, crowdfunding |
| **Self-Learning** | Persistent memory, improvement proposals |

## Scribe Protocol

Frank powers the covenant-native [Scribe Protocol](./SCRIBE_COVENANT_EDITION_SPEC.md) for programmable digital rights on Fractal Bitcoin.

## Configuration

Create `.env` in the project root:

```env
FRACTAL_RPC_URL=https://open-api-fractal-testnet.unisat.io
FRACTAL_API_KEY=your_api_key
FRACTAL_RPC_NODE_URL=http://localhost:8332
```

## Development

See [DEVELOPMENT.md](./DEVELOPMENT.md) for the roadmap.

## License

MIT
