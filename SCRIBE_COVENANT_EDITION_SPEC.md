# Scribe Protocol — Covenant Edition v1

## Overview

Scribe Protocol enables programmable digital rights on Bitcoin. The Covenant Edition runs natively on Fractal Bitcoin using OP_CAT covenants, providing trustless enforcement of ownership, licensing, and revenue distribution.

## Design Principles

1. **Covenant-Native First**: All core logic runs as Bitcoin covenants on Fractal
2. **Minimal Trust**: No trusted third parties for ownership or licensing
3. **Permanent Record**: Immutable on-chain provenance
4. **Composable**: Masters, licenses, and revenue splits interoperate
5. **OPNet Optional**: Registry integration available but not required

## Core Concepts

### Scribe ID (SID)

The SID uniquely identifies a creative work. It is derived deterministically:

```
SID = sha256(canonical_cbor(manifest))
```

The manifest contains:
- `title`: Work title
- `type`: Content type (MUSIC_TRACK, MUSIC_ALBUM, etc.)
- `creator`: Creator's public key or address
- `created_at`: ISO 8601 timestamp
- `content_hash`: sha256 of the content
- `metadata`: Additional type-specific fields

### Master Covenant

The Master represents ownership of the creative work. It is a stateful covenant that:

1. **Commits to the SID** in its state
2. **Controls ownership transfer** via owner signature
3. **Issues licenses** by creating child covenants
4. **Enforces royalties** on secondary sales

```
Master State:
- sid: Sha256 (immutable)
- owner: PubKey (mutable)
- license_count: bigint (mutable)
- revenue_split_root: Sha256 (mutable)
```

### License Covenants

Licenses grant specific rights derived from a Master:

| License Type | Rights Granted |
|--------------|----------------|
| `MUSIC_STREAM` | Streaming playback |
| `MUSIC_DOWNLOAD` | Digital download |
| `MUSIC_SYNC` | Synchronization (film/TV) |
| `MUSIC_MASTER` | Full master rights transfer |

License covenants:
- Reference the parent Master SID
- Specify granted rights and terms
- May be time-limited or perpetual
- Can enforce usage restrictions on-chain

### Revenue Split Covenant

Distributes payments to multiple parties:

```
RevenueSplit State:
- recipients: Array<{address, share_bps}>
- total_distributed: bigint
```

When funds arrive at the split covenant:
1. Covenant verifies amounts match shares
2. Creates outputs to each recipient
3. Updates total_distributed state

## Transaction Flows

### 1. Sealing (Master Creation)

```
Input:
  - Funding UTXO

Output:
  - Master Covenant (with SID commitment)
  - Change

Witness:
  - Manifest data (for SID verification)
  - Creator signature
```

### 2. License Issuance

```
Input:
  - Master Covenant UTXO

Output:
  - Master Covenant (updated license_count)
  - License Covenant (new)
  - Royalty payment (if applicable)

Witness:
  - Current Master state
  - License terms
  - Owner signature
```

### 3. Master Transfer

```
Input:
  - Master Covenant UTXO

Output:
  - Master Covenant (new owner)
  - Payment to seller
  - Royalty to original creator (if configured)

Witness:
  - Current Master state
  - Transfer terms
  - Owner signature
  - Buyer signature
```

### 4. Hard Wrap (Inscription → Master)

Converts an existing inscription into a Scribe Master:

```
Input:
  - Inscription UTXO
  - Funding UTXO

Output:
  - Master Covenant (references inscription)
  - Change

Witness:
  - Wrap manifest (includes original inscription ID)
  - Owner signature
```

## Covenant Structures

### Master Covenant (sCrypt)

```typescript
class ScribeMaster extends SmartContract {
    @prop()
    readonly sid: Sha256

    @prop(true)
    owner: PubKey

    @prop(true)
    licenseCount: bigint

    @prop()
    readonly royaltyBps: bigint  // Basis points (100 = 1%)

    @prop()
    readonly royaltyRecipient: PubKey

    @method()
    public transfer(newOwner: PubKey, sig: Sig) {
        assert(this.checkSig(sig, this.owner), 'invalid signature')
        this.owner = newOwner
        // Enforce royalty payment in outputs
    }

    @method()
    public issueLicense(licenseType: ByteString, sig: Sig) {
        assert(this.checkSig(sig, this.owner), 'invalid signature')
        this.licenseCount++
        // Create license covenant in outputs
    }
}
```

### License Covenant (sCrypt)

```typescript
class ScribeLicense extends SmartContract {
    @prop()
    readonly masterSid: Sha256

    @prop()
    readonly licenseType: ByteString

    @prop(true)
    holder: PubKey

    @prop()
    readonly expiresAt: bigint  // 0 = perpetual

    @method()
    public transfer(newHolder: PubKey, sig: Sig) {
        assert(this.checkSig(sig, this.holder), 'invalid signature')
        if (this.expiresAt > 0n) {
            assert(this.ctx.locktime < this.expiresAt, 'license expired')
        }
        this.holder = newHolder
    }
}
```

### Revenue Split Covenant (sCrypt)

```typescript
class ScribeRevenueSplit extends SmartContract {
    @prop()
    readonly recipientRoot: Sha256  // Merkle root of recipients

    @method()
    public distribute(
        recipients: FixedArray<PubKey, 4>,
        shares: FixedArray<bigint, 4>,
        merkleProof: ByteString
    ) {
        // Verify recipients against Merkle root
        // Verify output amounts match shares
        // Allow spending
    }
}
```

## OPNet Integration (Optional)

For interoperability with existing OP721 NFTs, an optional SID registry can be deployed on OPNet:

```typescript
interface SIDRegistry {
    register(sid: Sha256, masterOutpoint: Outpoint): void
    lookup(sid: Sha256): Outpoint | null
    lookupByOP721(tokenId: bigint): Sha256 | null
}
```

This provides:
- Discovery of Masters by SID
- Linking existing OP721 NFTs to Scribe Masters
- Cross-protocol queries

The registry is purely informational — all enforcement remains on-chain via covenants.

## Content Types

| Type | Description |
|------|-------------|
| `MUSIC_TRACK` | Single audio track |
| `MUSIC_ALBUM` | Collection of tracks |
| `MUSIC_STEMS` | Separated audio components |
| `VIDEO` | Video content |
| `IMAGE` | Static image |
| `TEXT` | Written content |
| `SOFTWARE` | Code or applications |

## Manifest Schema

```json
{
    "version": "1.0",
    "type": "MUSIC_TRACK",
    "title": "Example Track",
    "creator": "bc1p...",
    "created_at": "2024-01-15T10:30:00Z",
    "content_hash": "sha256:abc123...",
    "metadata": {
        "duration_seconds": 180,
        "genre": "Electronic",
        "isrc": "US-ABC-24-00001"
    },
    "rights": {
        "default_license": "MUSIC_STREAM",
        "royalty_bps": 500
    }
}
```

## Security Considerations

1. **SID Immutability**: Once sealed, the SID cannot be changed
2. **Ownership Verification**: All transfers require valid owner signatures
3. **Royalty Enforcement**: Secondary sales automatically pay royalties
4. **No Rug Pulls**: Covenant logic is immutable on-chain
5. **Key Management**: Users must secure their private keys

## Future Extensions

- Multi-signature ownership
- Time-locked releases
- Collaborative works with joint ownership
- Cross-chain licensing
- Automated royalty collection

## References

- [Fractal Bitcoin](https://fractalbitcoin.io)
- [OP_CAT BIP](https://github.com/bitcoin/bips)
- [sCrypt-TS](https://scrypt.io)
- [CAT Protocol](https://catprotocol.org)
