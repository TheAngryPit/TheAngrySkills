#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  update-skillset.sh <manifest.tsv> [--apply]

Default is dry-run. Use --apply to execute.

Behavior:
  - named skills use: npx skills update
  - wildcard rows (skill=*) use: npx skills add <repo> --skill '*'
  - wizard rows (skill=__wizard__) use: npx skills add <repo>

The wildcard add path is intentional: it picks up newly-added skills from the
remote repository, while native update only updates skills that are already
installed by name.
USAGE
}

quote_cmd() {
  local out=()
  local arg
  for arg in "$@"; do
    printf -v arg "%q" "$arg"
    out+=("$arg")
  done
  printf '%s\n' "${out[*]}"
}

resolve_manifest() {
  local input="$1"
  local script_dir
  local skill_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  skill_dir="$(cd "$script_dir/.." && pwd)"

  if [[ -f "$input" ]]; then
    printf '%s\n' "$input"
  elif [[ -f "$skill_dir/$input" ]]; then
    printf '%s\n' "$skill_dir/$input"
  elif [[ -f "$skill_dir/skillsets/$input" ]]; then
    printf '%s\n' "$skill_dir/skillsets/$input"
  else
    printf 'Manifest not found: %s\n' "$input" >&2
    exit 2
  fi
}

build_add_command() {
  local source="$1"
  local skill="$2"
  local scope="$3"
  local agent="$4"

  cmd=(npx skills add "$source")

  if [[ "$skill" != "__wizard__" && -n "$skill" ]]; then
    cmd+=(--skill "$skill")
  fi

  case "$scope" in
    wizard|none|"") ;;
    global) cmd+=(-g) ;;
    project) ;;
    *)
      printf 'Unsupported scope "%s" for skill "%s"\n' "$scope" "$skill" >&2
      exit 2
      ;;
  esac

  case "$agent" in
    wizard|none|"") ;;
    codex) cmd+=(-a codex) ;;
    *)
      printf 'Unsupported agent "%s" for skill "%s"\n' "$agent" "$skill" >&2
      exit 2
      ;;
  esac
}

build_update_command() {
  local skill="$1"
  local scope="$2"

  cmd=(npx skills update)

  case "$scope" in
    wizard|none|"") ;;
    global) cmd+=(-g) ;;
    project) cmd+=(-p) ;;
    *)
      printf 'Unsupported scope "%s" for skill "%s"\n' "$scope" "$skill" >&2
      exit 2
      ;;
  esac

  cmd+=("$skill")
}

apply=false

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 2
fi

manifest_arg="$1"
shift

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) apply=true ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

manifest="$(resolve_manifest "$manifest_arg")"

while IFS=$'\t' read -r source skill scope agent mode notes || [[ -n "${source:-}" ]]; do
  [[ -z "${source:-}" ]] && continue
  [[ "$source" == \#* ]] && continue

  if [[ "$skill" == "*" || "$skill" == "__wizard__" ]]; then
    cmd=()
    build_add_command "$source" "$skill" "${scope:-wizard}" "${agent:-wizard}"
  else
    cmd=()
    build_update_command "$skill" "${scope:-wizard}"
  fi

  if [[ "$apply" == true ]]; then
    printf '+ %s\n' "$(quote_cmd "${cmd[@]}")"
    "${cmd[@]}"
  else
    printf '%s\n' "$(quote_cmd "${cmd[@]}")"
  fi
done < "$manifest"
