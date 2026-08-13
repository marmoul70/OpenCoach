import type { ComponentType } from 'react'

export type WidgetStatus =
  | 'neutral'
  | 'success'
  | 'warning'
  | 'danger'

export interface WidgetDefinition {
  id: string
  moduleId: string
  title: string
  description?: string
  status?: WidgetStatus
  enabled: boolean
  detailsViewId?: string
  component?: ComponentType<{
    onClick: () => void
  }>
}