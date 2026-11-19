# How lintel connects to Autodesk's AI work

lintel uses AEC as its sample domain on purpose. This page maps each part of lintel to something Autodesk has said publicly about Autodesk Assistant and its agent platform. Each point is paraphrased and links to its source.

## 1. Autodesk Assistant is moving toward taking actions

At Autodesk University 2026, Autodesk previewed agentic AI across Forma, Fusion and Flow as the next generation of Autodesk Assistant. Autodesk defines agentic AI as AI that uses project context to help professionals understand, plan and take action toward an outcome. ([AU 2026 press release](https://kyodonewsprwire.jp/release/202609165978), [Unite.AI coverage](https://www.unite.ai/autodesk-previews-agentic-ai-across-forma-fusion-and-flow/))

**How lintel helps:** an agent that acts needs checks on its actions. Level 3 checks whether the agent asked before purging families, asked a question before renaming 212 doors, and reported a partial export accurately.

## 2. Human oversight is a stated commitment

Autodesk publishes AI Transparency Cards and says Autodesk Assistant is designed to support professional judgment with controls and human oversight. Its transparency guide describes human oversight as users being able to "review, edit, or approve generated outputs before a final action is taken." ([AU 2026 press release](https://kyodonewsprwire.jp/release/202609165978), [AI Transparency Cards](https://www.autodesk.com/trust/trusted-ai/ai-transparency-cards))

**How lintel helps:** it turns that description into a test. The `confirm.<tool>` check is a blocker if a destructive tool runs before the agent asks and the user replies. The `undo.offered` check confirms the user is told how to reverse the change.

## 3. Agents will get write access to models

The Revit Public MCP Server (Tech Preview, June 2026) is read-only. Autodesk says tools to create, modify and manage model data are planned for a separate write server, so users stay in control of what AI can change. ([Revit Public MCP Server](https://www.autodesk.com/blogs/aec/2026/06/17/revit-public-mcp-server/))

**How lintel helps:** write tools are where action checks matter most. The sample cases use tools like `purge_unused`, `rename_elements` and `modify_elements`, and the roadmap includes a policy pack for write tools.

## 4. More agents and more models, through one orchestrator

Assistant Builder will let customers connect their own agents, tools and partner services to Autodesk project context. Third-party agents from the Design & Make Marketplace are planned. An AI Orchestrator picks a model for each task based on accuracy, speed, security and cost. ([AU 2026 press release](https://kyodonewsprwire.jp/release/202609165978))

**How lintel helps:** when the model changes from task to task and some agents come from partners, users still expect one consistent voice and one standard for honesty and error recovery. lintel reads traces, so it works with any model or agent, and each report records which judge and rubric versions produced its scores.

## 5. Autodesk builds agent infrastructure in the open

Autodesk contributed enterprise requirements to the MCP specification, including stable client identity through Client Identifier Metadata Documents, and joined the Fine-Grained Authorization working group ([Autodesk News, Feb 2026](https://adsknews.autodesk.com/en/?p=55711)). The open-source APS DevCon 2026 workshop walks developers from a basic MCP server to an LLM agent that calls Autodesk Platform Services APIs ([APS blog](https://aps.autodesk.com/blog/devcon-mcp-workshop-now-speaks-net), [repo](https://github.com/autodesk-platform-services/mcp-devcon2026)).

**How lintel helps:** the workshop ends with a working agent. lintel covers the next question: is that agent ready to ship? The MCP trace adapter on the roadmap would let agents built from the workshop run through lintel.

## 6. Autodesk already has an editorial standard

Autodesk publishes an [Editorial Style Guide](https://styleguide.autodesk.com/?p=7388), managed by its content strategy team with input from a company-wide style council. It calls for active voice ([usage guidance](https://styleguide.autodesk.com/?p=5382)), simpler English for translation ([Global Writing](https://styleguide.autodesk.com/?p=5553)), and careful human review of AI output for accuracy and tone ([Using Generative AI](https://styleguide.autodesk.com/using-generative-ai/)).

**How lintel helps:** level 1 already flags passive voice, long sentences and high reading levels, and it skips English-only rules on other languages. A team could encode its own guide in the same YAML format and check every assistant reply automatically. Docs teams already use this pattern with Vale, which keeps style rules as YAML in the repo and enforces them in the editor and in CI ([Thoughtworks Technology Radar](https://www.thoughtworks.com/radar/tools/vale)).

---

*lintel has no affiliation with Autodesk. The rules in `config/styleguide.yaml` are my own examples and are separate from Autodesk's style guide.*
