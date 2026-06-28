import { Bracket } from "@/components/feature/bracket/Bracket";
import { SectionHeading } from "@/components/ui/GlowDivider";

export default function BracketPage() {
  return (
    <div className="py-12 sm:py-16">
      <SectionHeading kicker="Tournament Forecast" title="Run the whole thing.">
        Sixteen nations seeded by the power index, run through a single-elimination bracket. Every
        tie is decided by the model&apos;s head-to-head probability. Flip to coin-flip mode and
        re-simulate to watch upsets unfold.
      </SectionHeading>
      <Bracket />
    </div>
  );
}
