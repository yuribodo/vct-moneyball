export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse bg-bone-3/60 ${className}`} aria-hidden="true" />;
}
