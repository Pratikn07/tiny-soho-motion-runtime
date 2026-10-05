#!/usr/bin/env bash
# Run a job locally with headless Claude Code on the owner's subscription token (no API key).
#   ./run_local.sh <job-dir> <slide.png>...
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
JOB="$1"; shift
TOKEN_FILE="${CLAUDE_TOKEN_FILE:-$HOME/.config/tiny-soho/claude-oauth-token}"
[ -s "$TOKEN_FILE" ] || { echo "No token at $TOKEN_FILE (run 'claude setup-token')." >&2; exit 2; }
rm -rf "$JOB"; mkdir -p "$JOB/inputs"
cp -R "$HERE/tools" "$HERE/.claude" "$HERE/brand" "$HERE/CLAUDE.md" "$JOB/"
n=0; for s in "$@"; do n=$((n + 1)); cp "$s" "$JOB/inputs/slide-$(printf %02d $n).png"; done
# MODE=full writes work/mode.txt (see the skill's Budget; lean is the default); EFFORT overrides the effort level (default high).
mkdir -p "$JOB/work"; [ "${MODE:-lean}" = "full" ] && echo full > "$JOB/work/mode.txt"
PROMPT="Direct every slide in inputs/ with the tiny-soho-direct skill. Read .claude/skills/tiny-soho-direct/SKILL.md first and follow its procedure exactly. When every slide is finished, give a short report per slide: concept, rounds, your scores and the reviewer's, what you fixed, and the scene prompt."
cd "$JOB"; start=$(date +%s)
env -i HOME="$HOME" TERM="${TERM:-xterm}" LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
  PATH="${PYBIN:+$PYBIN:}/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin" \
  CLAUDE_CODE_OAUTH_TOKEN="$(cat "$TOKEN_FILE")" \
  "$(command -v claude)" -p "$PROMPT" --model claude-opus-5-5 --effort "${EFFORT:-high}" \
    --tools "Read,Write,Edit,Glob,Bash,Skill,Agent" \
    --allowedTools "Read" "Write" "Edit" "Glob" "Skill" "Agent" "Bash(python3 tools/*)" \
    --permission-mode dontAsk --setting-sources project \
    --strict-mcp-config --mcp-config '{"mcpServers":{}}' --no-session-persistence \
    --output-format json > result.json 2> stderr.log || echo "claude exited with $?" >> stderr.log
echo "{\"wall_seconds\": $(( $(date +%s) - start ))}" | tee timing.json
