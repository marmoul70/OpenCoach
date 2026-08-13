import type { ComponentType } from 'react'

export interface WidgetComponentProps {
  onClick: () => void
}

const components = new Map<
  string,
  ComponentType<WidgetComponentProps>
>()

export function registerWidgetComponent(
  widgetId: string,
  component: ComponentType<WidgetComponentProps>,
): void {
  if (components.has(widgetId)) {
    throw new Error(
      `Composant de widget déjà enregistré : ${widgetId}`,
    )
  }

  components.set(widgetId, component)
}

export function getWidgetComponent(
  widgetId: string,
): ComponentType<WidgetComponentProps> | undefined {
  return components.get(widgetId)
}
