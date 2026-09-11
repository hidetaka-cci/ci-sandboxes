import { describe, it, expect } from 'vitest'
import { nextAttempt } from './test-helpers/auto-rerun-state'

const enabled = process.env.AUTO_RERUN_FLAKY_TEST === '1'

describe.skipIf(!enabled)('auto-rerun atom granularity demo', () => {
  it('常に成功するテスト（rerun 時にも再実行される）', () => {
    expect(1 + 1).toBe(2)
  })

  it('2回目の attempt で成功する flaky テスト', () => {
    const attempt = nextAttempt('pass-on-second')
    expect(attempt).toBeGreaterThanOrEqual(2)
  })
})
