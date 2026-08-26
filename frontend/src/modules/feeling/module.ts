import {
  MessageCircleHeart,
} from 'lucide-react'

import {
  registerModule,
} from '../../core/modules/registry'

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

import {
  FeelingDetails,
} from './FeelingDetails'

import {
  FeelingWidget,
} from './FeelingWidget'


registerModule({
  id: 'feeling',
  name: 'Ressenti',
  description: 'État subjectif quotidien de l’athlète',
  enabled: true,
})

registerWidgetView({
  id: 'feeling-details',
  moduleId: 'feeling',
  title: 'Ressenti',
})

registerWidgetViewComponent(
  'feeling-details',
  FeelingDetails,
)

registerWidget({
  id: 'feeling',
  moduleId: 'feeling',
  title: 'Ressenti',
  description: 'Énergie, confort et disponibilité',
  status: 'success',
  accent: 'secondary',
  icon: MessageCircleHeart,
  enabled: true,
  detailsViewId: 'feeling-details',
})

registerWidgetComponent(
  'feeling',
  FeelingWidget,
)
