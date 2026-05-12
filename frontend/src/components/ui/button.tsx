import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '../../lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-2xl text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-60 [&_svg]:size-4',
  {
    variants: {
      variant: {
        default:
          'bg-teal-800 px-4 py-3 text-white shadow-[0_14px_28px_rgba(8,96,103,0.25)] hover:bg-teal-700',
        secondary:
          'border border-slate-200 bg-white px-4 py-3 text-slate-900 hover:bg-slate-50',
        ghost: 'px-3 py-2 text-slate-700 hover:bg-slate-100',
      },
      size: {
        default: 'h-11',
        sm: 'h-9 rounded-xl px-3',
        lg: 'h-12 rounded-2xl px-5',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props}
    />
  ),
)
Button.displayName = 'Button'

export { Button, buttonVariants }
