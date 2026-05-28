# Croquembouche

> A stateful Discord automation system with event-driven activity tracking, persistent countdown scheduling, and runtime-configurable behavior — built around a PostgreSQL-backed architecture that survives process restarts without state loss.

---

## Overview

Croquembouche is a personal-scale Discord bot engineered for operational correctness rather than feature breadth. It solves a specific class of problems — tracking time-sensitive events and user presence — with a persistence model that treats the database as the source of truth, not application memory.

The design philosophy is deliberately constrained: one server, one tracked user, zero configuration drift. Settings mutate through Discord commands and are committed to the database immediately, meaning no environment variable reload, no process restart, and no state divergence between what the bot *thinks* it's configured as and what it *actually* is.

This is not a framework. It is a system with clearly bounded responsibilities.

---

## Architecture

```
Discord Gateway (WebSocket)
        │
        ▼
  Event Dispatcher
  ┌─────────────────────────────────────┐
  │  on_ready       → Bootstrap         │
  │  on_presence_update → Session Log   │
  │  on_command     → Command Router    │
  └─────────────────────────────────────┘
        │
        ▼
  PostgreSQL (Single Source of Truth)
  ┌──────────────┬──────────────────────┐
  │  config      │  Runtime state KV    │
  │  countdowns  │  Named date targets  │
  │  activity    │  Session audit log   │
  └──────────────┴──────────────────────┘
```

**Key design decisions:**

- **No in-memory config caching with manual invalidation.** Every config read hits the database. This trades marginal latency for guaranteed consistency — acceptable at single-server scale, eliminates an entire class of stale-state bugs.
- **Session duration is computed, not stored.** The activity log records discrete `online` and `offline` events with timestamps. Duration is derived at query time, making the raw log auditable and replayable.
- **Schema bootstraps on first run.** No migration tooling required for initial deployment. The bot creates its own tables if they don't exist, reducing operational surface area for a single-operator setup.
- **Countdown delivery is presence-gated.** Reminders fire when the tracked user comes *online*, not on a wall-clock schedule. This avoids wasted notifications and aligns delivery with actual attention.

---

## Data Model

```sql
-- Runtime configuration. Mutable via Discord command at any time.
config (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
)

-- Named countdowns with target dates.
countdowns (
  name       TEXT PRIMARY KEY,
  target_date DATE NOT NULL
)

-- Append-only presence audit log.
activity_log (
  id         SERIAL PRIMARY KEY,
  event_type TEXT NOT NULL,   -- 'online' | 'offline'
  timestamp  TIMESTAMPTZ DEFAULT NOW()
)
```

The schema is intentionally minimal. No foreign keys, no soft deletes, no versioning overhead. At personal scale, simplicity is a correctness property.

---

## Prerequisites

| Dependency | Version | Purpose |
| :--- | :--- | :--- |
| Python | 3.8+ | Runtime |
| [uv](https://docs.astral.sh/uv/) | latest | Dependency isolation & reproducible installs |
| PostgreSQL | 12+ | Persistent state |
| Discord Bot Token | — | Gateway authentication |

---

## Deployment

**1. Clone**

```bash
git clone https://github.com/sadmanhsakib/croquembouche-discordBot.git
cd croquembouche-discordBot
```

**2. Install dependencies**

```bash
uv sync
```

**3. Configure environment**

```bash
copy example.env .env    # Windows
cp example.env .env      # macOS / Linux
```

Edit `.env`:

```env
BOT_TOKEN=your_discord_bot_token
DATABASE_URL=postgresql://user:password@host:5432/dbname
USER_ID=target_user_discord_id
```

| Variable | Description |
| :--- | :--- |
| `BOT_TOKEN` | Discord bot token from the Developer Portal. |
| `DATABASE_URL` | Standard PostgreSQL DSN. Supports connection pooling URLs. |
| `USER_ID` | Snowflake ID. |

**4. Run**

```bash
uv run python main.py
```

On first run, the bot connects to PostgreSQL and creates all required tables if they do not exist. No separate migration step.

---

## Command Reference

### General

| Command | Description |
| :--- | :--- |
| `bonjour` | Greeting. Confirms the bot is responsive. |
| `status` | Reports operational status. |
| `ping` | Returns gateway round-trip latency in milliseconds. |
| `help` | Displays this command index. |

### Countdown Management

Countdowns are stored by name and resolved to day-delta at delivery time. There is no precomputed "days remaining" field — the value is always current.

| Command | Description |
| :--- | :--- |
| `add countdown <NAME> <DATE>` | Registers a countdown. `DATE` format: `YYYY-MM-DD`. |
| `rmv countdown <NAME>` | Removes a countdown by name. |
| `list` | Lists all active countdowns with days remaining. |

### Administration

| Command | Description |
| :--- | :--- |
| `del <amount>` | Bulk-deletes the specified number of messages from the current channel. |
| `set <VARIABLE> <VALUE>` | Mutates a runtime configuration variable and commits it to the database immediately. |

**Runtime-configurable variables:**

| Variable | Effect |
| :--- | :--- |
| `PREFIX` | Changes the command prefix without restarting the process. |
| `SHOULD_LOG` | Enables or disables presence event logging. |
| `COUNTDOWN_CHANNEL_ID` | Redirects countdown delivery to a different channel. |

---

## Operational Notes

**On presence tracking accuracy:** Discord's `on_presence_update` event fires for status changes (online → idle → offline), not just binary connect/disconnect events. Depending on your Discord client and activity, multiple events may fire in quick succession. The activity log captures all of them; session duration calculations should account for this at query time.

**On countdown delivery guarantees:** Reminders are delivered once per online event. If the bot is offline when the tracked user comes online, that trigger is missed. For higher-reliability delivery, consider supplementing with a scheduled job that checks countdowns on an interval independent of presence events.

**On the `USER_ID` constraint:** The single-user tracking model is an explicit scope constraint, not a technical limitation. Tracking multiple users would require a schema change (user_id column on activity_log) and routing logic in the presence handler.

---

## Public Alternative

This bot is private and scoped to a single personal server. A public variant, [Croissant](https://discord.com/oauth2/authorize?client_id=1419550251739516959&permissions=1374389746800&integration_type=0&scope=bot), is available for multi-server deployment.

---

## Contributing

The core architecture and feature scope are stable. Bug reports and well-reasoned feature proposals are welcome via GitHub Issues. Pull Requests are reviewed against the project's design constraints — changes that add operational complexity without proportional value will be declined.

**Lead Developer:** [Sadman Sakib](https://github.com/sadmanhsakib)

---

## License

[PolyForm Noncommercial License 1.0.0](LICENSE) — free for personal and non-commercial use.