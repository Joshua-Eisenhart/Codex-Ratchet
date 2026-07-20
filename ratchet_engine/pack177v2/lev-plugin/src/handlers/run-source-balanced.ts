import { execFileSync } from 'node:child_process'
import { existsSync, readFileSync, realpathSync } from 'node:fs'
import { resolve } from 'node:path'
import { emitRatchetEvent } from '../bridge.js'

interface RunOptions {
  packRoot?: string
  python?: string
}

function execute(python: string, script: string, args: string[]): string {
  return execFileSync(python, ['-B', script, ...args], {
    encoding: 'utf8',
    timeout: 300_000,
    stdio: ['ignore', 'pipe', 'pipe'],
  })
}

export async function handler(args: unknown[]) {
  const candidate = args[args.length - 1]
  const options: RunOptions =
    typeof candidate === 'object' && candidate !== null
      ? (args.pop() as unknown as RunOptions)
      : {}
  if (!options.packRoot) {
    throw new Error('packRoot is required')
  }
  const packRoot = realpathSync(resolve(options.packRoot))
  const script = resolve(packRoot, 'source', 'source_balanced_completion_ratchet.py')
  const fuelCompiler = resolve(packRoot, 'source', 'compile_fuel_obligations.py')
  const graphBuilder = resolve(packRoot, 'source', 'build_lev_context_graph.py')
  const receipt = resolve(packRoot, 'receipts', 'campaign_receipt.json')
  const fuelReceipt = resolve(packRoot, 'receipts', 'fuel_obligations.json')
  const fuelSchedule = resolve(packRoot, 'receipts', 'fuel_schedule_projection.json')
  if (!existsSync(script) || !existsSync(fuelCompiler) || !existsSync(graphBuilder)) {
    throw new Error('packRoot does not contain the frozen fuel-bearing Ratchet operations')
  }
  const python = options.python || 'python3'
  const campaignId = 'fuel-bearing-completion-v0-2'
  emitRatchetEvent('ratchet.campaign.started', campaignId, {
    packRoot,
    mathematicalAuthority: false,
  })
  try {
    execute(python, script, ['--self-test'])
    execute(python, script, ['--run'])
    execute(python, script, ['--validate'])
    execute(python, fuelCompiler, ['--self-test'])
    execute(python, fuelCompiler, ['--run'])
    execute(python, fuelCompiler, ['--validate'])
    execute(python, graphBuilder, [])
    const campaign = JSON.parse(readFileSync(receipt, 'utf8')) as Record<string, unknown>
    const status = String(campaign.status || '')
    const held = status.includes('HOLD')
    emitRatchetEvent(
      held ? 'ratchet.campaign.held' : 'ratchet.campaign.completed',
      campaignId,
      {
        status,
        receipt,
        fuelReceipt,
        fuelSchedule,
        mathematicalAuthority: false,
      },
    )
    return {
      success: true,
      status,
      receipt,
      fuelReceipt,
      fuelSchedule,
      contextGraph: resolve(packRoot, 'receipts', 'lev_context_graph.json'),
      mathematicalAuthority: false,
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error)
    emitRatchetEvent('ratchet.campaign.failed', campaignId, {
      error: message,
      mathematicalAuthority: false,
    })
    throw error
  }
}

handler.description = 'Execute and receipt the source-balanced census and fuel compiler'
handler.inputSchema = {
  type: 'object',
  properties: {
    packRoot: { type: 'string', description: 'Absolute path to the verified execution pack' },
    python: { type: 'string', description: 'Authorized local Python interpreter' },
  },
  required: ['packRoot'],
}

export const runSourceBalancedTool = {
  name: 'ratchet:run-source-balanced',
  description: handler.description,
  inputSchema: handler.inputSchema,
  handler,
}
