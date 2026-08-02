declare module "mina-scheduler" {
  import type * as React from "react"

  export type Variant = "success" | "primary" | "default" | "warning" | "danger"

  export interface Event {
    id: string
    title: string
    description?: string
    startDate: Date
    endDate: Date
    variant?: Variant
  }

  export type Views = {
    mobileViews?: ("day" | "week" | "month")[]
    views?: ("day" | "week" | "month")[]
  }

  export type SchedulerProviderProps = {
    children: React.ReactNode
    initialState?: Event[]
    onAddEvent?: (event: Event) => void
    onUpdateEvent?: (event: Event) => void
    onDeleteEvent?: (id: string) => void
    weekStartsOn?: "sunday" | "monday"
  }

  export type SchedularViewProps = {
    views?: Views
    CustomComponents?: {
      customButtons?: {
        CustomAddEventButton?: React.ReactNode
        CustomPrevButton?: React.ReactNode
        CustomNextButton?: React.ReactNode
      }
      customTabs?: {
        CustomDayTab?: React.ReactNode
        CustomWeekTab?: React.ReactNode
        CustomMonthTab?: React.ReactNode
      }
      CustomEventComponent?: React.FC<Event & { minmized?: boolean }>
      CustomEventModal?: {
        CustomAddEventModal?: {
          title?: string
          CustomForm?: React.FC<{ register: unknown; errors: unknown }>
        }
      }
    }
    classNames?: {
      event?: string
      buttons?: {
        prev?: string
        next?: string
        addEvent?: string
      }
      tabs?: {
        cursor?: string
        panel?: string
        tab?: string
        tabContent?: string
        tabList?: string
        wrapper?: string
      }
      views?: {
        dayView?: string
        weekView?: string
        monthView?: string
      }
    }
  }

  export function SchedulerProvider(
    props: SchedulerProviderProps
  ): React.ReactElement
  export function SchedularView(props: SchedularViewProps): React.ReactElement
  export function useScheduler(): unknown
  export const eventSchema: unknown
  export const variants: unknown
}
