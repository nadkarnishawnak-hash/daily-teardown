# SF Compute (San Francisco Compute Company)

*2026-09-16 · Archetype: **arbitrage** · Founded 2023; closed a $40M Series A at a $300M valuation in December 2025 (DCD, citing WSJ), hired Voltage Park's ex-CEO as CTO, and spent 2026 getting written up as the stock market for GPUs (DailyDropout.FYI, July 2026).*

**Hook:** A 30-person company that owns zero GPUs manages over $100M of them

Audio: https://github.com/nadkarnishawnak-hash/daily-teardown/releases/download/ep-2026-09-16/2026-09-16-sf-compute-san-francisco-compute-company.mp3

## The setup

Big GPU clusters are sold the way office towers are leased: in one-to-three-year blocks, to whoever can sign a long contract. SF Compute is a roughly 30-person San Francisco company, founded in 2023, that lets AI teams get serious compute for hours or days instead of years, and lets whoever already signed the long contract do something with the hours they are not using. It publishes live prices for H100 and H200 capacity the way an exchange publishes a tape.

> Before you scroll: who has the budget here, the AI startup renting an hour or the data center sitting on stranded capacity? And where does the margin come from when the company owns none of the chips?

## The numbers

| | | |
|---|---|---|
| Revenue / run-rate | Not disclosed. Hard proxy: $40M Series A at a $300M valuation (Dec 2025), plus >$100M of hardware under management | [Data Center Dynamics, 2025 (citing the Wall Street Journal)](https://www.datacenterdynamics.com/en/news/sf-compute-raises-40m-for-ai-compute-marketplace-offering/) |
| Pricing | Public, posted clearing prices for Nvidia H100 and H200 capacity, sold on flexible short-term contracts rather than multi-year lock-ins; B300s flagged as coming | [Data Center Dynamics, 2025](https://www.datacenterdynamics.com/en/news/sf-compute-raises-40m-for-ai-compute-marketplace-offering/) |
| Margins / unit economics | Owns zero GPUs while managing >$100M of hardware with ~30 employees. est. $3.3M of hardware under management per head ($100M / 30). Capital-light: no chips, no concrete, no long-dated debt, so the spread between long-dated and short-dated compute is close to pure contribution | [Data Center Dynamics, 2025](https://www.datacenterdynamics.com/en/news/sf-compute-raises-40m-for-ai-compute-marketplace-offering/) |
| Funding / exit | $40M Series A at a $300M valuation, led by DCVC and Wing Venture Capital, with Electric Capital and Alt Capital participating (Dec 2025). No exit. | [Data Center Dynamics / eWEEK, 2025](https://www.eweek.com/news/sf-compute-ai-funding/) |

## The model

- **Economic buyer:** Two payers, one spread. AI labs, research teams and startups who need a big cluster for nine days and have compute budget but no appetite for a three-year commitment. And on the other side, data centers and enterprises already holding contracted capacity they are not using, who would rather recover cash than watch paid-for hardware idle. Both are paying for liquidity they cannot create themselves.
- **Emotional driver:** Fear of the lock-in. Nobody wants to be the person who signed a 36-month GPU contract for a model that got deprecated in month seven. On the sell side it is the sting of paying for idle metal every single night.
- **Recurring vs one-time:** Transactional, but structurally repeating. Training and inference demand is lumpy and constant, so the same buyers come back every cycle. It behaves like recurring revenue without a subscription.
- **Margins:** Spread-based and capital-light. Take rate is not public, so treat exact margin as unknown. What is known is the leverage: >$100M of hardware intermediated by ~30 people who own none of it (DCD, 2025). The cost of goods is the capacity contract; everything above it is the duration and access premium.
- **Capital to start:** $50k-$500k for a copycat in a different commodity. The software is trivial. The money goes to being the buyer of last resort on your own market for the first months, plus the legal work of standing behind contracts you did not originate.
- **Moat:** Honestly, thin on technology. The moat is liquidity and a public price. Once one venue has real prices and real fills, both sides default to it, and a second venue with no volume is useless to everyone. Add trust: you are selling someone else's hardware and eating the failure risk.
- **Distribution:** Word of mouth inside AI engineering circles, public posted prices as marketing (transparency is the ad), founder visibility, and investor networks pushing portfolio companies toward it. Hiring the former CEO of a GPU cloud as CTO buys supply-side relationships too.

## Why it works

Data centers must sell long because lenders underwrite long contracts, and AI teams must buy short because nobody can forecast what a model will need in eighteen months. That mismatch is not a temporary inefficiency, it is baked into how each side is financed, which means the price of a GPU-hour on a three-year contract and the price of the same GPU-hour next Tuesday will keep diverging. SF Compute stands in that gap, converts long and illiquid into short and liquid, and keeps part of the difference, without ever buying a chip or having to be right about where GPU prices go.

## Where else this shows up

- **Freight brokerage (C.H. Robinson and every three-person brokerage that copies it)**: Holds truckload capacity at contract rates and sells it into the spot market; owns no trucks, and the margin is purely knowing where the empty ones are.
- **Seats.aero**: Airlines price the same seat differently in miles and in cash; the product is simply the map of that gap, sold to people who could never find it themselves.

## How you'd start one today

- **First step:** Pick one asset sold in a size nobody actually wants: warehouse space leased by the year, commercial kitchen time, lab equipment, machine hours, dark fiber. Call five owners this week, ask what percentage of the month it sits idle, then find one buyer who has been turned away for being too small and broker a single deal by hand in a spreadsheet. No product, no code, just proof the gap is real and someone will pay it.
- **Hardest part:** The cold start. An empty market is worthless to both sides, so for the first stretch you have to be the buyer of last resort with your own cash, holding inventory you may not resell. That is balance-sheet risk, not a coding problem, and it is what stops the clones.

## Takeaway

When a market only sells in one size or one term, the distance between how a thing is sold and how it is actually needed is itself a business. You do not need to own the asset to get paid for closing that distance, but you do need to be willing to hold the risk nobody else will.

*Confidence: Medium-high: funding terms, headcount, and the >$100M-of-hardware-managed figure all come from a December 2025 DCD report citing the WSJ. Revenue and take rate are not public, so the spread economics are inferred from the model, not verified.*

### Sources

- [SF Compute raises $40m for AI compute marketplace offering](https://www.datacenterdynamics.com/en/news/sf-compute-raises-40m-for-ai-compute-marketplace-offering/) (2025)
- [SF Compute Raises $40M to Build Marketplace for AI Compute Capacity](https://www.eweek.com/news/sf-compute-ai-funding/) (2025)
- [SF Compute: The Stock Market for GPUs](https://dailydropout.substack.com/p/sf-compute-the-stock-market-for-gpus) (2026)
- [Spheron vs SF Compute: GPU Marketplace vs Cluster Market Compared](https://www.spheron.network/blog/spheron-vs-sf-compute/) (2026)
- [How SF Compute corners the offtake market](https://www.thedeepview.com/articles/how-sf-compute-corners-to-offtake-market) (2025)
- [SF Compute (official site, live H100/H200 pricing)](https://sfcompute.com/) (2026)

## What else is moving

- **Intel spinoff Cornelis Networks raised $205M led by IAG Capital Partners and launched Active Compute Fabric, a GPU-agnostic AI networking layer, with Qualcomm signed as a rack-scale inference partner; CN5000 400 Gbps ships now, CN6000 800 Gbps in Q4.** Why it matters: Interconnect is where Nvidia's lock-in and margin sit, so a funded open alternative is the first real pricing pressure on AI infra costs. [TechCrunch](https://techcrunch.com/2026/09/14/ai-infrastructure-company-cornelis-raises-205m-to-chip-away-at-nvidias-dominance/)
- **Apple opened the English public beta of its rebuilt Siri, powered by models custom-built with Google's Gemini, split between on-device and Private Cloud Compute, with daily limits on some server-backed features and no EU or China availability.** Why it matters: Apple outsourcing the model layer and rate-limiting inference is a live signal that assistant unit economics are still brutal at scale. [Apple Newsroom](https://apple.com/newsroom/2026/09/siri-ai-a-profoundly-more-capable-and-personal-assistant-is-here)
- **Perplexity's Portable Computer agent went live in its Windows app for Nvidia RTX GPUs with 24GB+ VRAM, running model, harness, orchestrator and scheduler on-device with a default local Qwen model and permission prompts before any cloud call.** Why it matters: A fully local agent changes the compliance calculus for workflows touching customer data, contracts or anything you can't send to a vendor API. [NVIDIA Blog](https://blogs.nvidia.com/blog/local-ai-perplexity-windows-pcs/)
- **Anthropic reported its continuous-integration workload grew 25x in six months, with engineers shipping roughly 8x more code per quarter and Claude authoring about 80% of it; test volume rose 10x, forcing a move to change-based test-impact analysis.** Why it matters: Agentic coding shifts cost rather than removing it: verification infra scales faster than your dev savings, so price CI and QA in before you commit. [Anthropic](https://claude.com/blog/agentic-coding-is-straining-ci-heres-how-we-scaled-test-impact-analysis-at-anthropic)
