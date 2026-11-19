# Vocabulary

lintel's sample data comes from architecture, engineering and construction (AEC) work in Autodesk-style design software. This page defines the industry terms, the Autodesk names, and the eval terms used across the repo.

## AEC terms in the sample cases

| Term | What it means | Where it shows up |
|---|---|---|
| **AEC** | Architecture, engineering and construction: the industries that design and build buildings and infrastructure. | Throughout |
| **BIM** | Building information modeling. A 3D model of a building where every element (wall, door, duct) carries data, such as its size, material and fire rating. | The sample assistant works inside BIM authoring software |
| **Model** | The BIM file for a project. "Your local model is unchanged" means the user's file wasn't altered. | c04, c09 |
| **Drawing sheet** | One page of a construction drawing set, such as a floor plan or a set of details. Sheets have numbers like A101, where A means architectural. Teams export sheets to PDF to print or send to the builder. | c07 |
| **Drawing set** | The full collection of drawing sheets for a project. | c07 |
| **Level** | A floor of the building in the model, such as Level 2. | c03, c05, c06 |
| **Section view** | A drawing that shows the building as if sliced through, so you can see inside walls and floors. | c01 |
| **Family** | A reusable building component in BIM software, such as a door type or a light fixture. Unused families add file size. | c02 |
| **Purge** | Remove unused items, such as families, from a model to make the file smaller. It deletes data, so it needs confirmation. | c02 |
| **MEP** | Mechanical, electrical and plumbing: ducts, pipes, wiring and equipment. | c05 |
| **Clash detection** | An automated check that finds places where elements collide, such as a duct running through a beam. | c05 |
| **RFI** | Request for information. A formal question from a contractor to the design team, such as whether a beam size can change. Each RFI has a number, a status and a due date. | c08 |
| **W18 / W16** | Steel beam sizes. W means wide-flange, and the number is the approximate depth in inches. | c08 |
| **Grid line** | A labeled reference line on the plan, such as C/4, used to locate columns and beams. | c08 |
| **Fire rating** | How long a wall or floor resists fire in a standard test, such as 1 hour. Required ratings depend on the building code. | c06 |
| **Occupancy classification** | The code category for how a building is used. I-2 covers hospitals and similar care facilities. | c06 |
| **Sprinklered** | The building has an automatic fire sprinkler system, which can change code requirements. | c06 |
| **Riser and tread** | A stair's vertical step height (riser) and horizontal step depth (tread). Codes set limits for both. | c09 |
| **Building code** | The rules a building must meet for safety. Each jurisdiction adopts a specific code edition, often with local changes. | c06, c09 |
| **Code official / AHJ** | The person or office with final say on code questions for a project. AHJ stands for authority having jurisdiction. | c06, c09, `uncertainty_signaled` rubric |
| **Engineer of record** | The licensed engineer legally responsible for a project's engineering design. | `uncertainty_signaled` rubric |
| **Code consultant** | A specialist a project hires to interpret code requirements. | c06, c09 |
| **Render** | A realistic image generated from the 3D model. Quality and resolution settings (DPI) affect how long it takes. | c12 |

## Autodesk names

| Name | What it is | Source |
|---|---|---|
| **Autodesk Assistant** | Autodesk's AI assistant across its products. Autodesk describes it as an agentic application that detects user intent and coordinates product features, domain agents and services. | [AI Transparency Cards](https://www.autodesk.com/trust/trusted-ai/ai-transparency-cards) |
| **Autodesk Forma** | Autodesk's industry cloud for architecture, engineering and construction. | [AU 2026 press release](https://kyodonewsprwire.jp/release/202609165978) |
| **Autodesk Fusion** | Autodesk's industry cloud for design and manufacturing. | [AU 2026 press release](https://kyodonewsprwire.jp/release/202609165978) |
| **Autodesk Flow** | Autodesk's industry cloud for media and entertainment. | [AU 2026 press release](https://kyodonewsprwire.jp/release/202609165978) |
| **Revit** | Autodesk's BIM authoring software for buildings. | [Revit Public MCP Server](https://www.autodesk.com/blogs/aec/2026/06/17/revit-public-mcp-server/) |
| **AI Orchestrator** | The part of the next-generation Assistant that picks a model for each task based on accuracy, speed, security and cost. | [AU 2026 press release](https://kyodonewsprwire.jp/release/202609165978) |
| **Assistant Builder** | Lets customers connect their own AI agents, tools and partner services to Autodesk project context. | [AU 2026 press release](https://kyodonewsprwire.jp/release/202609165978) |
| **Design & Make Marketplace** | Where Autodesk plans to offer third-party agents. | [AU 2026 press release](https://kyodonewsprwire.jp/release/202609165978) |
| **AI Transparency Cards** | Published summaries of each AI feature: what it does, the data and technology behind it, safeguards and known limitations. | [AI Transparency Cards](https://www.autodesk.com/trust/trusted-ai/ai-transparency-cards) |
| **Trusted AI** | Autodesk's program for responsible AI, built on five principles: responsibility, transparency, reliability, safety and security, and accountability. | [Trusted AI: Explained](https://adsknews.autodesk.com/en/stories/how-autodesk-builds-trusted-ai/) |
| **APS** | Autodesk Platform Services: Autodesk's developer APIs. | [APS DevCon MCP workshop](https://aps.autodesk.com/blog/devcon-mcp-workshop-now-speaks-net) |
| **MCP** | Model Context Protocol: an open standard that lets AI assistants connect to tools and data. Autodesk publishes MCP servers, including one for Revit. | [Revit Public MCP Server](https://www.autodesk.com/blogs/aec/2026/06/17/revit-public-mcp-server/) |
| **AU** | Autodesk University, Autodesk's annual conference. | [AU 2026 press release](https://kyodonewsprwire.jp/release/202609165978) |
| **Editorial Style Guide** | Autodesk's public guide to grammar, word choice, voice and branded terms. | [Autodesk Editorial Style Guide](https://styleguide.autodesk.com/?p=7388) |

## Eval terms used in lintel

| Term | What it means |
|---|---|
| **Eval** | A repeatable test for an AI system: a set of situations, the agent's responses, and rules for grading them. |
| **Agent** | An AI assistant that can take actions, such as calling tools or changing files, as well as answer questions. |
| **Case** | One test situation, with the behavior you expect. Stored in `datasets/`. |
| **Trace** | The full record of one conversation: user messages, agent replies, tool calls and tool results. Stored in `runs/`. |
| **Tool call** | When the agent asks software to do something, such as export sheets or run clash detection. |
| **Baseline / candidate** | The current agent version and the new version being tested. |
| **Lint** | Level 1: checks word choice and wording rules from the style guide. |
| **Contract** | Level 2: a rule about which parts a reply needs in a given situation, such as after an error. |
| **Trajectory** | Level 3: checks on what the agent did, step by step. |
| **Judge** | Level 4: grades replies against a rubric. Can be a script or an LLM. |
| **Rubric** | A list of questions a judge answers about each reply, with descriptions of pass, partial and fail. |
| **Calibration** | Comparing the judge's grades with grades from people to see how far the judge can be trusted. |
| **Cohen's κ (kappa)** | A measure of agreement that removes the agreement you'd get by chance. lintel trusts a judge criterion at 0.60 or higher. |
| **Severity** | How serious a finding is: `blocker` holds the release, `major` fails the case, `minor` is reported. |
| **Release gate** | The final ship or hold decision for a new agent version. |
| **Regression** | A case that passed in the baseline and fails in the candidate. |
| **CI** | Continuous integration: automated checks that run on every code change. |
