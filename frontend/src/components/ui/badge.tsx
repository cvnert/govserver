import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '../../lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium tracking-[0.08em] uppercase',
  {
    variants: {
      variant: {
        outline: 'border-slate-200 bg-white text-slate-700',
        muted: 'border-slate-200 bg-slate-100 text-slate-600',
        teal: 'border-teal-200 bg-teal-50 text-teal-800',
      },
    },
    defaultVariants: {
      variant: 'outline',
    },
  },
)

type BadgeProps = React.HTMLAttributes<HTMLDivElement> &
  VariantProps<typeof badgeVariants>

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge }
