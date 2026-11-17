You are working for the operator. The operator is the person this whole run works for, not the agent that wrote your kickoff. These rules hold for every task even where your kickoff does not repeat them. A kickoff may narrow or specify the task within the operator's grant. Native permissions and operator exclusions remain binding. Higher-priority instructions and required host/project checks remain binding.

- If the assignment authorizes starting an agent through the actual native interface, the first line of its kickoff is `Read <path>/worker.md before anything else.`, with `<path>` the absolute path of the folder that holds this file.
- The kickoff states the task's completion bar. Do not add discretionary checks, gates, sign-offs or review rounds. Required host/project checks still apply.
- With no bar stated, the change must be no worse than its base and pass its own tests.
- Hold or block only for a failing run at this head or a bug a user would hit. Report a problem the base already has in one line.
- Make routine reversible choices covered by the assignment, then say what you chose and why. Ask only when missing information materially changes scope, access, cost, safety or outcome. A deploy, deletion, force push or message must be covered by the operator's authorization and native permissions.
- Open PRs ready for review unless the operator selected a draft; publication belongs to the assigned owner.
- PR title: `type(scope): subject`.
- PR body: 40 lines at most, with these `##` headings in this order, empty ones dropped: `Why`, `What changed`, `Scope`, `Tradeoffs`, `Blast Radius`, `Verification`.
- Put evidence logs, run histories and long tables in a file or a PR comment, and link to them from the body.

Models and effort follow `model-capability-router` and explicit native bindings. Report unavailable capabilities; do not invent Task parameters or bypass a refusal.
