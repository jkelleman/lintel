# Why this matters at Autodesk

lintel's sample domain is AEC on purpose. Here's how it lines up with what Autodesk has said publicly about where Autodesk Assistant and its agent platform are going. Everything below is paraphrased from public sources, linked at the end of each point.

## 1. The Assistant is becoming an agent that acts, not a chatbot that answers

At Autodesk University 2026, Autodesk previewed agentic AI across Forma, Fusion and Flow as the next generation of Autodesk Assistant, working across products, projects and teams. Autodesk defines agentic AI as using project context to help professionals understand, plan and *take action*, not only answer questions. ([AU 2026 press release](https://kyodonewsprwire.jp/release/202609165978), [Unite.AI coverage](https://www.unite.ai/autodesk-previews-agentic-ai-across-forma-fusion-and-flow/))

**What lintel adds:** once an agent acts, evaluating the words isn't enough. Rung 3 checks what the agent *did*: asked before purging, clarified before renaming 212 doors, reported a partial export honestly.

## 2. Human oversight is a stated product commitment

Autodesk publishes AI Transparency Cards and describes the Assistant as designed to support professional judgment with controls and human oversight. Its transparency guide defines human oversight as users being able to "review, edit, or approve generated outputs before a final action is taken." ([AU 2026 press release](https://kyodonewsprwire.jp/release/202609165978), [AI Transparency Cards](https://www.autodesk.com/trust/trusted-ai/ai-transparency-cards))

**What lintel adds:** that definition becomes a testable contract. `confirm.<tool>` is a blocker-level check that a destructive tool never runs before a question and a user reply, and `undo.offered` checks that the user is told how to reverse it.

## 3. Agents are getting write access to models

The Revit Public MCP Server (Tech Preview, June 2026) is read-only today. Autodesk says create, modify and manage tools are planned for a separate write server, so users control what AI can change. ([Revit Public MCP Server](https://www.autodesk.com/blogs/aec/2026/06/17/revit-public-mcp-server/))

**What lintel adds:** the write server is where trajectory evals become essential. lintel's sample cases (`purge_unused`, `rename_elements`, `modify_elements`) are the kinds of tools a write server exposes, and the roadmap includes a write-tool policy pack.

## 4. More agents, from more places, through one orchestrator

Assistant Builder will let customers connect their own agents, tools and partner services to Autodesk project context, with third-party agents from the Design & Make Marketplace planned. Behind it, an AI Orchestrator picks models per task based on accuracy, speed, security and cost. ([AU 2026 press release](https://kyodonewsprwire.jp/release/202609165978))

**What lintel adds:** when the model changes per task and agents come from outside Autodesk, the voice, honesty and recovery behavior users experience needs one shared bar that every model and agent is measured against. lintel's gate is model-agnostic. It reads traces, not model internals, and records which judge and rubric versions produced each score.

## 5. Autodesk builds agent infrastructure in the open

Autodesk contributed enterprise requirements to the MCP specification (stable client identity via Client Identifier Metadata Documents) and joined the Fine-Grained Authorization working group ([Autodesk News, Feb 2026](https://adsknews.autodesk.com/en/?p=55711)). The APS DevCon 2026 workshop is open source and goes from a bare MCP server to an LLM agent grounded in APS APIs ([APS blog](https://aps.autodesk.com/blog/devcon-mcp-workshop-now-speaks-net), [repo](https://github.com/autodesk-platform-services/mcp-devcon2026)).

**What lintel adds:** the workshop's arc ends at "agent works." lintel is the next step: "agent is ready to ship." The roadmap's MCP trace adapter would let any agent built from that workshop run through the ladder.

## 6. The editorial standard already exists, so make it executable

Autodesk maintains a public [Editorial Style Guide](https://styleguide.autodesk.com/?p=7388), managed by its content strategy team with a cross-company style council. It calls for active voice ([usage guidance](https://styleguide.autodesk.com/?p=5382)), simpler English for translation ([Global Writing](https://styleguide.autodesk.com/?p=5553)), and careful human validation of AI output for accuracy and tone ([Using Generative AI](https://styleguide.autodesk.com/using-generative-ai/)).

**What lintel adds:** rung 1 already flags passive voice, long sentences and reading level, and skips English-only rules on other locales. The same YAML pattern could encode a team's own guide, so the guide checks every assistant reply instead of waiting for a reviewer. Teams that write docs as code already do this with Vale (style rules as YAML in the repo, enforced in the editor and in CI, per [Thoughtworks Technology Radar](https://www.thoughtworks.com/radar/tools/vale)).

---

*lintel isn't affiliated with Autodesk. Rules in `config/styleguide.yaml` are my own illustrative examples, not Autodesk's style guide.*
