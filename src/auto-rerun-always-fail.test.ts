import { describe, it, expect } from 'vitest'
import { nextAttempt } from './test-helpers/auto-rerun-state'

const enabled = process.env.AUTO_RERUN_FAIL_TEST === '1'

describe.skipIf(!enabled)('auto-rerun max attempts demo', () => {
  it('max-auto-rerun 回数を超えても失敗し続ける', () => {
    nextAttempt('always-fail')
    expect(true).toBe(false)
  })
})
