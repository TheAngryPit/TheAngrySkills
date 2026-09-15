import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


detector = load_script("detect-upstream-updates")
lifecycle = load_script("upstream-pr-lifecycle")


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def commit(repo, message):
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", message],
        check=True,
    )
    return git(repo, "rev-parse", "HEAD")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def matt_root(tmp_path, upstream):
    root = tmp_path / "repo"
    source_paths = [
        ("skills/engineering/code-review", "skills/mirrors-mattpocock/code-review"),
        ("skills/productivity/writing-for-agents", "skills/engineering/writing-for-astra"),
    ]
    write(root / "scripts/matt-adaptations.json", json.dumps([
        {"name": "code-review", "destination": destination, "source_path": source, "overlay": "patch"}
        for source, destination in source_paths[:1]
    ]))
    for source, destination in source_paths:
        source_dir = upstream / source
        write(source_dir / "SKILL.md", f"# {source}\n")
        destination_dir = root / destination
        write(destination_dir / "SKILL.md", "# local adaptation\n")
        record = {
            "commit": "pending",
            "source_path": source,
            "upstream_sha256": detector.snapshot(upstream, source),
        }
        write(destination_dir / "UPSTREAM.json", json.dumps(record))
    return root


def test_matt_ignores_unrelated_commits_and_reports_support_and_new_skills(tmp_path):
    upstream = tmp_path / "matt"
    upstream.mkdir()
    subprocess.run(["git", "init", "-q", str(upstream)], check=True)
    write(upstream / "LICENSE", "MIT\n")
    root = matt_root(tmp_path, upstream)
    # Matt's upstream repository contains skills outside this repository's
    # accepted adaptation batch; an already-present one is not new drift.
    write(upstream / "skills/old-unpublished/SKILL.md", "historical\n")
    baseline = commit(upstream, "baseline")
    for record in (root / "skills/mirrors-mattpocock/code-review/UPSTREAM.json", root / "skills/engineering/writing-for-astra/UPSTREAM.json"):
        data = json.loads(record.read_text())
        data["commit"] = baseline
        record.write_text(json.dumps(data))

    write(upstream / "README.md", "unrelated\n")
    commit(upstream, "unrelated")
    report = detector.detect_matt(upstream, root)
    assert report["changed"] is False
    assert report["changed_skills"] == []
    assert report["changed_support_files"] == []

    write(upstream / "skills/engineering/code-review/references/notes.md", "new support\n")
    write(upstream / "skills/new-skill/SKILL.md", "candidate\n")
    commit(upstream, "relevant drift")
    report = detector.detect_matt(upstream, root)
    assert report["changed"] is True
    assert report["changed_support_files"] == ["skills/engineering/code-review/references/notes.md"]
    assert report["new_skills"] == ["skills/new-skill"]
    assert report["candidate_content_promoted"] is False


def cursor_root(tmp_path, upstream, baseline):
    root = tmp_path / "repo"
    setup = upstream / "pstack/skills/setup-pstack/SKILL.md"
    excluded = upstream / "pstack/skills/make-bot-ui/SKILL.md"
    manifest = {
        "schema_version": 1,
        "upstream_commit": baseline,
        "upstream_repository": "https://github.com/cursor/plugins.git",
        "skills": [
            {
                "path": "pstack/skills/setup-pstack/SKILL.md",
                "published_name": "cursor-setup-pstack",
                "family": "pstack",
                "files": {"SKILL.md": detector.sha(setup)},
                "publish": True,
            },
            {
                "path": "pstack/skills/make-bot-ui/SKILL.md",
                "published_name": "cursor-make-bot-ui",
                "family": "pstack",
                "files": {"SKILL.md": detector.sha(excluded)},
                "publish": False,
                "excluded_from_mirror": True,
                "exclusion_reason": "fixture hold",
            },
        ],
        "support_files": {
            "pstack/agents/pstack-subagent.md": {
                "sha256": detector.sha(upstream / "pstack/agents/pstack-subagent.md"),
                "related_skills": ["cursor-setup-pstack"],
            }
        },
    }
    write(root / "sources/cursor-plugins/manifest.json", json.dumps(manifest))
    return root


