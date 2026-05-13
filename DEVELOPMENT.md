# Frank MCP Development Roadmap

Frank is a **general-purpose OP_CAT + sCrypt AI instructor**. The roadmap below tracks the chain-agnostic tooling Frank ships — it deliberately stays out of any one chain's domain-specific protocol (those live in chain-specific companions like [Brad](https://github.com/bitbragi/brad-bitamp-mcp)).

## Phase 1: Foundation (Complete)

- [x] Core MCP server with FastMCP
- [x] Health check and identity tools
- [x] Self-improving learning system (`log_learning`, `get_learnings`, `propose_improvement`)
- [x] UniSat-OpenAPI integration (Fractal-style nodes)
- [x] Environment configuration (`.env` support)

## Phase 2: Core Tooling (Complete)

- [x] Bitcoin-Core-compatible JSON-RPC (works for any fork)
  - [x] Blockchain info, blocks, block hashes
  - [x] Transaction queries and decoding
  - [x] Mempool info and raw mempool
  - [x] UTXO management (`listunspent`, `gettxout`)
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

## Phase 3: General-Purpose Covenant Templates (Complete)

- [x] Covenant scaffolding (`covenant_scaffold_master`)
  - [x] State machine covenants
  - [x] Time-locked vaults
  - [x] Crowdfunding covenants
  - [x] Token issuance covenants
  - [x] Inscription covenants
  - [x] Atomic swap covenants

These templates are the *primitives* every chain-specific covenant suite eventually composes. Chain-specific protocols (rights management, media licensing, NFT marketplaces, etc.) belong in companion MCPs, not in Frank.

## Phase 4: Self-Improvement Engine

- [x] Enhanced learning system with tags
- [x] Proposal system with patch support
- [ ] Auto-patching for templates directory
- [ ] Template versioning and rollback
- [ ] Learning export/import
- [ ] Cross-session context preservation

## Phase 5: Community & Polish

- [x] Comprehensive documentation
- [x] Landing page
- [ ] Example projects (one per template type, chain-agnostic)
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
├── archive/              # Historical / superseded docs
└── venv/                 # Python environment
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Use `propose_improvement` to suggest changes
4. Submit a pull request

Keep contributions **chain-agnostic**. If you're building something that only makes sense on one specific chain, it probably belongs in a companion MCP (see [Brad](https://github.com/bitbragi/brad-bitamp-mcp) for the Bitamp pattern), not in Frank.

## Tech Stack

- Python 3.11+
- [FastMCP](https://github.com/jlowin/fastmcp)
- httpx (async HTTP)
- sCrypt-TS (covenant development)
- Any Bitcoin-Core-compatible OP_CAT-enabled chain
