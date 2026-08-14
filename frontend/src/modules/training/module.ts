import { Activity } from 'lucide-react'

import { registerModule } from '../../core/modules/registry'
import {
  registerWidget,
  registerWidgetView,
} from '../../core/widgets'
import {
  registerWidgetComponent,
} from '../../components/widgets/WidgetComponentRegistry'
import {
  registerWidgetViewComponent,
} from '../../components/widgets/WidgetViewRegistry'

import { TrainingWidget } from './TrainingWidget'
import { TrainingDetails } from './TrainingDetails'

registerModule({
  id: 'training',
  name: 'Entraînement',
  description: 'Séances et planification de l’entraînement',
  enabled: true,
})

registerWidgetView({
  id: 'training-details',
  moduleId: 'training',
  title: 'Entraînement du jour',
})

registerWidgetViewComponent(
  'training-details',
  TrainingDetails,
)

registerWidget({
  id: 'training',
  moduleId: 'training',
  title: 'Entraînement du jour',
  description: 'Votre séance prévue aujourd’hui',
  status: 'warning',
  accent: 'primary',
  icon: Activity,
  enabled: true,
  detailsViewId: 'training-details',
})

registerWidgetComponent(
  'training',
  TrainingWidget,
)
