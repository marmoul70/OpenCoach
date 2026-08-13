import { registerModule } from '../../core/modules/registry'
import {
  registerWidget,
  registerWidgetView,
} from '../../core/widgets'
import {
  registerWidgetViewComponent,
} from '../../components/widgets/WidgetViewRegistry'
import { DashboardDetails } from './DashboardDetails'

registerModule({
  id: 'dashboard',
  name: 'Dashboard',
  description: 'Vue synthétique de l’état OpenCoach',
  enabled: true,
})

registerWidgetView({
  id: 'dashboard-welcome-details',
  moduleId: 'dashboard',
  title: 'Bienvenue sur OpenCoach',
})

registerWidgetViewComponent(
  'dashboard-welcome-details',
  DashboardDetails,
)

registerWidget({
  id: 'dashboard-welcome',
  moduleId: 'dashboard',
  title: 'Bienvenue sur OpenCoach',
  description: 'Votre espace de suivi OpenCoach',
  status: 'neutral',
  enabled: true,
  detailsViewId: 'dashboard-welcome-details',
})