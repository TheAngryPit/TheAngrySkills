#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  install-skillset.sh <manifest.tsv> [--apply]

Default is dry-run. Use --apply to execute.

Manifest columns:
  source<TAB>skill<TAB>scope<TAB>agent<TAB>mode<TAB>notes

scope:
  wizard  leave install method to native npx skills wizard
  global  add -g
  project no global flag
  none    no scope flag

agent:
  wizard  leave target agent to native npx skills wizard
  codex   add -a codex
  none    no agent flag

mode:
  add     run npx skills add
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

  cmd=(npx skills add "$source" --skill "$skill")

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

  if [[ "${mode:-}" != "add" ]]; then
    printf 'Skipping unsupported mode "%s" for skill "%s"\n' "${mode:-}" "${skill:-}" >&2
    continue
  fi

  cmd=()
  build_add_command "$source" "$skill" "${scope:-wizard}" "${agent:-wizard}"

  if [[ "$apply" == true ]]; then
    printf '+ %s\n' "$(quote_cmd "${cmd[@]}")"
    "${cmd[@]}"
  else
    printf '%s\n' "$(quote_cmd "${cmd[@]}")"
  fi
done < "$manifest"
