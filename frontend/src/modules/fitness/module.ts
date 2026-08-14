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

import { FitnessWidget } from './FitnessWidget'
import { FitnessDetails } from './FitnessDetails'
import { HeartPulse } from 'lucide-react'

registerModule({
  id: 'fitness',
  name: 'État de forme',
  description: 'Analyse de l’état de forme et de récupération',
  enabled: true,
})

registerWidgetView({
  id: 'fitness-details',
  moduleId: 'fitness',
  title: 'État de forme',
})

registerWidgetViewComponent(
  'fitness-details',
  FitnessDetails,
)

registerWidget({
  id: 'fitness',
  moduleId: 'fitness',
  title: 'État de forme',
  description: 'Votre état de forme actuel',
  status: 'success',
  accent: 'success',
  icon: HeartPulse,
  enabled: true,
  detailsViewId: 'fitness-details',
})

registerWidgetComponent(
  'fitness',
  FitnessWidget,
)