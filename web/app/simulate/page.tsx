import { Simulator } from "@/components/feature/simulate/Simulator";
import { SectionHeading } from "@/components/ui/GlowDivider";

export const dynamic = "force-dynamic";

export default async function SimulatePage({
  searchParams,
}: {
  searchParams: Promise<{ a?: string; b?: string }>;
}) {
  const { a, b } = await searchParams;

  return (
    <div className="py-12 sm:py-16">
      <SectionHeading kicker="Head-to-Head" title="Run the tape.">
        Pick two nations and a date. The forecast reads only what was known before that day — each
        roster&apos;s club form, nothing from the future.
      </SectionHeading>
      <Simulator initialA={a} initialB={b} />
    </div>
  );
}
