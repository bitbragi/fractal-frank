# Frank MCP Development Roadmap

## Phase 1: Foundation (Current)

- [x] Core MCP server with FastMCP
- [x] Health check and identity tools
- [x] Self-improving learning system (log_learning, get_learnings, propose_improvement)
- [x] Basic Fractal RPC integration via UniSat OpenAPI
- [x] Environment configuration (.env support)

## Phase 2: Core Tooling

- [x] Full Fractal Bitcoin RPC
  - [x] Blockchain info, blocks, block hashes
  - [x] Transaction queries and decoding
  - [x] Mempool info and raw mempool
  - [x] UTXO management (listunspent, gettxout)
  - [x] Address validation and info
  - [x] Fee estimation
  - [x] Raw transaction creation and broadcasting
- [x] sCrypt-TS Development
  - [x] Project scaffolding
  - [x] Contract compilation
  - [x] Test runner
  - [x] Advanced contract templates (hashlock, multisig, oracle, auction, escrow)
- [x] CAT-721 NFT Support
  - [x] Basic collection scaffolding
  - [x] Advanced scaffolding with traits and royalties
  - [x] Metadata batch generation

## Phase 3: Scribe Protocol Core

- [x] ScribeMaster Covenant Generator
  - [x] State machine covenants
  - [x] Time-locked vaults
  - [x] Crowdfunding covenants
  - [x] Token issuance covenants
  - [x] Inscription covenants
  - [x] Atomic swap covenants
- [ ] Scribe Covenant Edition
  - [ ] Master covenant template
  - [ ] License issuance hooks
  - [ ] Revenue split covenants
  - [ ] SID generation (canonical CBOR + sha256)
  - [ ] Hard wrap transaction builder
  - [ ] Full sealing flow

## Phase 4: Autonomous Powerhouse

- [x] Enhanced learning system with tags
- [x] Proposal system with patch support
- [ ] Auto-patching for templates directory
- [ ] Template versioning and rollback
- [ ] Learning export/import
- [ ] Cross-session context preservation

## Phase 5: Community & Polish

- [x] Comprehensive documentation
- [x] Landing page (frank.scribe.spot)
- [ ] Example projects
- [ ] Tutorial workflows
- [ ] Community templates repository
- [ ] Plugin system for custom tools

## Architecture

```
frank-mcp/
├── frank_mcp.py          # Main MCP server
├── .env                  # Configuration
├── learnings.jsonl       # Persistent learnings
├── proposals.jsonl       # Improvement proposals
├── templates/            # Patchable templates
├── public/               # Landing page
└── venv/                 # Python environment
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Use `propose_improvement` to suggest changes
4. Submit a pull request

## Tech Stack

- Python 3.11+
- FastMCP
- httpx (async HTTP)
- sCrypt-TS (contract development)
- Fractal Bitcoin (OP_CAT enabled)
