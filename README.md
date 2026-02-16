# 🔍 AI Cost Tracker

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
![Demo](demo.gif)

**Stop getting surprise LLM bills. Track costs per user and feature with one decorator.**

---

## ❌ The Problem

You're getting **$10,000 OpenAI bills** with zero visibility:

- **Which users** are expensive? (Some cost $100/mo, others $0.50)
- **Which features** burn money? (Chat? Summary? Code generation?)
- **Which teams** are overspending? (Marketing using GPT-4 for everything)
- **When** are you about to blow your budget? (Find out at month-end 💸)

**OpenAI's dashboard only shows total org spend.** Useless for multi-user apps.

---

## ✅ The Solution

One decorator. Full visibility.

```python
from ai_cost_tracker import track_costs
from openai import OpenAI

client = OpenAI()

@track_costs(user_id="user_123", feature="chat")
def my_chat(prompt):
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

# That's it. Now you know:
# • Cost per user (down to the penny)
# • Cost per feature (chat vs summary vs code)
# • Tokens used (input + output)
# • Response time
```

**What you get:**

```python
from ai_cost_tracker import init_tracker

storage = init_tracker("costs.db")

# Total spend
print(f"${storage.get_total_cost():.2f}")

# Top 5 expensive users
for user_id, cost, calls in storage.get_top_users(5):
    print(f"{user_id}: ${cost:.4f} ({calls} calls)")

# Top 5 expensive features
for feature, cost, calls in storage.get_top_features(5):
    print(f"{feature}: ${cost:.4f} ({calls} calls)")
```

---

## Installation

```bash
pip install ai-cost-tracker
```

_(Coming soon to PyPI - for now install from source)_

```bash
git clone https://github.com/YOUR_USERNAME/ai-cost-tracker.git
cd ai-cost-tracker
pip install -e .
```

---

## 🎯 Why Use This?

**Before ai-cost-tracker:**

- 😱 "Why is our bill $10,000 this month?"
- 🤷 "Which user is costing us money?"
- 📊 Manually export OpenAI logs to spreadsheets
- 🔧 Build custom tracking scripts (takes days)

**After ai-cost-tracker:**

- ✅ See cost per user in real-time
- ✅ Identify expensive features instantly
- ✅ One decorator, zero maintenance
- ✅ Works with OpenAI **and** Anthropic

**Real example:** One user found a power user running GPT-4 unnecessarily. Switched to GPT-3.5-turbo. **Saved $500/month**.

---

## Quick Start

### Step 1: Install

```bash
pip install -e .  # or git clone and install
```

### Step 2: Add One Decorator

```python
from openai import OpenAI
from ai_cost_tracker import init_tracker, track_costs

# Initialize (creates local SQLite database)
storage = init_tracker("costs.db", org_id="my-org")
client = OpenAI()

# Wrap your function with @track_costs
@track_costs(user_id="user_1", feature="chat")
def chat(prompt: str):
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

# Use normally - costs tracked automatically
chat("How can I reduce LLM spend?")
```

### Step 3: View Your Costs

```python
# Total spend
print(f"Total: ${storage.get_total_cost():.2f}")

# Top users
for user_id, cost, calls in storage.get_top_users(limit=5):
    print(f"{user_id}: ${cost:.4f} ({calls} calls)")

# Top features
for feature, cost, calls in storage.get_top_features(limit=5):
    print(f"{feature}: ${cost:.4f} ({calls} calls)")
```

**That's it.** You now know exactly where your AI spend is going.

---

## Supported providers

- OpenAI (usage fields: `prompt_tokens`, `completion_tokens`)
- Anthropic (usage fields: `input_tokens`, `output_tokens`)

## API overview

- `init_tracker(storage_path, org_id="default")`
- `@track_costs(user_id, feature, metadata={})`
- `track_manual(user_id, feature, model, tokens_in, tokens_out, ...)`
- `SQLiteStorage.get_total_cost(filters={...})`
- `SQLiteStorage.get_top_users(limit=10)`
- `SQLiteStorage.get_top_features(limit=10)`

## FAQ

**Q: Do I need to change my OpenAI/Anthropic call logic?**
No. Wrap functions that return provider responses with `@track_costs`.

**Q: Can I track costs without a provider response object?**
Yes. Use `track_manual(...)` when you already know token counts.

**Q: Is this production safe?**
It includes error handling and indexed SQLite queries. For high write volume, you may replace the storage backend with a managed database implementation.

## Roadmap

- [x] ✅ Core Python library (OpenAI + Anthropic)
- [x] ✅ SQLite storage with filtering
- [x] ✅ Async function support
- [ ] 🚧 TypeScript/Node.js version (March 2026)
- [ ] 🚧 Cloud dashboard with charts (April 2026)
- [ ] 🚧 Budget alerts & Slack integration (May 2026)
- [ ] 🚧 PostgreSQL backend option (June 2026)

**Want a feature?** [Open an issue](../../issues) or give us a ⭐

---

## ⭐ Star This Project

If this saves you **time** or **money**, please star the repo!

It helps others discover the project and motivates us to keep improving it.

[![GitHub stars](https://img.shields.io/github/stars/briskibe/ai-cost-tracker?style=social)](https://github.com/briskibe/ai-cost-tracker/stargazers)

---

## Examples

Check out complete examples in the [`examples/`](examples/) directory:

- [`example_openai.py`](examples/example_openai.py) - Basic OpenAI tracking
- [`example_anthropic.py`](examples/example_anthropic.py) - Anthropic Claude tracking
- [`example_fastapi.py`](examples/example_fastapi.py) - FastAPI integration with automatic context

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick ways to help:**

- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🔧 Add support for new LLM providers

---

## License

MIT License - see [LICENSE](LICENSE) file.

---

## Support

- 📖 **Documentation:** This README + inline docstrings
- 🐛 **Issues:** [GitHub Issues](../../issues)
- 💬 **Discussions:** [GitHub Discussions](../../discussions)

---

**Built with ❤️ for developers tired of surprise AI bills.**

_Stop guessing. Start tracking._
