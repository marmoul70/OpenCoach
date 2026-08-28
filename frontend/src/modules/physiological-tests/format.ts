export function formatPhysiologicalTestProtocol(
  protocol: string,
): string {
  const labels:
    Record<string, string> = {
      half_cooper:
        'Demi-Cooper · 6 min',
      cooper:
        'Cooper · 12 min',
      threshold_30_min:
        'Test seuil · 30 min',
    }

  return (
    labels[protocol]
    ?? protocol.replaceAll(
      '_',
      ' ',
    )
  )
}


export function formatPhysiologicalMetric(
  metric: string,
): string {
  const labels:
    Record<string, string> = {
      vma: 'VMA',
      max_heart_rate: 'FC max',
      resting_heart_rate:
        'FC repos',
      threshold_heart_rate_1:
        'SV1',
      threshold_heart_rate_2:
        'SV2',
    }

  return (
    labels[metric]
    ?? metric.toUpperCase()
  )
}
