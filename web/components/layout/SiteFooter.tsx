export function SiteFooter() {
  return (
    <footer className="mt-28 on-steel">
      <div className="mx-auto max-w-[68rem] px-5 py-12 sm:px-8">
        <div className="flex items-center gap-3">
          <span className="h-3 w-6 bg-red" />
          <span className="label text-bone/60">Settled when it&apos;s over</span>
        </div>
        <p className="display mt-4 max-w-2xl text-2xl leading-tight text-bone sm:text-3xl">
          Every call here was dated and frozen before a single map was played.
        </p>
        <p className="mt-4 max-w-xl text-sm leading-relaxed text-bone/55">
          Built from VLR.gg match data. Leakage-checked, baseline-relative, and reproducible from
          versioned inputs — when the tournament ends, the data shows who was right.
        </p>
      </div>
    </footer>
  );
}
