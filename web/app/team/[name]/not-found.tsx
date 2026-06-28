import { EmptyState } from "@/components/ui/States";
import { ButtonLink } from "@/components/ui/Button";

export default function TeamNotFound() {
  return (
    <div className="py-24">
      <EmptyState kicker="404" title="No such nation">
        That team isn&apos;t in the ENC 2026 field.
        <div className="mt-5">
          <ButtonLink href="/rankings" variant="ghost">
            Back to the board
          </ButtonLink>
        </div>
      </EmptyState>
    </div>
  );
}
