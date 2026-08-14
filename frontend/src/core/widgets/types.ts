import type { ComponentType } from 'react'

export type WidgetStatus =
  | 'neutral'
  | 'success'
  | 'warning'
  | 'danger'

export type WidgetAccent =
  | 'neutral'
  | 'primary'
  | 'secondary'
  | 'accent'
  | 'info'
  | 'success'
  | 'warning'
  | 'error'

export interface WidgetDefinition {
  id: string
  moduleId: string
  title: string
  description?: string
  status?: WidgetStatus
  accent?: WidgetAccent
  icon?: ComponentType<{
    className?: string
  }>
  enabled: boolean
  detailsViewId?: string
  component?: ComponentType<{
    onClick: () => void
  }>
}
