import { cn } from '../../../utils/classes.ts'

interface PinProps {
  color: 'red' | 'yellow' | 'white'
  isWinning: boolean
}

export function Pin(props: PinProps) {
  return (
    <div
      className={cn('w-12 h-12 lg:w-16 lg:h-16 rounded-full flex items-center justify-center', {
        'bg-red-400 fade-in-down': props.color === 'red',
        'bg-yellow-400 fade-in-down': props.color === 'yellow',
        'bg-white': props.color === 'white',
        'ring-4 ring-green-400': props.isWinning,
      })}
    >
      {props.isWinning && (
        <span className="text-xl lg:text-3xl select-none"> 🎉 </span>
      )}
    </div>
  )
}
