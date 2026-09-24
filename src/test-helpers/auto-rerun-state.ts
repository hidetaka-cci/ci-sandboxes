import { readFileSync, writeFileSync, existsSync } from 'node:fs'

const STATE_PATH = '/tmp/auto-rerun-state.json'

function readState(): Record<string, number> {
  if (!existsSync(STATE_PATH)) {
    return {}
  }
  return JSON.parse(readFileSync(STATE_PATH, 'utf8')) as Record<string, number>
}

function writeState(state: Record<string, number>): void {
  writeFileSync(STATE_PATH, JSON.stringify(state))
}

/** 同一ジョブ内の rerun 間で attempt 回数を保持する */
export function nextAttempt(key: string): number {
  const state = readState()
  const attempt = (state[key] ?? 0) + 1
  state[key] = attempt
  writeState(state)
  return attempt
}
