import { getEventBus, createLifecycleEvent, type AggregateType } from '@lev-os/event-bus/events'

const bus = getEventBus()

export type RatchetEventName =
  | 'ratchet.campaign.started'
  | 'ratchet.campaign.completed'
  | 'ratchet.campaign.held'
  | 'ratchet.campaign.failed'

export function emitRatchetEvent(
  event: RatchetEventName,
  campaignId: string,
  data: Record<string, unknown>,
): void {
  const lifecycleEvent = createLifecycleEvent(
    'ratchet',
    event,
    'L1',
    { campaignId, ...data },
    campaignId,
    'entity' as AggregateType,
  )
  bus.emit(lifecycleEvent)
}