def test_cursor_pstack_reports_skill_support_inventory_and_holds_exclusion(tmp_path):
    upstream = tmp_path / "cursor"
    upstream.mkdir()
    subprocess.run(["git", "init", "-q", str(upstream)], check=True)
    write(upstream / "pstack/LICENSE", "MIT\n")
    write(upstream / "pstack/README.md", "pstack\n")
    write(upstream / "pstack/agents/pstack-subagent.md", "agent\n")
    write(upstream / "pstack/skills/setup-pstack/SKILL.md", "budget: 1\n")
    write(upstream / "pstack/skills/make-bot-ui/SKILL.md", "held\n")
    write(upstream / "other/skills/unrelated/SKILL.md", "unrelated\n")
    baseline = commit(upstream, "baseline")
    root = cursor_root(tmp_path, upstream, baseline)

    write(upstream / "pstack/skills/setup-pstack/SKILL.md", "budget: 2\n")
    write(upstream / "pstack/README.md", "pstack updated\n")
    write(upstream / "pstack/skills/make-bot-ui/SKILL.md", "held updated\n")
    write(upstream / "pstack/skills/new-skill/SKILL.md", "candidate\n")
    write(upstream / "other/README.md", "unrelated\n")
    latest = commit(upstream, "pstack drift")

    report = detector.detect_cursor(upstream, root)
    assert report["baseline"] == baseline
    assert report["latest"] == latest
    assert report["changed"] is True
    assert report["changed_skills"] == [
        "pstack/skills/make-bot-ui/SKILL.md",
        "pstack/skills/setup-pstack/SKILL.md",
    ]
    assert "pstack/README.md" in report["changed_support_files"]
    assert report["new_skills"] == ["pstack/skills/new-skill"]
    assert report["excluded_skills"] == ["pstack/skills/make-bot-ui"]
    assert all(not path.startswith("other/") for path in report["changed_support_files"])


def test_cursor_unchanged_when_only_another_plugin_moves(tmp_path):
    upstream = tmp_path / "cursor"
    upstream.mkdir()
    subprocess.run(["git", "init", "-q", str(upstream)], check=True)
    write(upstream / "pstack/LICENSE", "MIT\n")
    write(upstream / "pstack/README.md", "pstack\n")
    write(upstream / "pstack/agents/pstack-subagent.md", "agent\n")
    write(upstream / "pstack/skills/setup-pstack/SKILL.md", "budget: 1\n")
    write(upstream / "pstack/skills/make-bot-ui/SKILL.md", "held\n")
    baseline = commit(upstream, "baseline")
    root = cursor_root(tmp_path, upstream, baseline)
    write(upstream / "other/skills/new/SKILL.md", "unrelated\n")
    commit(upstream, "other plugin")
    report = detector.detect_cursor(upstream, root)
    assert report["changed"] is False
    assert report["changed_skills"] == []
    assert report["changed_support_files"] == []


def test_lifecycle_fails_closed_for_duplicates_and_ref_mismatch():
    prs = [
        {"number": 10, "body": lifecycle.family_batch_marker("matt", "adapted"), "baseRefName": "main", "headRefName": "automation/upstream-matt-adapted"},
    ]
    assert lifecycle.select_pr(prs, "matt", "adapted", "main", "automation/upstream-matt-adapted") == {"action": "update", "number": 10}
    duplicate = prs + [{**prs[0], "number": 11}]
    try:
        lifecycle.select_pr(duplicate, "matt", "adapted", "main", "automation/upstream-matt-adapted")
    except ValueError as error:
        assert "multiple open PRs" in str(error)
    else:
        raise AssertionError("duplicate PR marker was accepted")
    mismatched = [{**prs[0], "headRefName": "someone-else"}]
    try:
        lifecycle.select_pr(mismatched, "matt", "adapted", "main", "automation/upstream-matt-adapted")
    except ValueError as error:
        assert "unexpected refs" in str(error)
    else:
        raise AssertionError("mismatched PR refs were accepted")


def test_pr_body_keeps_bounded_codex_request_and_no_promotion():
    report = detector.blank_result("cursor", "pstack", "https://example.invalid/cursor", "old", "new")
    evidence = detector.render_report(report)
    body = lifecycle.pr_body(report, evidence, lifecycle.bounded_prompt(report))
    assert body.count(report["marker"]) == 1
    assert "@codex update" in body
    assert "Do not publish new skills" in body
    report["candidate_content_promoted"] = True
    try:
        lifecycle.pr_body(report, evidence, "@codex update")
    except ValueError as error:
        assert "cannot be promoted" in str(error)
    else:
        raise AssertionError("promotion was accepted")


def test_scheduled_workflow_is_review_only_and_scoped_to_two_batches():
    workflow = (ROOT / ".github/workflows/review-matt-cursor-upstreams.yml").read_text()
    assert "--family matt" in workflow
    assert "--family cursor" in workflow
    assert "gh pr create" in workflow
    assert "gh pr edit" in workflow
    assert "gh pr merge" not in workflow
    assert "--force" not in workflow
    assert "reports/upstream-updates" in workflow
